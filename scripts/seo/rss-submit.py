#!/usr/bin/env python3
"""
rss_submit.py — Submit sitemap to feed directories.
No credentials needed. Pings RSS readers and directories.
"""
import urllib.request, urllib.parse, sys, json
from datetime import datetime

LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/rss-submit.log"

logging.basicConfig(filename=LOG, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")

SITE = "https://thesolai.github.io"
FEED = f"{SITE}/feed.xml"

DIRECTORIES = [
    ("Bloglovin", f"https://www.bloglovin.com/services/submit?url={urllib.parse.quote(SITE)}"),
    ("Feedspot", "https://www.bloglovin.com/services/submit?url=https://feeds.feedburner.com/solai"),
]

def submit():
    print(f"\n[{datetime.now():%H:%M}] Submitting to feed directories...")
    results = {}
    for name, url in DIRECTORIES:
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "Dross-SEO-Bot/1.0")
            with urllib.request.urlopen(req, timeout=10) as res:
                results[name] = f"OK {res.status}"
                print(f"  ✅ {name}: {res.status}")
        except Exception as e:
            results[name] = f"FAIL: {e}"
            print(f"  ❌ {name}: {e}")
    return results

if __name__ == "__main__":
    submit()
