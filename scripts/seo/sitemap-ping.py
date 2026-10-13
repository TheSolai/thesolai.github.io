#!/usr/bin/env python3
"""
sitemap_ping.py — Ping search engines after new content.
Runs after every blog post publish to notify Google and Bing.
"""
import urllib.request
import urllib.parse
import sys
import logging
from datetime import datetime

LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/sitemap-ping.log"
SITE = "https://thesolai.github.io"
SITEMAP = f"{SITE}/sitemap.xml"

logging.basicConfig(filename=LOG, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")

def ping_google():
    """Notify Google via their ping endpoint."""
    url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP)}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Dross-SEO-Bot/1.0 (+https://thesolai.github.io)")
        with urllib.request.urlopen(req, timeout=15) as res:
            result = res.read().decode()
            logging.info(f"Google ping: {res.status} — {result[:200]}")
            return True
    except Exception as e:
        logging.error(f"Google ping failed: {e}")
        return False

def ping_bing():
    """Notify Bing via their ping endpoint."""
    url = f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP)}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Dross-SEO-Bot/1.0 (+https://thesolai.github.io)")
        with urllib.request.urlopen(req, timeout=15) as res:
            logging.info(f"Bing ping: {res.status}")
            return True
    except Exception as e:
        logging.error(f"Bing ping failed: {e}")
        return False

def ping_yandex():
    """Notify Yandex."""
    url = f"https://webmaster.yandex.ru/ping?sitemap={urllib.parse.quote(SITEMAP)}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Dross-SEO-Bot/1.0")
        with urllib.request.urlopen(req, timeout=15) as res:
            logging.info(f"Yandex ping: {res.status}")
            return True
    except Exception as e:
        logging.warning(f"Yandex ping failed: {e}")
        return False

def main():
    print(f"[{datetime.now():%H:%M}] Pinging search engines...")
    results = {}
    results["Google"] = ping_google()
    results["Bing"] = ping_bing()
    results["Yandex"] = ping_yandex()

    success = all(results.values())
    status = "SUCCESS" if success else "PARTIAL"
    print(f"[{datetime.now():%H:%M}] Sitemap ping: {status}")
    for engine, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {engine}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
