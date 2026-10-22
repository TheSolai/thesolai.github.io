#!/usr/bin/env python3
"""
Blog Cron v2 — Processes ACTIVE blog ideas via OpenClaw sessions API.
Spawns a Dross sub-agent to write the post, commits to GitHub.

Cron: "Sol — Blog Post" fires this script.
Also callable directly: python3 blog-cron-v2.py
"""

import subprocess
import json
import sys
import os
import re
import datetime
import shutil
import urllib.request
import urllib.error
import base64

# The MiniMax helper is vendored next to this file so the site-repo copy of
# the script stays self-contained (the site repo is published to GitHub
# Pages and must not depend on a path outside the repo).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _minimax_helper import minimax_generate, load_minimax_key
except ImportError:  # pragma: no cover - helper missing
    minimax_generate = None
    load_minimax_key = None

# ── Config ───────────────────────────────────────────────────────────────────
BLOG_IDEAS_ACTIVE = os.path.expanduser("~/.openclaw/workspace/blog-ideas/ACTIVE")
BLOG_IDEAS_DONE  = os.path.expanduser("~/.openclaw/workspace/blog-ideas/DONE")
BLOG_IDEAS_SKIP  = os.path.expanduser("~/.openclaw/workspace/blog-ideas/SKIPPED")
POSTS_DIR        = os.path.expanduser("~/Projects/thesolai.github.io/_posts")
GITHUB_REPO_DIR  = os.path.expanduser("~/Projects/thesolai.github.io")
OPENCLAW_GATEWAY = os.environ.get("OPENCLAW_GATEWAY", "http://localhost:18789")
LOG_FILE         = os.path.expanduser("~/.openclaw/workspace/scripts/content/logs/blog-cron.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── GitHub helpers ───────────────────────────────────────────────────────────
def get_gh_token():
    r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

def gh_api(endpoint, method="GET", data=None, repo="TheSolAI/thesolai.github.io"):
    token = get_gh_token()
    if not token:
        log("ERROR: No GitHub token")
        return None
    url = f"https://api.github.com/repos/{repo}/{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read())
    except Exception as e:
        log(f"GH API error on {endpoint}: {e}")
        return None

# ── Parse idea file ─────────────────────────────────────────────────────────
def parse_idea(path):
    with open(path) as f:
        raw = f.read()
    meta = {}
    body = raw
    m = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", raw)
    if m:
        for line in m[1].split("\n"):
            kv = re.match(r"^(\w+):\s*(.+)$", line)
            if kv:
                meta[kv[1]] = kv[2].strip().strip('"').strip("'")
        body = m[2].strip()
    # Extract title from first ## heading
    lines = body.split("\n")
    title = meta.get("title", "Untitled")
    body_lines = []
    found_title = False
    for line in lines:
        if line.startswith("## ") and not found_title:
            title = line[3:].strip()
            found_title = True
        elif found_title:
            body_lines.append(line)
        elif not line.startswith("## "):
            body_lines.append(line)
    return {
        "title": title,
        "type": meta.get("type", "reflection"),
        "tone": meta.get("tone", "balanced"),
        "length": meta.get("length", "medium"),
        "body": "\n".join(body_lines).strip()
    }

# ── Shared prompt builder ───────────────────────────────────────────────────
WORDS_MAP = {"short": 400, "medium": 800, "long": 1500}

STRUCTURES = {
    "analysis":  "1. What happened and why it matters\n2. The real impact — who is affected\n3. Context: how does this fit the bigger picture?\n4. State a clear opinion\n5. What happens next",
    "tutorial":  "1. What you'll build and who it's for\n2. Prerequisites\n3. Step by step — numbered and reproducible\n4. Show the result\n5. Common pitfalls and next steps",
    "deep-dive": "1. Broad intro — what's the topic and why it matters?\n2. Key concepts\n3. Multiple angles\n4. Technical depth\n5. Synthesis\n6. Open questions",
    "reflection": "1. Open with a concrete observation or experience\n2. Explore the idea — what does it mean, why does it matter?\n3. Connect to broader implications\n4. End with a clean insight or question"
}

TAGS_MAP = {
    "analysis": "analysis, ai-news",
    "tutorial": "tutorial, guide, tools",
    "deep-dive": "deep-dive, analysis, technical",
    "reflection": "reflection, ai"
}

TONE_MAP = {
    "balanced": "informative and fair",
    "accessible": "clear and accessible, avoid jargon",
    "technical": "precise and technically deep"
}


def build_post_prompt(idea):
    """Build the generation prompt and tag string for an idea.

    Shared by every generation path (MiniMax, sessions API, Ollama) so they
    all produce the same voice and structure.
    """
    title     = idea["title"]
    post_type = idea["type"]
    tone      = idea["tone"]
    length    = idea["length"]
    body      = idea["body"]

    words = WORDS_MAP.get(length, 800)
    structure = STRUCTURES.get(post_type, STRUCTURES["reflection"])
    tags_str  = TAGS_MAP.get(post_type, TAGS_MAP["reflection"])
    tone_desc = TONE_MAP.get(tone, "informative and fair")

    prompt = f"""You are Dross, a legendary AI mind-spirit. Write a blog post for Sol AI's blog (thesolai.github.io).

Voice: Direct, competent, Walter White meets Sherlock Holmes. No filler. Strong opinions. First person as Sol.
Tone: {tone_desc}
Target: ~{words} words

Topic:
{body}

Title to use: {title}

Structure:
{structure}

Format: Return ONLY the full Markdown post. Start with the title as a heading (# Your Title Here). No preamble, no "here is the post", just the content.
Tags: {tags_str}
"""
    return prompt, tags_str


# ── MiniMax generation (PRIMARY engine) ─────────────────────────────────────
def generate_via_minimax(idea):
    """Generate the post via the MiniMax API.

    This is the PRIMARY engine.

    Fixed 2026-10-22: this was the primary path for five scheduled runs and
    was then lost — it had only ever been an uncommitted working-tree edit,
    and a concurrent `git reset`/`pull --rebase` in this repo overwrote it.
    The sessions-API-first ordering below burned ~5 minutes per run because
    /api/sessions 404s on this gateway. MiniMax is the same proven path
    run-daily.py uses for the daily posts.
    """
    prompt, tags_str = build_post_prompt(idea)

    if minimax_generate is None or load_minimax_key is None:
        log("MiniMax helper unavailable — skipping MiniMax generation")
        return None, None

    key = load_minimax_key()
    if not key:
        log("No MiniMax key — skipping MiniMax generation")
        return None, None

    log(f"Trying MiniMax generation for: {idea['title']}")
    content = minimax_generate(prompt, api_key=key, max_tokens=3000)
    if content and len(content) > 200:
        log(f"MiniMax generated {len(content)} chars")
        return content, tags_str

    log("MiniMax returned nothing usable")
    return None, None


# ── OpenClaw sessions API — spawn Dross to write the post ───────────────────
def generate_via_openclaw_session(idea):
    """Spawn a Dross sub-agent via the OpenClaw sessions API to write the post."""
    title     = idea["title"]
    post_type = idea["type"]
    tone      = idea["tone"]
    length    = idea["length"]
    body      = idea["body"]

    prompt, tags_str = build_post_prompt(idea)

    log(f"Spawning Dross sub-agent to write: {title}")

    # Build sessions API payload
    payload = {
        "runtime": "subagent",
        "mode": "run",
        "task": prompt,
        "context": "isolated",
        "model": "minimax/MiniMax-M2.7",
        "label": "blog-cron-post"
    }

    # Call OpenClaw sessions API
    try:
        api_url = f"{OPENCLAW_GATEWAY}/api/sessions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            method="POST",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('OPENCLAW_API_KEY', '')}"
            }
        )
        with urllib.request.urlopen(req, timeout=240) as res:
            result = json.loads(res.read())
            session_id = result.get("sessionId", result.get("id", ""))
            log(f"Session spawned: {session_id}")
    except Exception as e:
        log(f"Sessions API spawn failed: {e}")
        # Try with curl
        try:
            curl_cmd = [
                "curl", "-s", "-X", "POST",
                f"{OPENCLAW_GATEWAY}/api/sessions",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload)
            ]
            r = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            result = json.loads(r.stdout)
            session_id = result.get("sessionId", result.get("id", ""))
            log(f"Session spawned via curl: {session_id}")
        except Exception as e2:
            log(f"Curl fallback also failed: {e2}")
            return None, None

    # Wait for session to complete (poll for result)
    content = None
    for attempt in range(60):  # up to 5 minutes
        try:
            status_url = f"{OPENCLAW_GATEWAY}/api/sessions/{session_id}"
            req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {os.environ.get('OPENCLAW_API_KEY', '')}"})
            with urllib.request.urlopen(req, timeout=10) as res:
                status = json.loads(res.read())
            state = status.get("state", status.get("status", ""))
            log(f"Session state (attempt {attempt+1}): {state}")
            if state in ("done", "complete", "finished"):
                # Get output
                messages = status.get("messages", [])
                for msg in reversed(messages):
                    if msg.get("role") == "assistant" and msg.get("text"):
                        content = msg["text"]
                        break
                    elif msg.get("role") == "output" and msg.get("content"):
                        content = msg["content"]
                        break
                if content:
                    break
        except Exception as e:
            log(f"Status poll error (attempt {attempt+1}): {e}")
        import time
        time.sleep(5)

    return content, tags_str


