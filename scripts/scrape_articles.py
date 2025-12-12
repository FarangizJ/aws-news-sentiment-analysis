#!/usr/bin/env python3
"""
Simple scraper for the assignment:
- saves ScienceDaily English article
- saves Zamin.uz Uzbek article (falls back to skipping if blocked)
Saves files to data/ and uploads to S3 using scripts/utils.py
"""

import requests
from bs4 import BeautifulSoup
import urllib3
import sys
from utils import save_to_file, upload_to_s3

# disable only the InsecureRequestWarning if we must use verify=False fallback
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CEU-class-bot/1.0; +https://example.com/bot)"
}

items = [
    {
        "name": "english",
        "url": "https://www.sciencedaily.com/releases/2025/12/251201233536.htm",
        "path": "data/english.txt",
        "s3_key": "raw/english.txt"
    },
    {
        "name": "uzbek",
        "url": "https://zamin.uz/uz/tibbiyot/139371-kokrak-bezi-saratoni-sabablari-belgilari-hamda-uni-davolash.html",
        "path": "data/uzbek.txt",
        "s3_key": "raw/uzbek.txt"
    }
]

def fetch_text(url):
    """Fetch textual content using requests and BeautifulSoup."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.SSLError:
        # fallback: some sites have SSL issues inside Codespace; try with verify=False
        print(f"SSL error fetching {url} - retrying with verify=False", file=sys.stderr)
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
    except Exception as e:
        raise

    soup = BeautifulSoup(resp.content, "html.parser")
    # Try common article selectors
    selectors = [
        "article", 
        "div[itemprop='articleBody']",
        "div.article-content", 
        "#content", 
        "#main", 
        "div.post-content", 
        "div#block-system-main"
    ]
    texts = []
    for sel in selectors:
        nodes = soup.select(sel)
        if nodes:
            for n in nodes:
                paragraphs = n.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text:
                        texts.append(text)
            if texts:
                break

    # if nothing found, try collecting all <p>
    if not texts:
        for p in soup.find_all("p"):
            t = p.get_text().strip()
            if t:
                texts.append(t)

    return "\n\n".join(texts).strip()

def main():
    for item in items:
        print(f"Fetching {item['name']} from {item['url']}")
        try:
            text = fetch_text(item["url"])
            if not text:
                print(f"No text extracted for {item['name']} ({item['url']})", file=sys.stderr)
                continue
            save_to_file(item["path"], text)
            print(f"Saved {item['path']}")
            try:
                upload_to_s3(item["path"], item["s3_key"])
            except Exception as e:
                print(f"Warning: failed to upload {item['path']} to S3: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error fetching {item['name']}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
