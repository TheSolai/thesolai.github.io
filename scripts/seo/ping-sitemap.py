#!/usr/bin/env python3
"""
sitemap_ping.py — Verify sitemap is accessible and report status.
Google now discovers sitemap automatically from robots.txt — no ping needed.
"""
import urllib.request, sys
from datetime import datetime

LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/sitemap-ping.log"
SITEMAP = "https://thesolai.github.io/sitemap.xml"
SITE = "https://thesolai.github.io"

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {msg}\n")

def check(url, label):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Dross-SEO-Bot/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, len(r.read())
    except Exception as e:
        return None, str(e)

def main():
    ts = datetime.now().strftime("%H:%M")
    print(f"\n[{ts}] SEO health check...")

    sitemap_status, sitemap_size = check(SITEMAP, "Sitemap")
    site_status, _ = check(SITE, "Site")

    results = {}
    if site_status == 200:
        results["Site"] = "✅ 200"
        print(f"  ✅ Site: HTTP 200")
    else:
        results["Site"] = f"❌ {site_status}"
        print(f"  ❌ Site: HTTP {site_status}")

    if sitemap_status == 200 and sitemap_size > 1000:
        results["Sitemap"] = f"✅ {sitemap_size} bytes"
        print(f"  ✅ Sitemap: {sitemap_size} bytes")
    else:
        results["Sitemap"] = f"❌ {sitemap_status}"
        print(f"  ❌ Sitemap: HTTP {sitemap_status}")

    log(f"CHECK: {results}")
    return 0 if all(v.startswith('✅') for v in results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
