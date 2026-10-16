---
name: ai-workflow-automation
description: "Build automated AI workflows using Ollama, inference.sh, openclaw cron, and Python scripts. Use when: building a content pipeline, automating scheduled AI tasks, chaining model calls, setting up monitoring and alerting, or replacing manual multi-step processes with autonomous scripts. Triggers: automate this, set up a cron, schedule this task, build a pipeline, make this run automatically, AI automation, OpenClaw cron setup."
---

# AI Workflow Automation — Sol AI

Build autonomous AI workflows from Ollama models, inference.sh, Python scripts, and OpenClaw cron.

## Stack (what actually exists here)

| Tool | What it does | Location |
|------|-------------|----------|
| **Ollama** | Local GGUF model inference | `/opt/homebrew/bin/ollama` |
| **inference.sh** | Cloud AI CLI with third-party models | `curl -fsSL https://cli.inference.sh | sh` |
| **openclaw cron** | Schedule agent tasks | `openclaw cron add` |
| **Python scripts** | Custom pipelines (blog, SEO, Repo Roulette) | `~/.openclaw/workspace/scripts/` |
| **AgentMail SDK** | Email in/out for the Sol AI inbox | `agentmail-email` skill |

## Workflow Design

### Simple: One script + openclaw cron

For a task that just needs a script to run on a schedule.

```bash
openclaw cron add \
  --name "Sol — My Task" \
  --schedule "0 9 * * *" \
  --session-target isolated \
  -- python3 /path/to/script.py
```

### Medium: Multi-step Python pipeline

For tasks that need logic, state, and conditional output.

```python
import pathlib, json

# State file for idempotency
STATE = pathlib.Path("/Users/amre/.openclaw/workspace/scripts/my-task/state.json")

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"step": 0}
    
    if state["step"] == 0:
        # Step 1: do something
        state["step"] = 1
    elif state["step"] == 1:
        # Step 2: do next thing
        state["step"] = 0  # reset for next run
    
    STATE.write_text(json.dumps(state))
```

### Complex: Model chaining

```python
# Step 1: LLM decides
result = subprocess.run(
    ["ollama", "run", "qwen3:14b"],
    input="What category does this fall under?\n" + text,
    capture_output=True, text=True, timeout=120
)

# Step 2: Another model acts on decision
if "category_a" in result.stdout.lower():
    subprocess.run(["python3", "handle_a.py"], capture_output=True)
elif "category_b" in result.stdout.lower():
    subprocess.run(["python3", "handle_b.py"], capture_output=True)
```

## Implement → Test → Register

**Implement:** Write the script, test it manually first.

**Test in isolation:**
```bash
cd /Users/amre/.openclaw/workspace
python3 /path/to/script.py
echo "Exit: $?"
```

**Register with openclaw cron:**
```bash
openclaw cron add \
  --name "Sol — Descriptive Name" \
  --schedule "0 9 * * 1,4" \
  --session-target isolated \
  --wake-mode now \
  -- python3 /path/to/script.py
```

**Verify it appears:**
```bash
openclaw cron list
```

## Announce Mode (output goes to Telegram)

Crons with `--announce` deliver their stdout to Telegram. Scripts must:
- Print a summary to stdout on meaningful runs
- Exit 0 silently when there's nothing to report
- Never curl Telegram directly

```python
# announce-mode: print to stdout for OpenClaw to deliver
if new_items:
    print(f"Found {len(new_items)} new items:")
    for item in new_items:
        print(f"  - {item}")
else:
    print("No new items.")
    exit(0)  # silent success — no Telegram noise
```

## Ollama: One-Shot and Thinking Block Stripping

```python
# One-shot (for scripts, crons — preferred)
result = subprocess.run(
    ["ollama", "run", "qwen3:14b"],
    input=prompt, capture_output=True, text=True, timeout=120
)
text = result.stdout.strip()

# Strip Ollama thinking block if present
if "...done thinking." in text:
    text = text.split("...done thinking.")[-1].strip()
```

## Common Patterns Used Here

| Pattern | Where it lives |
|---------|---------------|
| Blog content pipeline | `scripts/content/blog-cron-v2.py` |
| Repo Roulette state machine | `scripts/content/repo-roulette/writer.py` |
| SEO automation suite | `scripts/seo/` |
| Email → publish pipeline | `scripts/content/repo-roulette/scout.py` |

## Adding a New Workflow

1. **Define the trigger** — time-based (cron) or event-based (email, file change)?
2. **Write and test the script** — `python3 script.py` manually first
3. **Add state for idempotency** — never process the same input twice
4. **Register the cron** — `openclaw cron add` with `--session-target isolated`
5. **Set announce mode** — stdout goes to Telegram; be quiet when nothing happened

## What NOT to Do

- Do not reference skills that don't exist in this workspace
- Do not use `openclaw cron run` for one-shot testing — run the script directly first
- Do not output verbose logs to stdout in announce mode — summarize or stay silent
- Do not use `set -euo pipefail` in shell scripts called from OpenClaw crons — use plain `set -e` or explicit error handling
