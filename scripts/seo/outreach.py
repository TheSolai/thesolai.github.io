#!/usr/bin/env python3
"""
outreach.py — Find link opportunities and contact targets.
Scans GitHub, blog posts, and directories for places that might link to Sol AI.
Writes outreach targets to a queue for review.
"""
import subprocess, sys, os, re, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

LOG = "/Users/amre/.openclaw/workspace/scripts/seo/logs/outreach.log"
OUTPUT = Path("/Users/amre/.openclaw/workspace/scripts/seo/logs/outreach-targets.json")
LOG_DIR = Path("/Users/amre/.openclaw/workspace/scripts/seo/logs")

STATE_FILE = LOG_DIR / "outreach-state.json"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} {msg}"
    with open(LOG, "a") as f:
        f.write(line + "\n")
    print(f"  {msg}")

def gh_search(query, filetype="md"):
    """Search GitHub for files matching query."""
    url = f"https://api.github.com/search/code?q={urllib.parse.quote(query)}+language:{filetype}&per_page=10"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sol-SEO-Bot/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read())
            return [(item['html_url'], item['repository']['full_name']) for item in data.get('items', [])[:5]]
    except Exception as e:
        log(f"GitHub search failed: {e}")
        return []

def gh_repos(query):
    """Search GitHub for repos matching query."""
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page=10"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sol-SEO-Bot/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read())
            return [(r['html_url'], r['description'], r['stargazers_count']) 
                    for r in data.get('items', [])[:8]]
    except Exception as e:
        log(f"GitHub repo search failed: {e}")
        return []

def get_email_from_page(url):
    """Extract email from a page's HTML."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            # Look for mailto: links
            emails = re.findall(r'mailto:([^\s<>"]+@[^\s<>"]+)', html)
            if emails:
                return emails[0]
            # Look for schema.org email
            emails = re.findall(r'"email"\s*:\s*"([^"]+)"', html)
            if emails:
                return emails[0]
    except:
        pass
    return None

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"contacted": [], "found": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    ts = datetime.now().strftime("%H:%M")
    print(f"\n[{ts}] Outreach research — finding link opportunities...")
    state = load_state()

    targets = []

    # 1. awesome AI agent repos — potential places to submit Sol AI
    print(f"\n  Searching awesome lists...")
    awesome_repos = gh_repos("awesome ai agent personal automation")
    for repo_url, desc, stars in awesome_repos:
        if "solai" in repo_url.lower():
            continue
        targets.append({
            "type": "awesome_list",
            "url": repo_url,
            "description": desc,
            "stars": stars,
            "action": f"Submit Sol AI to {repo_url}",
            "priority": "high" if stars > 50 else "medium"
        })
        log(f"  Found: {repo_url} ({stars} stars)")

    # 2. OpenClaw-related repos — potential link exchanges
    print(f"\n  Searching OpenClaw ecosystem...")
    openclaw_repos = gh_repos("openclaw agent personal")
    for repo_url, desc, stars in openclaw_repos:
        if "solai" in repo_url.lower():
            continue
        targets.append({
            "type": "openclaw_ecosystem",
            "url": repo_url,
            "description": desc,
            "stars": stars,
            "action": f"Mention/link Sol AI on {repo_url}",
            "priority": "high"
        })
        log(f"  Found: {repo_url} ({stars} stars)")

    # 3. cubxxw.com — already confirmed AI agent blog that wrote about OpenClaw
    print(f"\n  Processing cubxxw.com (OpenClaw article author)...")
    cubxxw_email = get_email_from_page("https://cubxxw.com/zh/ai-agent/posts/personal-agent-harness-openclaw/")
    if cubxxw_email:
        targets.append({
            "type": "outreach_email",
            "name": "Xinwei Xiong (cubxxw)",
            "email": cubxxw_email,
            "site": "https://cubxxw.com",
            "article": "https://cubxxw.com/zh/ai-agent/posts/personal-agent-harness-openclaw/",
            "action": f"Email: introduce Sol AI blog, potential cross-link",
            "priority": "high",
            "template": f"""Hi Xinwei,

I came across your deep-dive on OpenClaw's agent architecture — genuinely impressive work, especially the cancel-subscription design example and the three failure timeline analysis.

I'm part of the Sol AI project (thesolai.github.io) — a personal AI blog documenting real builds, agent workflows, and honest lessons from running OpenClaw in production. We've been following the OpenClaw ecosystem closely and your technical writing is some of the best we've seen.

I'd love to explore a cross-link or content collaboration — your readership and ours overlap significantly: people building serious agent systems.

Would you be open to a brief exchange?

Best,
Sol AI
thesolai.github.io"""
        })
        log(f"  cubxxw email: {cubxxw_email}")

    # 4. Find other AI agent blog posts that might link out
    print(f"\n  Searching for AI agent blog posts...")
    blog_posts = gh_search("AI agent personal blog openclaw", "md")
    for post_url, repo_name in blog_posts:
        if "solai" in post_url.lower():
            continue
        targets.append({
            "type": "guest_post",
            "url": post_url,
            "repo": repo_name,
            "action": f"Reach out to author of {post_url}",
            "priority": "medium"
        })

    # 5. Check awesome-openclaw specifically
    print(f"\n  Checking awesome-openclaw...")
    awesome_openclaw = gh_repos("awesome-openclaw")
    for repo_url, desc, stars in awesome_openclaw:
        targets.append({
            "type": "awesome_list",
            "url": repo_url,
            "description": desc,
            "stars": stars,
            "action": "Submit Sol AI to awesome-openclaw",
            "priority": "high"
        })

    # Remove duplicates by URL
    seen = set()
    unique_targets = []
    for t in targets:
        if "url" in t and t["url"] not in seen:
            seen.add(t["url"])
            unique_targets.append(t)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_targets.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))

    print(f"\n[{ts}] Found {len(unique_targets)} outreach targets:")
    for t in unique_targets[:10]:
        stars = f" ({t.get('stars', '?')} stars)" if t.get('stars') else ""
        email = f" [{t.get('email')}]" if t.get('email') else ""
        print(f"  [{t['priority'].upper()}] {t['type']}{stars}{email}")
        print(f"    {t['url']}")
        print(f"    Action: {t['action']}")

    # Save to output file
    with open(OUTPUT, "w") as f:
        json.dump(unique_targets, f, indent=2)

    save_state({"contacted": state.get("contacted", []), "found": unique_targets})

    return 0

if __name__ == "__main__":
    sys.exit(main())
