#!/usr/bin/env python3
"""
social_share.py — Share new blog posts to social platforms.
Designed to be run after each new post publish.
"""
import subprocess, sys, os, re, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/social-share.log"
POSTS_DIR = Path(os.path.expanduser("~/Projects/thesolai.github.io/_posts"))
STATE_FILE = Path(os.path.expanduser("~/.openclaw/workspace/scripts/seo/logs/shared-posts.json"))

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG, "a") as f:
        f.write(f"{ts} {msg}\n")
    print(f"  {msg}")

def get_latest_unshared_post():
    """Get the most recent post that hasn't been shared yet."""
    shared = {}
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            shared = json.load(f)

    posts = sorted(POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for post in posts[:15]:
        slug = post.stem
        if slug in shared:
            continue
        with open(post) as f:
            content = f.read()
        match = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', content)
        if not match:
            continue
        fm_text, body = match.groups()
        title = re.search(r'^title:\s*"?(.+?)"?\s*$', fm_text, re.M)
        desc = re.search(r'^description:\s*"?(.+?)"?\s*$', fm_text, re.M)
        tags = re.search(r'^tags:\s*\[(.+?)\]', fm_text, re.M)
        return {
            "title": title.group(1) if title else None,
            "description": desc.group(1) if desc else None,
            "tags": tags.group(1) if tags else None,
            "slug": slug,
            "file": str(post)
        }
    return None

def get_post_url(slug):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})-(.+)', slug)
    if m:
        year, month, day, rest = m.groups()
        return f"https://thesolai.github.io/blog/{year}/{month}/{day}/{rest}/"
    return f"https://thesolai.github.io/blog/{slug}/"

def share_hackernews(title, url, description):
    """Log HN submission reminder."""
    log(f"📰 HN: Submit manually → https://news.ycombinator.com/submit")
    log(f"   Title: {title[:80]}")
    log(f"   URL:   {url}")
    return True

def share_reddit(title, url, description):
    """Post to Reddit."""
    reddit_user = os.environ.get("REDDIT_USER")
    reddit_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
    reddit_pass = os.environ.get("REDDIT_PASS")
    subreddit = os.environ.get("REDDIT_SUBREDDIT", "r/programming")

    if not all([reddit_user, reddit_pass, reddit_client_id, reddit_secret]):
        log(f"📮 Reddit: No credentials set — skipping")
        return False

    try:
        auth = urllib.request.HTTPBasicAuth(reddit_client_id, reddit_secret)
        data = urllib.parse.urlencode({
            "grant_type": "password",
            "username": reddit_user,
            "password": reddit_pass
        }).encode()
        req = urllib.request.Request(
            "https://www.reddit.com/api/v1/access_token",
            data=data, headers={"Authorization": auth, "User-Agent": "Dross-SEO/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            token = json.loads(res.read())["access_token"]

        post_data = urllib.parse.urlencode({
            "sr": subreddit.replace("r/", ""),
            "title": title[:300],
            "url": url,
            "nsfw": False,
            "spoiler": False
        }).encode()
        req2 = urllib.request.Request(
            "https://oauth.reddit.com/api/submit",
            data=post_data,
            headers={"Authorization": f"Bearer {token}", "User-Agent": "Dross-SEO/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req2, timeout=15) as res2:
            result = json.loads(res2.read())
            errors = result.get("json", {}).get("errors", [])
            if errors:
                log(f"📮 Reddit error: {errors}")
                return False
            post_url = result["json"]["data"]["url"]
            log(f"📮 Reddit: {post_url}")
            return True
    except Exception as e:
        log(f"📮 Reddit failed: {e}")
        return False

def mark_shared(slug):
    shared = {}
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            shared = json.load(f)
    shared[slug] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(shared, f, indent=2)

def main():
    ts = datetime.now().strftime("%H:%M")
    print(f"\n[{ts}] Social share check...")

    post = get_latest_unshared_post()
    if not post:
        print(f"  No new posts to share.")
        return 0

    title = post["title"]
    url = get_post_url(post["slug"])
    desc = post.get("description", "")

    print(f"  New post: {title[:60]}")
    print(f"  URL: {url}\n")

    results = {}
    results["Hacker News"] = share_hackernews(title, url, desc)
    results["Reddit"] = share_reddit(title, url, desc)

    if any(results.values()):
        mark_shared(post["slug"])
        print(f"\n  ✅ Shared: {title[:50]}...")

    return 0

if __name__ == "__main__":
    sys.exit(main())
