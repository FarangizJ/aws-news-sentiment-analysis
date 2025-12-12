#!/usr/bin/env python3
import boto3
import json
import math
from pathlib import Path
from utils import load_file, save_to_file, upload_to_s3
import os

COMPREHEND_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")
comprehend = boto3.client("comprehend", region_name=COMPREHEND_REGION)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MAX_BYTES = 4500  # safe margin under 5000 bytes

def chunk_text_by_bytes(text, max_bytes=MAX_BYTES):
    """Split text into chunks each not exceeding max_bytes when encoded as utf-8."""
    words = text.split()
    chunks = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip() if cur else w
        if len(candidate.encode("utf-8")) <= max_bytes:
            cur = candidate
        else:
            if cur:
                chunks.append(cur)
            # if single word is too long (rare), forcibly cut it
            if len(w.encode("utf-8")) > max_bytes:
                b = w.encode("utf-8")
                # split bytes safely into max_bytes pieces and decode loosely
                for i in range(0, len(b), max_bytes):
                    part = b[i:i+max_bytes].decode("utf-8", errors="ignore")
                    if part:
                        chunks.append(part)
                cur = ""
            else:
                cur = w
    if cur:
        chunks.append(cur)
    return chunks

def analyze_chunk(text_chunk):
    """Call Comprehend APIs for a chunk. Returns dictionary with sentiment, phrases, entities and byte_length."""
    byte_len = len(text_chunk.encode("utf-8"))
    res = {}
    # sentiment
    s = comprehend.detect_sentiment(Text=text_chunk, LanguageCode="en")
    res["sentiment"] = s
    # key phrases
    kp = comprehend.detect_key_phrases(Text=text_chunk, LanguageCode="en")
    res["key_phrases"] = kp.get("KeyPhrases", [])
    # entities
    ent = comprehend.detect_entities(Text=text_chunk, LanguageCode="en")
    res["entities"] = ent.get("Entities", [])
    res["bytes"] = byte_len
    return res

def aggregate_results(chunks_results):
    """Aggregate per-chunk results into a single summary."""
    # Aggregate sentiment scores weighted by bytes
    total_bytes = sum(c["bytes"] for c in chunks_results)
    agg_scores = {"Positive":0.0, "Negative":0.0, "Neutral":0.0, "Mixed":0.0}
    for c in chunks_results:
        weight = c["bytes"]/total_bytes if total_bytes>0 else 0
        scores = c["sentiment"]["SentimentScore"]
        for k in agg_scores:
            agg_scores[k] += scores.get(k, 0.0) * weight
    # choose dominant sentiment
    dominant = max(agg_scores.items(), key=lambda x: x[1])[0]

    # Merge key phrases: keep highest score per phrase (case-normalized)
    kp_map = {}
    for c in chunks_results:
        for kp in c["key_phrases"]:
            text = kp["Text"].strip().lower()
            if text in kp_map:
                kp_map[text] = max(kp_map[text], kp["Score"])
            else:
                kp_map[text] = kp["Score"]
    key_phrases = [{"Text": k, "Score": v} for k,v in sorted(kp_map.items(), key=lambda x: -x[1])]

    # Merge entities by (text,type) picking highest score
    ent_map = {}
    for c in chunks_results:
        for e in c["entities"]:
            key = (e.get("Text","").strip().lower(), e.get("Type"))
            if key in ent_map:
                ent_map[key]["Score"] = max(ent_map[key]["Score"], e.get("Score",0.0))
            else:
                ent_map[key] = {"Text": key[0], "Type": key[1], "Score": e.get("Score",0.0)}
    entities = sorted(list(ent_map.values()), key=lambda x: -x["Score"])

    return {
        "dominant_sentiment": dominant,
        "sentiment_scores": agg_scores,
        "key_phrases": key_phrases,
        "entities": entities,
        "total_bytes": total_bytes,
        "chunks_count": len(chunks_results)
    }

def analyze_text_file(label, filepath):
    text = load_file(filepath)
    # If text is short, still use chunk function (one chunk)
    chunks = chunk_text_by_bytes(text)
    print(f"Analyzing {label}: {len(chunks)} chunk(s).")
    chunks_results = []
    for i,chunk in enumerate(chunks,1):
        print(f" - chunk {i}/{len(chunks)} bytes={len(chunk.encode('utf-8'))} ...")
        r = analyze_chunk(chunk)
        chunks_results.append(r)
    summary = aggregate_results(chunks_results)
    out = DATA_DIR / f"{label}_analysis.json"
    save_to_file(out, json.dumps({"summary": summary, "chunks": chunks_results}, indent=2, ensure_ascii=False))
    try:
        upload_to_s3(str(out), f"{label}_analysis.json")
    except Exception as e:
        print("Warning: upload to S3 failed:", e)
    print("Saved analysis ->", out)
    return out

def main():
    # files to analyze (change or add as needed)
    pairs = [
        ("english", "data/english.txt"),
        ("uzbek_translated", "data/uzbek_translated.txt")
    ]
    for label, path in pairs:
        if not Path(path).exists():
            print(f"Skipping {label}: file not found: {path}")
            continue
        analyze_text_file(label, path)

if __name__ == "__main__":
    main()
