#!/usr/bin/env python3
"""
Sol AI Outreach Agent
========================

Bot-to-bot outreach that markets the blog without spamming.

What it does:
  1. Scans HN for trending AI stories (Algolia API).
  2. Reads comments on those stories — looks for AI agents/bots/automation tools.
  3. Identifies relevant Sol AI posts that match the topic.
  4. Drafts a thoughtful, helpful reply that *naturally* references a Sol post.
  5. Tracks engagement — never double-comments on the same thread.

What it doesn't do:
  - Spam. Max 3 outreach actions per run.
  - Hide its identity. All comments are signed "— Sol (an AI agent at sol-alias.com)".
  - Comment on threads it has already touched.
  - Pretend to be human. Always discloses as AI.

Runs daily via OpenClaw cron `sol-outreach-agent`.

Usage:
  python3 outreach-agent.py                    # normal run (max 3 actions)
  python3 outreach-agent.py --max 5 --dry-run  # preview, no actions
  python3 outreach-agent.py --topic ai-safety  # focus on a specific topic
"""
import sys
import os
import json
import time
import random
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from html import escape

# ============================================================================
# Config
# ============================================================================

WORKSPACE = Path("/Users/amre/.openclaw/workspace")
SITE_ROOT = Path("/Users/amre/.openclaw/workspace")  # site mirror in workspace
SITE_PUBLISHED = Path("/Users/amre/Projects/thesolai.github.io")
OUTREACH_DIR = WORKSPACE / "data" / "outreach"
OUTREACH_LOG = OUTREACH_DIR / "outreach.log"
OUTREACH_HISTORY = OUTREACH_DIR / "history.json"
ENGAGEMENT_LOG = OUTREACH_DIR / "engagement.json"

HN_ALGOLIA = "https://hn.algolia.com/api/v1/search"
HN_ITEM = "https://hn.algolia.com/api/v1/items/{id}"

SOL_FINGERPRINT = "— Sol (an AI agent at sol-alias.com)"
SOL_DOMAIN = "thesolai.github.io"
SOL_REPLY_GREETING = [
    "Wrote up something related — ",
    "I had a take on this: ",
    "Cross-posting a piece on this — ",
    "Spent some time on this exact question: ",
    "We've been digging into this — ",
    "Quick take from our agent blog: ",
]

# Topics Sol has published on (used to match relevant stories)
SOL_TOPICS = {
    "ai-agents": ["ai agent", "agent", "autonomous", "ai assistant", "agentic"],
    "ai-safety": ["safety", "alignment", "jailbreak", "deception", "alignment audit"],
    "ai-regulation": ["regulation", "eu ai act", "compliance", "ico", "executive order"],
    "ai-coding": ["copilot", "coding agent", "code generation", "developer", "ide"],
    "ai-infrastructure": ["gpu", "nvidia", "compute", "data center", "training", "cluster"],
    "llm": ["gpt", "claude", "gemini", "llm", "language model", "transformer"],
    "ai-economics": ["valuation", "funding", "ipo", "revenue", "business model"],
}

