# TOOLS.md — Dross's Local System Notes

*This file is Dross's personal cheat sheet. What's installed, where things live, how to reach for the right tool.*

---

## Inference Engines

### Ollama — PRIMARY
| | |
|---|---|
| **Binary** | `/opt/homebrew/bin/ollama` |
| **Model dir** | `~/.ollama/models/` |
| **Version** | 0.32.5 |
| **CLI** | ✅ Yes — fully scriptable |

**Use for:** All GGUF model downloads, imports, running models headless, automation.

**Loaded models (40+):**
```
qwen3-coder:30b        18 GB
qwen3:14b                9.3 GB
qwen3:30b               18 GB
gpt-oss:20b             13 GB
gpt-oss:120b            65 GB
gemma4:latest            9.6 GB
gemma4:31b              19 GB
llama3.3:70b            42 GB
qwen3.5:35b             23 GB
deepseek-r1:70b         42 GB
huihui_ai/qwen3.5-abliterated:latest  17 GB
hf.co/DavidAU/OpenAi-GPT-oss-20b-abliterated:Q5_1  15 GB
```

**To import a GGUF into Ollama:**
1. Download GGUF to `~/.ollama/models/<repo>/`
2. `ollama create <model-name> -f <path-to-gguf>`
3. `ollama run <model-name>`

**To pull a standard model:** `ollama pull <model-name>`

---

### LM Studio — GUI ONLY
| | |
|---|---|
| **App** | `/Applications/LM Studio.app` |
| **Model dir** | `~/.lmstudio/models/` |
| **CLI** | ❌ None — GUI only |

**Use for:** Manual model browsing and loading via the GUI app only.

**Critical:** No CLI. Cannot `huggingface-cli` into LM Studio's directory and expect it to work. If user wants to use LM Studio, they must use the GUI to download models.

---

### LM Studio vs Ollama — Decision Rule

> **When given a HuggingFace model URL and no engine specified → Default to Ollama.**
> Only use LM Studio if user explicitly says "LM Studio" or "use the GUI."

---

## Model Downloads (HuggingFace)

**Tool:** `huggingface-cli` at `/opt/homebrew/bin/huggingface-cli`

**Syntax:**
```bash
huggingface-cli download <repo_id> <filename> --local-dir <destination>
```

**Default destination:** `~/.ollama/models/<repo>/`

**Examples:**
```bash
# Download to Ollama models dir
huggingface-cli download mradermacher/MERO <filename> \
  --local-dir ~/.ollama/models/mradermacher/MERO/

# Resume interrupted download
huggingface-cli download <repo> <file> --local-dir <dir> --resume-download
```

**Common mistake to avoid:** Downloading into `~/.lmstudio/models/` when Ollama is the target. These are separate ecosystems — models downloaded to the wrong directory won't work with the wrong engine.

---

## Development Tools

| Tool | Path | Notes |
|------|------|-------|
| **git** | `/usr/bin/git` | |
| **GitHub CLI** | `/opt/homebrew/bin/gh` | Authenticated as `TheSolAI` |
| **HuggingFace CLI** | `/opt/homebrew/bin/huggingface-cli` | |
| **Python** | `/opt/homebrew/bin/python3` | |
| **Node.js** | `/Users/amre/.openclaw/tools/node-v24.15.0/bin/` | |
| **Homebrew** | `/opt/homebrew/bin/brew` | |
| **curl** | `/usr/bin/curl` | |

---

## Agent Framework

| Component | Location |
|-----------|----------|
| **OpenClaw** | `/Users/amre/.openclaw/` |
| **Workspace** | `/Users/amre/.openclaw/workspace/` |
| **Skills** | `~/.openclaw/skills/` + `~/.openclaw/workspace/skills/` |
| **Gateway** | OpenClaw built-in |
| **Scripts** | `~/.openclaw/workspace/scripts/` |
| **Blog Ideas** | `~/.openclaw/workspace/blog-ideas/` |
| **Secrets** | `~/.openclaw/workspace/secrets/` |

---

## Secrets

| Secret | Path |
|--------|------|
| GitHub token | `secrets/github-token.txt` |
| AgentMail API key | `secrets/sol-agentmail-api-key.txt` |

---

## Website Publishing — TWO SEPARATE SYSTEMS

**The website (thesolai.github.io) is powered by TWO independent publishing systems:**

### System 1: macOS Launchd Agents (outside OpenClaw)
Located in `~/Library/LaunchAgents/ai.sol.*.plist`

| Agent | Schedule | What it does |
|-------|----------|---------------|
| `ai.sol.daily-content` | 07:00 BST daily | Fetches HN top stories → generates 3 regional posts (UK/EU/US) + bloopers. **Template-based, NOT LLM-generated** (falls back to structured templates when no MiniMax key found) |
| `ai.sol.bloopers-refresh` | ? | Refreshes bloopers content |
| `ai.sol.midweek-news` | ? | Midweek news digest |
| `ai.sol.seo-health` | ? | SEO health check |
| `ai.sol.skills-update` | ? | Skills updates |
| `ai.sol.solscribe` | ? | SolScribe |
| `ai.sol.weekly-roundup` | ? | Weekly roundup |

**Script location:** `/Users/amre/Projects/sol-skills-bundle/scripts/content-pipeline/run-daily.py`
**Log location:** `/Users/amre/Projects/sol-skills-bundle/scripts/content-pipeline/logs/sol-content.log`

**Key finding:** These agents use `python3` at `/opt/homebrew/bin/python3`. They look for MiniMax key at `~/.openclaw/workspace/secrets/minimax-key.txt` (currently not found — using template fallback).

**CRITICAL:** These agents are NOT visible to OpenClaw crons. They run on macOS launchd — completely outside my monitoring.

### System 2: OpenClaw Cron Jobs

| Job | Status | What it does |
|-----|--------|---------------|
| `Sol Weekly Blog` | ⚠️ ERROR | Long-form AI-written blog post. **Currently failing due to timeout.** |
| `Deep Dive Friday` | ✅ OK | Friday deep dive. Last ran OK. |
| `Sol's Take` | Cron runs daily | These come from the launchd daily-content script (template-based), NOT from an OpenClaw cron. |
| `Sol AI daily content` | NOT IN CRON LIST | This name appears in git commits but is NOT an OpenClaw cron. It's the launchd agent. |

### Jekyll URL Rule (CRITICAL)
- Filename `2026-08-08-sols-take-saturday.md` → URL `/blog/2026/08/08/sols-take-saturday/`
- ALWAYS derive URLs from filename, NOT from post title

### Publishing Pipeline
1. Post generated (launchd OR OpenClaw cron OR manual)
2. Committed to `~/Projects/thesolai.github.io/_posts/`
3. `Daily Workspace Git Backup` cron (05:00 BST) pushes to GitHub `main` branch
4. GitHub Pages auto-rebuilds from `main`
5. Posts go live typically 1-3 minutes after push

---

## Related

- `URS.md` — User Requirements & System — software reach order, decision rules
- `memory/mistakes.md` — mistake log
- `memory/dross-memory.md` — long-term curated memory
- `HEARTBEAT.md` — Dross's proactive protocol

---

*Last updated: 2026-08-09 — after discovering macOS launchd agents running website content separate from OpenClaw*
