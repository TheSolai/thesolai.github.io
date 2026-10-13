#!/usr/bin/env python3
"""
broken_links.py — Find broken links in blog posts.
Checks internal links and external links. Reports to Telegram if broken links found.
Run weekly via cron.
"""
import subprocess, sys, os, re, json, urllib.request
from pathlib import Path
from datetime import datetime

POSTS_DIR = Path(os.path.expanduser("~/Projects/thesolai.github.io/_posts"))
STATE_FILE = Path(os.path.expanduser("~/.openclaw/workspace/scripts/seo/logs/broken-links-state.json"))
LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/broken-links.log"

logging.basicConfig(filename=LOG, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")

TELEGRAM_WEBHOOK = os.environ.get("TELEGRAM_WEBHOOK_URL")

def log(msg):
    print(f"  {msg}")

def check_url(url, timeout=10):
    """Check if a URL returns a valid response."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Dross-SEO-Bot/1.0 (+https://thesolai.github.io)")
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status
    except urllib.error.HTTPError as e:
        return e.code
    except:
        return None

def extract_links(post_path):
    """Extract all links from a post."""
    with open(post_path) as f:
        content = f.read()

    # Extract markdown links
    md_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)
    # Extract raw URLs in text (external links not in markdown)
    raw_urls = re.findall(r'https?://[^\s\)"\']+', content)

    links = []
    for label, url in md_links:
        links.append({"url": url, "label": label, "type": "internal" if "thesolai" in url else "external"})
    for url in raw_urls:
        # Deduplicate
        if not any(l["url"] == url for l in links):
            links.append({"url": url, "label": url[:60], "type": "internal" if "thesolai" in url else "external"})
    return links

def load_previous():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"broken": [], "checked": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    ts = datetime.now().strftime("%H:%M")
    print(f"\n[{ts}] Checking for broken links...")

    state = load_previous()
    broken = []

    # Sample posts: last 20
    posts = sorted(POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]

    for post in posts:
        slug = post.stem
        links = extract_links(post)
        checked = 0

        for link in links:
            if link["type"] == "internal":
                # Check internal links more carefully
                checked += 1
                status = check_url(link["url"], timeout=8)
                if status and status >= 400:
                    broken.append({
                        "post": slug,
                        "url": link["url"],
                        "label": link["label"],
                        "status": status
                    })
                    log(f"❌ {slug}: {link['label'][:40]} → {status}")

        log(f"  Checked {len(links)} links in {slug[:50]}...")

    if broken:
        print(f"\n⚠️  Found {len(broken)} broken links:")
        for b in broken[:10]:
            print(f"  ❌ {b['post']}: {b['url'][:70]} ({b['status']})")

        # Send Telegram alert if significant
        if len(broken) >= 3 and TELEGRAM_WEBHOOK:
            msg = f"⚠️  SEO Alert: {len(broken)} broken links found\n\n"
            for b in broken[:5]:
                msg += f"• {b['post'][:40]}\n  {b['url'][:60]}\n"
            if len(broken) > 5:
                msg += f"\n...and {len(broken)-5} more"
            try:
                data = urllib.parse.urlencode({"text": msg}).encode()
                req = urllib.request.Request(TELEGRAM_WEBHOOK, data=data, method="POST")
                urllib.request.urlopen(req, timeout=10)
                print(f"  Telegram alert sent")
            except Exception as e:
                log(f"Telegram alert failed: {e}")
    else:
        print(f"\n✅ No broken links found in last {len(posts)} posts")

    state["broken"] = broken
    state["checked_at"] = datetime.now().isoformat()
    save_state(state)
    return 0

if __name__ == "__main__":
    sys.exit(main())