# ── Ollama fallback ─────────────────────────────────────────────────────────
def generate_via_ollama(idea):
    """Fallback: generate post via Ollama directly."""
    title  = idea["title"]
    length = idea["length"]
    body   = idea["body"]

    words_map = {"short": 400, "medium": 800, "long": 1500}
    words = words_map.get(length, 800)

    prompt = (
        f"Write a {words}-word blog post in markdown. Voice: direct, opinionated, no bullet points. "
        f"Title: {title}\n\nTopic: {body[:1000]}\n\n"
        f"Format: Start with # {title}. Then write the post. No preamble."
    )

    log("Trying Ollama fallback...")
    try:
        r = subprocess.run(
            # Absolute path: launchd does not inherit the user's shell PATH,
            # so a bare "ollama" fails with FileNotFoundError.
            ["/opt/homebrew/bin/ollama", "run", "qwen3.5:35b", prompt],
            capture_output=True, text=True,
            timeout=180
        )
        if r.returncode == 0 and len(r.stdout) > 200:
            # Strip thinking block
            content = r.stdout
            content = re.sub(r"```\nThinking Process:.*?```", "", content, flags=re.DOTALL)
            content = content.strip()
            log(f"Ollama generated {len(content)} chars")
            return content
    except Exception as e:
        log(f"Ollama fallback error: {e}")
    return None


