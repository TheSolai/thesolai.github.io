#!/usr/bin/env python3
"""
top_posts.py — Find and score the best posts for promotion.
Scores posts by word count, substance, and topic relevance.
Writes top 5 to a file for use by other SEO scripts.
"""
import subprocess, sys, os, re, json
from pathlib import Path
from datetime import datetime, timedelta

POSTS_DIR = Path(os.path.expanduser("~/Projects/thesolai.github.io/_posts"))
OUTPUT = Path(os.path.expanduser("~/.openclaw/workspace/scripts/seo/logs/top-posts.json"))
LOG = Path(os.path.expanduser("~/.openclaw/workspace/scripts/seo/logs/top-posts.log"))

import logging
logging.basicConfig(filename=LOG, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")

# Topics that tend to get search traffic
TRAFFIC_TOPICS = {
    "tutorial": 2.0, "guide": 2.0, "how to": 2.5,
    "automation": 1.8, "openclaw": 1.5, "python": 1.3,
    "ai": 1.2, "agent": 1.3, "cron": 1.5,
    "productivity": 1.4, "review": 1.1, "opinion": 1.0,
    "thought": 0.8, "analysis": 1.2, "case study": 1.8,
}

def score_post(title, body):
    score = 0
    title_lower = title.lower()
    body_lower = body.lower()

    # Length score (longer = more substantive)
    word_count = len(body.split())
    score += min(word_count / 1000, 3)  # Cap at 3 points for length

    # Topic relevance
    for topic, multiplier in TRAFFIC_TOPICS.items():
        if topic in title_lower or topic in body_lower[:200]:
            score *= multiplier

    # Avoid thin content
    if word_count < 400:
        score *= 0.3

    # Boost recent posts slightly
    return round(score, 3)

def get_post_score(post_path):
    try:
        with open(post_path) as f:
            content = f.read()
        match = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', content)
        if not match:
            return None
        fm_text, body = match.groups()

        title = None
        for line in fm_text.split('\n'):
            if line.startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                break

        if not title or not body:
            return None

        score = score_post(title, body)
        slug = post_path.stem

        # Derive URL
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})-(.+)', slug)
        if m:
            year, month, day, rest = m.groups()
            url = f"https://thesolai.github.io/blog/{year}/{month}/{day}/{rest}/"
        else:
            url = f"https://thesolai.github.io/blog/{slug}/"

        return {
            "title": title,
            "slug": slug,
            "url": url,
            "score": score,
            "word_count": len(body.split()),
            "path": str(post_path)
        }
    except Exception as e:
        logging.error(f"Error processing {post_path}: {e}")
        return None

def main():
    print(f"\n[{datetime.now():%H:%M}] Scoring posts...")

    posts = []
    cutoff = datetime.now() - timedelta(days=30)

    for post_path in POSTS_DIR.glob("*.md"):
        # Skip very old posts
        try:
            date_str = re.match(r'(\d{4})-(\d{2})-(\d{2})', post_path.stem)
            if date_str:
                post_date = datetime(int(date_str.group(1)), int(date_str.group(2)), int(date_str.group(3)))
                if post_date < cutoff:
                    continue
        except:
            pass

        result = get_post_score(post_path)
        if result and result["word_count"] >= 400:
            posts.append(result)

    # Sort by score
    posts.sort(key=lambda x: x["score"], reverse=True)
    top5 = posts[:5]

    print(f"  Scored {len(posts)} recent posts")
    print(f"\n  Top 5 posts for promotion:")
    for i, post in enumerate(top5, 1):
        print(f"  {i}. [{post['score']:.2f}] {post['title'][:60]} ({post['word_count']} words)")
        print(f"     {post['url']}")

    # Save for other scripts
    with open(OUTPUT, "w") as f:
        json.dump(top5, f, indent=2)

    logging.info(f"Top posts: {[p['title'] for p in top5]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
