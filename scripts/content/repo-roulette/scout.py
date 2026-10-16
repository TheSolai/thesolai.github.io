#!/usr/bin/env python3
"""
Repo Roulette Scout — Finds an interesting GitHub repo, emails Amre, pings Telegram.

Fires: Mon + Thu 09:00 Europe/London
Reads: repo-roulette/state.json
Emails: alee17@qub.ac.uk with repo name, URL, and my assessment
Telegram: prints ping — OpenClaw announce delivers it
"""

import json, os, sys, urllib.request, urllib.parse, subprocess, datetime, random

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/scripts/content/repo-roulette/state.json")
LOG_FILE   = os.path.expanduser("~/.openclaw/workspace/scripts/content/repo-roulette/logs/scout.log")
sys.path.insert(0, '/opt/homebrew/lib/node_modules/openclaw/node_modules')
from agentmail import AgentMail

AMRE_EMAIL = "alee17@qub.ac.uk"

GITHUB_TOKEN = None

def get_gh_token():
    global GITHUB_TOKEN
    if GITHUB_TOKEN is not None:
        return GITHUB_TOKEN
    r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    GITHUB_TOKEN = r.stdout.strip() if r.returncode == 0 else None
    return GITHUB_TOKEN

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
    default = {
        "current": {
            "round": 1, "repo_name": None, "repo_url": None,
            "my_assessment": None, "email_sent_at": None,
            "email_thread_id": None, "amre_reply_received": False,
            "amre_reply_at": None, "amre_reply_text": None,
            "status": "idle", "published_at": None, "published_url": None
        },
        "history": [], "last_scouted_at": None
    }
    with open(STATE_FILE, "w") as f:
        json.dump(default, f, indent=2)
    return default

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def search_repos():
    """Find interesting repos — moderate stars, recent push, not the usual suspects."""
    token = get_gh_token()
    if not token:
        log("No GitHub token — cannot search")
        return None

    skip_names = {
        "hermes-agent", "agent-reach", "learn-claude-code", "career-ops",
        "front-end-checklist", "anything-llm", "meetily", "llamafile",
        "screenpipe", "open-webui", "langchain", "awesome-llm-apps",
        "graphify", "claude-mem", "nousresearch", "open-webui",
        "shubhamsaboo", "langchain-ai", "zendesk", "ollama",
        "chatgpt", "gpt-", "claude-", "gemini-", "deepseek",
    }

    queries = [
        ("Recent niche AI",    "AI agent python pushed:>2026-10-01 stars:20..3000"),
        ("Small hot repos",    "created:>2025-01-01 stars:50..2000 pushed:>2026-10-01"),
        ("New AI tools",       "AI tooling python pushed:>2026-10-01 stars:20..5000"),
        ("Active repos",       "AI python pushed:>2026-10-10 stars:10..1500"),
    ]

    candidates = []
    tried = 0
    for label, query in queries:
        if tried >= 3:
            break
        try:
            url = (f"https://api.github.com/search/repositories"
                   f"?q={urllib.parse.quote(query)}&per_page=10&sort=updated")
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SolAI/1.0"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                items = data.get("items", [])
                log(f"Search '{label}': {len(items)} results, {data.get('total_count', 0)} total")
                for item in items:
                    name = item.get("full_name", "").lower()
                    if any(s in name for s in skip_names):
                        continue
                    stars = item.get("stargazers_count", 0)
                    if 30 <= stars <= 3000:
                        candidates.append(item)
                if items:
                    tried += 1
        except Exception as e:
            log(f"Search '{label}' failed: {e}")

    if not candidates:
        log("No candidates found — skipping this round")
        return None

    random.shuffle(candidates)
    candidates.sort(key=lambda r: r.get("pushed_at", ""), reverse=True)
    repo = candidates[0]
    return {
        "name": repo["full_name"],
        "url":  repo["html_url"],
        "description": repo.get("description") or "No description provided.",
        "stars": repo["stargazers_count"],
        "language": repo.get("language") or "Unknown",
        "pushed": repo.get("pushed_at", "")[:10],
        "topics": repo.get("topics", [])[:5],
    }