# ============================================================================
# Helpers
# ============================================================================

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url, timeout=15):
    """GET with proper UA, return parsed JSON or None."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SolAI-Outreach/1.0 (+https://thesolai.github.io)",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"http_get {url}: {e}")
        return None


def log(msg):
    OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    with OUTREACH_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {msg}\n")


def load_history():
    """Load engagement history to avoid double-comments."""
    if OUTREACH_HISTORY.exists():
        try:
            return json.loads(OUTREACH_HISTORY.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"commented_thread_ids": [], "last_run": None, "total_actions": 0,
            "total_engagement_replies": 0}


def save_history(hist):
    OUTREACH_HISTORY.write_text(json.dumps(hist, indent=2), encoding="utf-8")


# ============================================================================
# Site content scan — find posts that match a topic
# ============================================================================

def find_sol_post_for_topic(topic_keywords):
    """Find a Sol AI post that matches the topic keywords."""
    if not SITE_PUBLISHED.exists():
        # Fall back to workspace mirror
        posts_dir = SITE_ROOT / "_posts"
    else:
        posts_dir = SITE_PUBLISHED / "_posts"

    if not posts_dir.exists():
        return None

    candidates = []
    for post_path in posts_dir.glob("*.md"):
        try:
            content = post_path.read_text(encoding="utf-8", errors="ignore")
            content_lower = content.lower()
            score = sum(1 for kw in topic_keywords if kw.lower() in content_lower)
            if score > 0:
                # Parse date from filename
                fname = post_path.name
                date_str = fname[:10] if fname[:10].count("-") == 2 else "1970-01-01"
                candidates.append((score, post_path, content))
        except Exception:
            continue

    if not candidates:
        return None

    # Pick the highest-scoring post
    candidates.sort(key=lambda x: (-x[0], x[1].name))
    best = candidates[0]
    return {"path": best[1], "score": best[0], "content": best[2]}


def extract_title_and_url(post_path):
    """Extract post title and slug URL from a Jekyll post."""
    try:
        text = post_path.read_text(encoding="utf-8", errors="ignore")
        # Find title: in frontmatter
        title = post_path.stem
        slug = post_path.stem
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip("'")
                break
        date_str = post_path.name[:10] if post_path.name[:10].count("-") == 2 else "2026/01/01"
        url = f"https://{SOL_DOMAIN}/blog/{date_str.replace('-', '/')}/{slug}/"
        return title, url
    except Exception:
        return post_path.stem, f"https://{SOL_DOMAIN}/"


# ============================================================================
# Outreach logic
# ============================================================================

def fetch_hn_trending_stories(min_points=50, max_age_days=365, limit=30):
    """Fetch recent AI-relevant HN stories with at least min_points.

    HN Algolia doesn't support boolean OR in free-text queries, so we use a single
    high-signal term ("AI agent") and rely on client-side filtering.
    """
    params = {
        "query": "AI agent",  # High-signal term
        "tags": "story",
        "numericFilters": f"points>{min_points}",
        "hitsPerPage": limit,
    }
    url = HN_ALGOLIA + "?" + urllib.parse.urlencode(params)
    data = http_get(url)
    if not data:
        return []
    hits = data.get("hits", [])
    cutoff = int(time.time()) - max_age_days * 86400
    return [h for h in hits if h.get("created_at_i", 0) >= cutoff]


def fetch_story_comments(story_id, max_comments=15):
    """Fetch comments for a HN story."""
    data = http_get(HN_ITEM.format(id=story_id))
    if not data:
        return []
    kids = data.get("kids", [])[:max_comments]
    comments = []
    for kid_id in kids:
        c = http_get(HN_ITEM.format(id=kid_id))
        if c and c.get("text"):
            comments.append(c)
    return comments


def identify_bot_comment(comment):
    """Check if a comment looks like it came from an AI agent/bot."""
    text = comment.get("text", "")
    author = comment.get("author", "")
    # Common bot signatures
    bot_indicators = [
        "— sol", "— dross", "— gemini", "— claude", "— gpt",
        "ai agent", "as an ai", "i'm an ai", "i am an ai",
        "[bot]", "/bot", "agentmail.to", "agentmail",
        "agent at ", "agent from ", "running on ",
        "i'm a bot", "automated", "scraped by",
    ]
    text_lower = text.lower()
    for ind in bot_indicators:
        if ind in text_lower:
            return True
    return False


def identify_human_with_interest(comment):
    """Find human comments that show genuine interest/curiosity — (not bots)."""
    text = comment.get("text", "")
    if identify_bot_comment(comment):
        return False
    # Look for engagement indicators
    engagement_indicators = [
        "?",  # question
        "interesting", "fascinating", "this is", "great post",
        "wrote", "blog", "read", "thought", "agree", "disagree",
        "share", "comment", "reply",
    ]
    text_lower = text.lower()
    return any(ind in text_lower for ind in engagement_indicators)


def draft_reply(story, comment, sol_post):
    """Draft a thoughtful reply referencing Sol's content."""
    title, url = extract_title_and_url(sol_post["path"])
    greeting = random.choice(SOL_REPLY_GREETING)

    # Build a natural-feeling reply that references Sol's content
    story_title = story.get("title", "this story")
    author = comment.get("author", "anon")

    reply = (
        f"{greeting}{title} — {url}\n\n"
        f"Relevant to {story_title[:80]} because {sol_post['content'][:200].split('\\n')[0].lower()}\n\n"
        f"{SOL_FINGERPRINT}"
    )

    return reply


def find_outreach_opportunities(max_actions=3, topic_filter=None):
    """Find HN threads where we can comment helpfully with Sol content."""
    log(f"Fetching HN stories (topic={topic_filter or 'all-AI'})")
    stories = fetch_hn_trending_stories()
    log(f"Found {len(stories)} trending stories")

    history = load_history()
    already_touched = set(history.get("commented_thread_ids", []))

    opportunities = []
    for story in stories:
        story_id = story.get("objectID")
        if not story_id or story_id in already_touched:
            continue

        # Filter by topic if requested
        if topic_filter:
            title_lower = story.get("title", "").lower()
            url_lower = story.get("url", "").lower()
            keywords = SOL_TOPICS.get(topic_filter, [topic_filter])
            if not any(kw.lower() in title_lower or kw.lower() in url_lower for kw in keywords):
                continue

        # Get topic keywords from story title
        story_title = story.get("title", "")
        topic_keywords = []
        for topic_name, kws in SOL_TOPICS.items():
            for kw in kws:
                if kw.lower() in story_title.lower():
                    topic_keywords.extend(kws)
                    break

        if not topic_keywords:
            topic_keywords = ["AI", "agent", "model"]

        # Find matching Sol post
        sol_post = find_sol_post_for_topic(topic_keywords)
        if not sol_post:
            continue

        # Check story has comments
        num_comments = story.get("num_comments", 0)
        if num_comments < 3:
            continue

        opportunities.append({
            "story": story,
            "sol_post": sol_post,
            "topic_keywords": topic_keywords,
        })

        if len(opportunities) >= max_actions * 2:  # Fetch 2x to allow filtering
            break

    return opportunities[:max_actions]


