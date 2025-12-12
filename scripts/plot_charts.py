#!/usr/bin/env python3
import json
from pathlib import Path
import matplotlib.pyplot as plt
import math

ROOT = Path(".")
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "charts"
OUT_DIR.mkdir(exist_ok=True)

def load_json(name):
    return json.load(open(DATA_DIR / name, encoding='utf-8'))

# --- Chart 1: Sentiment Comparison (stacked bar) ---
def chart_sentiment():
    e = load_json("english_analysis.json")["summary"]["sentiment_scores"]
    u = load_json("uzbek_translated_analysis.json")["summary"]["sentiment_scores"]

    labels = ["Positive", "Negative", "Neutral", "Mixed"]
    eng_vals = [e.get(k,0) for k in labels]
    uzb_vals = [u.get(k,0) for k in labels]

    x = range(len(labels))
    plt.figure(figsize=(8,5))
    # plot English and Uzbek side-by-side grouped bars
    width = 0.35
    plt.bar([i - width/2 for i in x], eng_vals, width=width)
    plt.bar([i + width/2 for i in x], uzb_vals, width=width)
    plt.xticks(x, labels)
    plt.ylabel("Score (0-1)")
    plt.title("Sentiment comparison: English vs Uzbek (translated)")
    plt.legend(["English","Uzbek (translated)"])
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sentiment_comparison.png")
    plt.close()

# --- Chart 2: Top 10 Key Phrases comparison (bar chart) ---
def chart_key_phrases(top_n=10):
    e_kp = load_json("english_analysis.json")["summary"]["key_phrases"]
    u_kp = load_json("uzbek_translated_analysis.json")["summary"]["key_phrases"]

    # take top N texts for each
    e_top = [(kp["Text"], kp["Score"]) for kp in e_kp[:top_n]]
    u_top = [(kp["Text"], kp["Score"]) for kp in u_kp[:top_n]]

    # Normalize labels for display (truncate if long)
    def short(s, l=40):
        return (s if len(s)<=l else s[:l-1]+"…")
    # Plot two subplots stacked
    plt.figure(figsize=(12,8))
    plt.subplot(2,1,1)
    texts = [short(t) for t,_ in e_top]
    scores = [s for _,s in e_top]
    y_pos = range(len(texts))[::-1]
    plt.barh(y_pos, scores)
    plt.yticks(y_pos, texts[::-1])
    plt.title("Top key phrases — English (top {})".format(top_n))
    plt.xlabel("Score")

    plt.subplot(2,1,2)
    texts = [short(t) for t,_ in u_top]
    scores = [s for _,s in u_top]
    y_pos = range(len(texts))[::-1]
    plt.barh(y_pos, scores)
    plt.yticks(y_pos, texts[::-1])
    plt.title("Top key phrases — Uzbek (translated) (top {})".format(top_n))
    plt.xlabel("Score")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "key_phrases_comparison.png")
    plt.close()

# --- Chart 3: Entity Type Frequencies ---
def chart_entity_counts():
    e_entities = load_json("english_analysis.json")["summary"]["entities"]
    u_entities = load_json("uzbek_translated_analysis.json")["summary"]["entities"]

    def counts(entities):
        d = {}
        for ent in entities:
            t = ent.get("Type", "UNKNOWN")
            d[t] = d.get(t,0) + 1
        return d

    e_counts = counts(e_entities)
    u_counts = counts(u_entities)

    # union of types
    types = sorted(set(list(e_counts.keys()) + list(u_counts.keys())))
    e_vals = [e_counts.get(t,0) for t in types]
    u_vals = [u_counts.get(t,0) for t in types]

    x = range(len(types))
    plt.figure(figsize=(10,5))
    width = 0.35
    plt.bar([i - width/2 for i in x], e_vals, width=width)
    plt.bar([i + width/2 for i in x], u_vals, width=width)
    plt.xticks(x, types, rotation=45, ha="right")
    plt.ylabel("Count")
    plt.title("Entity type counts: English vs Uzbek (translated)")
    plt.legend(["English","Uzbek (translated)"])
    plt.tight_layout()
    plt.savefig(OUT_DIR / "entity_type_counts.png")
    plt.close()

def main():
    chart_sentiment()
    chart_key_phrases()
    chart_entity_counts()
    print("Charts saved to", OUT_DIR)

if __name__ == "__main__":
    main()