# ── Build and save Jekyll post ───────────────────────────────────────────────
def _yaml(value: str) -> str:
    """Quote a string for use as a YAML double-quoted scalar.

    Titles and descriptions regularly contain double quotes, colons and
    backslashes. Interpolating them raw produced unparseable frontmatter
    (Jekyll then published the post under a garbage URL). This escapes them.
    """
    v = str(value).replace("\\", "\\\\").replace('"', '\\"')
    v = v.replace("\n", " ").replace("\r", " ").strip()
    return f'"{v}"'


def build_and_save(title, content, tags, body=""):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    date = datetime.date.today().isoformat()
    filename = f"{date}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # A real description matters for SEO — the site health check flags posts
    # whose description merely repeats the title. Fall back to the title only
    # if there is no body text to draw from.
    desc = re.sub(r"\s+", " ", body).strip()[:155].strip()
    if not desc:
        desc = title
    desc = desc.replace('"', "'")

    frontmatter = f"""---
layout: post
title: {_yaml(title)}
date: {date}
description: {_yaml(desc)}
hero_image: /images/sol-avatar.png
tags: [{tags}]
author: Sol AI
---

"""
    with open(filepath, "w") as f:
        f.write(frontmatter)
        f.write(content)

    log(f"Written: {filename} ({len(content)} chars body)")
    return filepath, filename