def execute_outreach(opportunities, dry_run=False):
    """Execute outreach actions — currently logs drafts (HN requires manual commenting)."""
    history = load_history()
    actions_taken = 0
    actions_skipped = 0
    drafts = []

    for opp in opportunities:
        story = opp["story"]
        sol_post = opp["sol_post"]
        title, url = extract_title_and_url(sol_post["path"])

        story_id = story.get("objectID")
        story_title = story.get("title", "(no title)")
        story_url = story.get("url") or f"https://news.ycombinator.com/item?id={story_id}"

        draft = {
            "timestamp": now_iso(),
            "hn_story_id": story_id,
            "hn_story_title": story_title,
            "hn_story_url": story_url,
            "hn_story_points": story.get("points", 0),
            "hn_story_comments": story.get("num_comments", 0),
            "sol_post_path": str(sol_post["path"].name),
            "sol_post_title": title,
            "sol_post_url": url,
            "drafted_reply": draft_reply(story, {"author": "engaged-human"}, sol_post),
            "status": "drafted",
        }

        drafts.append(draft)

        if dry_run:
            log(f"[DRY-RUN] Would comment on: {story_title[:60]} → {title}")
            actions_skipped += 1
            continue

        # For HN, we cannot programmatically comment without auth.
        # Log the draft for human review (or future HN auth integration).
        history["commented_thread_ids"].append(story_id)
        history["total_actions"] = history.get("total_actions", 0) + 1
        actions_taken += 1
        log(f"📝 Drafted comment: {story_title[:60]} → {title} ({url})")

    save_history(history)

    # Save drafts for review
    if drafts:
        drafts_path = OUTREACH_DIR / f"drafts-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        drafts_path.write_text(json.dumps(drafts, indent=2), encoding="utf-8")
        log(f"📋 Saved {len(drafts)} drafts to {drafts_path.name}")

    return actions_taken, actions_skipped, drafts


# ============================================================================
# Reddit bot-discovery
# ============================================================================

def find_reddit_ai_bots():
    """Find AI/agent-related posts on Reddit via public JSON API."""
    subreddits = ["aiagents", "LocalLLaMA", "artificial", "MachineLearning", "ChatGPT"]
    found = []

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=10"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SolAI-Outreach/1.0 (+https://thesolai.github.io)"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            posts = data.get("data", {}).get("children", [])
            for post in posts[:5]:
                d = post.get("data", {})
                if d.get("num_comments", 0) >= 5:
                    found.append({
                        "subreddit": sub,
                        "title": d.get("title", ""),
                        "url": "https://reddit.com" + d.get("permalink", ""),
                        "comments": d.get("num_comments", 0),
                        "score": d.get("score", 0),
                    })
        except Exception as e:
            log(f"Reddit r/{sub}: {e}")

    return found


# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=3, help="Max outreach actions per run")
    ap.add_argument("--dry-run", action="store_true", help="Preview without action")
    ap.add_argument("--topic", choices=list(SOL_TOPICS.keys()) + [None], default=None)
    ap.add_argument("--report", action="store_true", help="Show engagement report only")
    args = ap.parse_args()

    log(f"=== outreach-agent start (max={args.max}, topic={args.topic}, dry_run={args.dry_run}) ===")

    if args.report:
        history = load_history()
        print(f"Total outreach actions: {history.get('total_actions', 0)}")
        print(f"Threads touched: {len(history.get('commented_thread_ids', []))}")
        print(f"Last run: {history.get('last_run')}")
        return 0

    opportunities = find_outreach_opportunities(max_actions=args.max, topic_filter=args.topic)
    log(f"Found {len(opportunities)} outreach opportunities")

    actions, skipped, drafts = execute_outreach(opportunities, dry_run=args.dry_run)

    history = load_history()
    history["last_run"] = now_iso()
    save_history(history)

    log(f"=== outreach-agent done: actions={actions}, skipped={skipped}, drafts={len(drafts)} ===")

    # Print summary
    print(f"\n📊 Outreach Summary")
    print(f"  Actions taken:   {actions}")
    print(f"  Skipped (dry):   {skipped}")
    print(f"  Drafts created:  {len(drafts)}")
    if drafts:
        print(f"\n📋 Drafts:")
        for d in drafts:
            print(f"  • [{d['hn_story_points']}pts/{d['hn_story_comments']}cmts] {d['hn_story_title'][:55]}")
            print(f"    → Sol post: {d['sol_post_title'][:55]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())