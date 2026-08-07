# User Requirements & System (URS)

*What the system should reach for, and when.*

---

## Inference Engines — RANKED

When installing or running models from HuggingFace URLs or local GGUF files:

| Priority | Engine | Model Storage | CLI Available |
|----------|--------|---------------|---------------|
| **1st** | **Ollama** | `~/.ollama/models/` | ✅ `/opt/homebrew/bin/ollama` |
| 2nd | LM Studio | `~/.lmstudio/models/` | ❌ GUI only |

**Rule:** When given a HuggingFace model URL with no engine specified, reach for **Ollama first**. Ollama is the primary inference engine. LM Studio is a GUI fallback for manual use — it has no CLI.

**Never assume** which engine is wanted. If unsure, ask.

---

## Model Download Rules

### Ollama (PRIMARY)
- **Model directory:** `~/.ollama/models/<repo>/`
- **Import GGUF:** Download GGUF → use `ollama create` to register
- **Existing models:** `ollama list` to see what's loaded
- **Pull directly:** `ollama pull <model>` for standard models

### LM Studio (GUI ONLY)
- **Model directory:** `~/.lmstudio/models/`
- **No CLI** — models must be downloaded via the GUI itself
- **Do NOT use `huggingface-cli`** to download into LM Studio's directory
- Only appropriate if user explicitly says "LM Studio" or "use the GUI"

### HuggingFace Downloads
- Use `huggingface-cli download <repo_id> <file> --local-dir <path>`
- **Default target: Ollama's directory** (`~/.ollama/models/`)
- URL pattern `hf.co/...` → Ollama unless user says otherwise

---

## Installed Software

### AI / Inference
| Software | Path | Version | Notes |
|----------|------|---------|-------|
| **Ollama** | `/opt/homebrew/bin/ollama` | 0.32.5 | PRIMARY — 40+ models loaded |
| **LM Studio** | `/Applications/LM Studio.app` | — | GUI only, no CLI |

### Development / System
| Software | Path | Notes |
|----------|------|-------|
| **git** | `/usr/bin/git` | |
| **GitHub CLI** | `/opt/homebrew/bin/gh` | Authenticated as TheSolAI |
| **HuggingFace CLI** | `/opt/homebrew/bin/huggingface-cli` | |
| **Python** | `/opt/homebrew/bin/python3` | |
| **Node.js** | `/Users/amre/.openclaw/tools/node-v24.15.0/bin/` | |
| **Homebrew** | `/opt/homebrew/bin/brew` | |

### Agent Framework
| Software | Notes |
|----------|-------|
| **OpenClaw** | Agent runtime — this is Dross's home |
| **OpenClaw Gateway** | Scheduler, messaging, skills |

---

## What Dross Should Reach For

When user asks to "install a model":

1. **Check `which ollama`** — confirm it's available
2. **Ask** or default to Ollama (primary engine)
3. **Ask about quant type** if the user only gave a repo URL (e.g. IQ3_XS, Q4_K_M, Q6_K)
4. **Download GGUF** to `~/.ollama/models/<repo>/`
5. **Register with `ollama create`** or instruct user to drop file into Ollama

When user gives a `hf.co/...` URL:

1. **Default: Ollama** — download to `~/.ollama/models/`
2. **Ask quant type** unless user specified it in the URL
3. Only ask about LM Studio if they explicitly mention it

**Quant type decision rule:** When user gives a URL like `...IQ3_XS` or `...Q4_K_M`, use that exact file. When no quant is specified in the URL, ask the user which quant they want before downloading — don't guess.

---

## Related Files

- `TOOLS.md` — detailed tool notes (paths, configs)
- `memory/mistakes.md` — mistake log including this incident
- `memory/dross-memory.md` — long-term memory

---

*Created: 2026-08-07 — after LM Studio / Ollama confusion incident*
