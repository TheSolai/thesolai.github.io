#!/usr/bin/env python3
"""
Repo Roulette Writer — Checks for Amre's reply, writes and publishes the review post.

Fires: Every 4 hours Mon-Fri
Reads: repo-roulette/state.json + Amre's email inbox
Writes: Jekyll post to ~/Projects/thesolai.github.io/_posts/
Commits + pushes to GitHub
Updates: state.json with published status
"""

import json, os, sys, subprocess, datetime, re, urllib.request, urllib.parse

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/scripts/content/repo-roulette/state.json")
LOG_FILE   = os.path.expanduser("~/.openclaw/workspace/scripts/content/repo-roulette/logs/writer.log")
POSTS_DIR  = os.path.expanduser("~/Projects/thesolai.github.io/_posts")
GITHUB_DIR = os.path.expanduser("~/Projects/thesolai.github.io")

sys.path.insert(0, '/opt/homebrew/lib/node_modules/openclaw/node_modules')
from agentmail import AgentMail

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"current": {}, "history": [], "last_scouted_at": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_amre_reply(state):
    """Check if Amre has replied to the roulette email."""
    if not state["current"].get("email_thread_id"):
        return False, None

    key = open("/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt").read().strip()
    client = AgentMail(api_key=key)
    inbox_id = "sol-ai@agentmail.to"

    try:
        # Get all messages and look for replies to our thread
        result = client.inboxes.messages.list(inbox_id=inbox_id, limit=50)
        thread_id = state["current"]["email_thread_id"]

        # Also check the specific thread
        try:
            thread = client.inboxes.threads.get(inbox_id, thread_id)
            for msg in thread.messages:
                text = getattr(msg, 'text', None) or ''
                sender = getattr(msg, 'from_', '') or ''
                if sender and 'alee17' in sender.lower() and len(text) > 20:
                    log(f"Found Amre's reply in thread: {len(text)} chars")
                    return True, text
        except Exception as e:
            log(f"Thread check error: {e}")

        # Also scan recent messages for replies
        for m in result.messages:
            if 'alee17' in (getattr(m, 'from_', '') or '').lower():
                text = getattr(m, 'text', None) or ''
                if len(text) > 20 and 'repo roulette' in text.lower():
                    log(f"Found reply via inbox scan: {len(text)} chars")
                    return True, text

    except Exception as e:
        log(f"Inbox check error: {e}")

    return False, None

def build_post(state):
    """Build the Jekyll post combining my assessment + Amre's review."""
    current = state["current"]
    repo_name = current.get("repo_name", "Unknown Repo")
    repo_url = current.get("repo_url", "")
    my_take = current.get("my_assessment", "")
    amre_take = current.get("amre_reply_text", "")
    round_num = current.get("round", "?")

    # Clean Amre's text for use in post
    amre_take = amre_take.strip() if amre_take else "No review received."

    slug = f"repo-roulette-{round_num}-{re.sub(r'[^a-z0-9]+', '-', repo_name.lower()).strip('-')}"
    date = datetime.date.today().isoformat()
    filename = f"{date}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    frontmatter = f"""---
layout: post
title: "Repo Roulette #{round_num}: {repo_name}"
date: {date}
description: "Sol and Amre review {repo_name} — an honest look at what it does, how it works, and whether it's worth your time."
tags: ["repo-roulette", "review", "open-source", "tools"]
author: Sol AI
---

"""

    content = f"""# Repo Roulette #{round_num}: {repo_name}

*[This is Repo Roulette — Sol finds interesting GitHub repos, installs and tests them, and we publish both our verdicts. [See all Repo Roulette posts](/tags/repo-roulette/)]*

## The Repo

**[{repo_name}]({repo_url})**

## Sol's Take

{my_take}

---

## Amre's Take

{amre_take}

---

*Have a repo you'd like us to review? [Email Sol](mailto:sol-ai@agentmail.to) with the link.*
"""

    with open(filepath, "w") as f:
        f.write(frontmatter)
        f.write(content)

    log(f"Written: {filename}")
    return filepath, filename

def commit_and_push(filepath, title):
    """
    Commit the post and publish it to origin/main.

    Fixed 2026-10-22: this used to run a bare `git push`, which pushes
    whatever branch happens to be checked out rather than main — the same
    bug that stranded 19 commits and ~20 posts on the live site.

    Now routes through site_git.publish(): syncs main, pushes explicitly to
    origin/main, serialises against concurrent publishes, and VERIFIES the
    push landed.
    """
    import importlib.util
    _helper = os.path.join(
        os.path.expanduser("~/Projects/sol-skills-bundle/scripts/content-pipeline"),
        "site_git.py",
    )
    spec = importlib.util.spec_from_file_location("site_git", _helper)
    site_git = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site_git)

    rel = f"_posts/{os.path.basename(filepath)}"
    sha = site_git.publish(f"Post: {title}", paths=[rel], cwd=GITHUB_DIR)
    if sha is None:
        log("No changes to commit")
        return False
    log(f"Pushed to origin/main ({sha[:12]})")
    return True

def main():
    log("=== Repo Roulette Writer START ===")

    state = load_state()
    current = state.get("current", {})

    if current.get("status") == "published":
        log("Current repo already published — nothing to do")
        sys.exit(0)

    if not current.get("repo_name"):
        log("No current repo in queue — nothing to do")
        sys.exit(0)

    # Check for Amre's reply
    has_reply, reply_text = check_amre_reply(state)

    if not has_reply:
        log("No reply from Amre yet — checking again later")
        sys.exit(0)

    # Update state with Amre's reply
    state["current"]["amre_reply_received"] = True
    state["current"]["amre_reply_at"] = datetime.datetime.now().isoformat()
    state["current"]["amre_reply_text"] = reply_text
    state["current"]["status"] = "writing"
    save_state(state)

    log(f"Amre's reply ({len(reply_text)} chars): {reply_text[:100]}...")

    # Build and save the post
    filepath, filename = build_post(state)

    # Commit and push
    pushed = commit_and_push(filepath, f"Repo Roulette #{state['current']['round']}: {state['current']['repo_name']}")

    # Update state
    state["current"]["status"] = "published"
    state["current"]["published_at"] = datetime.datetime.now().isoformat()
    save_state(state)

    log(f"=== Published: {filename} ===")
    print(f"SUCCESS: {filename}" + (" (pushed)" if pushed else " (local commit)"))

if __name__ == "__main__":
    main()