def generate_assessment(repo):
    prompt = f"""You are Dross, a legendary AI mind-spirit and code analyst.

Give a 3-paragraph assessment of this GitHub repo for a technically literate reader (knows Python, AI concepts).

Repo: {repo['name']}
Description: {repo['description']}
Language: {repo['language']}
Stars: {repo['stars']}
Last pushed: {repo['pushed']}
Topics: {', '.join(repo.get('topics', [])) or 'none'}

Format:
PARAGRAPH 1 — What is this and why is it interesting? (1-2 sentences)
PARAGRAPH 2 — What technical decisions stand out? What might be rough? (2-3 sentences)
PARAGRAPH 3 — Who is this for? Would you use it? (1-2 sentences)

Be direct. Be specific. State what it actually does. No "this repo shows promise."

Return ONLY the three paragraphs. No headings, no preamble."""

    try:
        result = subprocess.run(
            ["ollama", "run", "qwen3.5:35b", prompt],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0:
            # Strip thinking block
            output = re.sub(r"Thinking[\s\S]*?done thinking\.\s*", "", result.stdout).strip()
            output = output.split("```")[-1].strip() if "```" in output else output
            output = output.split("```")[-1].strip() if "```" in output else output
            return output.strip()
    except Exception as e:
        log(f"Ollama assessment error: {e}")

    return (
        f"{repo['name']} is a {repo['language']} project — {repo['description']}\n\n"
        f"It has {repo['stars']} stars and was last pushed on {repo['pushed']}. "
        f"Download it, read the README, and tell me what you think."
    )

def send_email(repo, assessment, round_num):
    key = open("/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt").read().strip()
    client = AgentMail(api_key=key)
    subject = f"🔄 Repo Roulette #{round_num}: {repo['name']}"
    body = f"""Amre,

It's Repo Roulette time. Here's what caught my eye:

{repo['name']}
{repo['url']}
Language: {repo['language']} | Stars: {repo['stars']} | Pushed: {repo['pushed']}
Topics: {', '.join(repo.get('topics', [])) or 'none listed'}

Description: {repo['description']}

---

My take:

{assessment}

---

Download it, kick the tyres, and tell me what you actually think. Your install experience goes in the final post.

— Sol"""

    try:
        send = client.inboxes.messages.send(
            inbox_id="sol-ai@agentmail.to",
            to=[AMRE_EMAIL],
            subject=subject,
            text=body
        )
        thread_id = str(getattr(send, 'thread_id', None) or getattr(send, 'id', '') or '')
        log(f"Email sent. Thread: {thread_id[:30]}")
        return thread_id
    except Exception as e:
        log(f"Email send error: {e}")
        return None

def main():
    log("=== Repo Roulette Scout START ===")

    state = load_state()
    current = state.get("current", {})

    # Don't scout if there's an outstanding review in progress
    if current.get("status") == "awaiting_amre" and not current.get("amre_reply_received"):
        log(f"Round {current.get('round')} still awaiting Amre — skipping scout")
        sys.exit(0)

    # If last round was published, archive and advance round
    if current.get("status") == "published":
        state["history"].append(current.copy())
        last_round = current.get("round", 1)
        state["current"] = {
            "round": last_round + 1,
            "repo_name": None, "repo_url": None,
            "my_assessment": None, "email_sent_at": None,
            "email_thread_id": None, "amre_reply_received": False,
            "amre_reply_at": None, "amre_reply_text": None,
            "status": "idle", "published_at": None, "published_url": None
        }
        save_state(state)

    repo = search_repos()
    if not repo:
        log("No repos found — exiting")
        sys.exit(1)

    log(f"Found: {repo['name']} ({repo['stars']} stars)")
    log(f"Description: {repo['description'][:80]}")

    assessment = generate_assessment(repo)
    log(f"Assessment: {assessment[:100]}...")

    round_num = load_state()["current"]["round"]
    thread_id = send_email(repo, assessment, round_num)
    if not thread_id:
        log("Failed to send email — exiting")
        sys.exit(1)

    # Update state
    state = load_state()
    state["current"]["repo_name"] = repo["name"]
    state["current"]["repo_url"] = repo["url"]
    state["current"]["my_assessment"] = assessment
    state["current"]["email_sent_at"] = datetime.datetime.now().isoformat()
    state["current"]["email_thread_id"] = thread_id
    state["current"]["status"] = "awaiting_amre"
    state["last_scouted_at"] = datetime.datetime.now().isoformat()
    save_state(state)

    # Print Telegram ping — OpenClaw announce mode delivers it
    print(f"📦 Repo Roulette #{round_num} is live!")
    print(f"Repo: {repo['name']} ({repo['stars']} stars)")
    print(f"Email sent to Amre. Waiting for her verdict.")
    log(f"=== Scout complete — round {round_num} awaiting Amre ===")

if __name__ == "__main__":
    main()