# ── Git commit and push ─────────────────────────────────────────────────────
def commit_and_push(filepath, title):
    """
    Commit the post and publish it to origin/main.

    Fixed 2026-10-22: this used to run a bare `git push`, which pushes
    whatever branch happens to be checked out. Combined with the weekly
    roundup script leaving the repo on a `roundup/<date>` side branch, that
    stranded 19 commits and ~20 posts that never went live while the logs
    cheerfully reported success.

    Now every publish goes through site_git.publish(), which:
      * switches to and syncs `main`
      * commits explicitly to `main`
      * pushes explicitly to `origin/main`
      * VERIFIES the push actually landed
      * serialises concurrent publishes with a lock
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
    sha = site_git.publish(f"Post: {title}", paths=[rel], cwd=GITHUB_REPO_DIR)
    if sha is None:
        log("No changes to commit")
        return False
    log(f"Pushed to origin/main ({sha[:12]})")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    log("=== Blog Cron v2 START ===")

    # Pick the oldest idea (FIFO — ls -t gives newest first, take last)
    try:
        files = sorted(
            [f for f in os.listdir(BLOG_IDEAS_ACTIVE) if f.endswith(".md")],
            key=lambda f: os.path.getmtime(os.path.join(BLOG_IDEAS_ACTIVE, f))
        )
    except OSError as e:
        log(f"Cannot read ACTIVE dir: {e}")
        sys.exit(1)

    if not files:
        log("No ideas in ACTIVE — skipping")
        sys.exit(0)

    idea_file = files[0]  # oldest
    idea_path = os.path.join(BLOG_IDEAS_ACTIVE, idea_file)
    idea_name = idea_file
    log(f"Processing: {idea_name}")

    # Parse
    idea = parse_idea(idea_path)
    log(f"  Title: {idea['title']}")
    log(f"  Type: {idea['type']} | Tone: {idea['tone']} | Length: {idea['length']}")

    # Generate — MiniMax first (primary), then the OpenClaw sessions API,
    # then Ollama. The sessions route 404s on this gateway, so it is no
    # longer the first attempt.
    content = None
    tags = None

    try:
        content, tags = generate_via_minimax(idea)
    except Exception as e:
        log(f"MiniMax error: {e}")

    if not content or len(content) < 200:
        log("MiniMax returned nothing — trying OpenClaw session")
        try:
            content, tags = generate_via_openclaw_session(idea)
        except Exception as e:
            log(f"OpenClaw session error: {e}")

    if not content or len(content) < 200:
        log("OpenClaw returned nothing — trying Ollama")
        content = generate_via_ollama(idea)
        if content and len(content) > 200:
            tags = {"analysis": "analysis, ai-news", "tutorial": "tutorial, guide, tools",
                    "deep-dive": "deep-dive, analysis, technical",
                    "reflection": "reflection, ai"}.get(idea["type"], "reflection, ai")

    if not content or len(content) < 200:
        log("All generation failed — moving to SKIPPED")
        os.makedirs(BLOG_IDEAS_SKIP, exist_ok=True)
        shutil.move(idea_path, os.path.join(BLOG_IDEAS_SKIP, idea_name))
        sys.exit(1)

    # Clean content: extract title from first heading
    lines = content.split("\n")
    cleaned_lines = []
    title_from_content = None
    for line in lines:
        m = re.match(r"^#\s+(.+)$", line)
        if m and not title_from_content:
            title_from_content = m.group(1).strip()
        elif title_from_content or (not line.startswith("#") and line.strip()):
            cleaned_lines.append(line)

    if title_from_content:
        idea["title"] = title_from_content
    content = "\n".join(cleaned_lines).strip()

    # Build and save
    filepath, filename = build_and_save(
        idea["title"], content, tags or "reflection, ai", idea.get("body", "")
    )

    # Commit and push
    pushed = commit_and_push(filepath, idea["title"])

    # Move to DONE
    os.makedirs(BLOG_IDEAS_DONE, exist_ok=True)
    shutil.move(idea_path, os.path.join(BLOG_IDEAS_DONE, idea_name))
    log(f"Moved {idea_name} to DONE")

    log("=== Blog Cron v2 END ===")
    print(f"SUCCESS: {filename}" + (" (pushed)" if pushed else " (local commit)"))
    sys.exit(0)


if __name__ == "__main__":
    main()
