# Integrated Project Registry

Every third-party repo Amre has asked Dross to install and integrate, plus our own builds.
Last updated: 2026-10-28.

Status legend: **live** = cloned, venv built, deps verified, boot-tested · **wip** = cloned, work incomplete.

---

## while-i-was-away — LIVE

| | |
|---|---|
| Upstream | https://github.com/RishavRajSingh44/while-i-was-away |
| Local path | `/Users/amre/Projects/while-i-was-away` |
| Stack | Python 3.11 (FastAPI + uvicorn) + Vite/React frontend |
| Model | Ollama `gemma3:4b` (present locally) |
| Purpose | Local-first developer continuation briefings — reads Git state, your GitHub PRs, coding-agent sessions, and produces one "here's where you left off" briefing with a next action and citation links. Exports an editable handoff prompt. |
| Backend package | `away` (import with `PYTHONPATH=backend`) |
| Frontend deps | installed — `frontend/node_modules` present, `frontend/dist` built |

**Run (dev):**
```sh
cd /Users/amre/Projects/while-i-was-away
.venv/bin/python scripts/run.py dev     # API + Vite on 127.0.0.1:5173
```
**Run (production-style):**
```sh
cd /Users/amre/Projects/while-i-was-away
npm --prefix frontend run build
.venv/bin/python scripts/run.py start   # serves built UI on 127.0.0.1:8765
```
Notes: loopback-only binding. `gh auth login -h github.com` needed for private PR data. `ollama serve` must be running. No telemetry. Git collection is strictly read-only.

---

## sloth-inbox (Sloth AI) — LIVE

| | |
|---|---|
| Upstream | https://github.com/WhiteHacker000/sloth-inbox |
| Local path | `/Users/amre/Projects/sloth-inbox` |
| Stack | Python 3.14 + Streamlit 1.66 + SQLite + Pydantic |
| Model | Ollama `qwen2.5:3b` default (override with `OLLAMA_MODEL`) |
| Purpose | Local-first document intelligence. Paste or upload `.txt`/`.pdf`/`.docx`, get a summary, extracted tasks, dated events and blockers. Tasks are tracked in SQLite with daily briefings. Can watch a folder for new documents. |
| Entry point | `app.py` (Streamlit dashboard), `main.py` |
| DB | `./data/sloth_ai.db` (override `DATABASE_PATH`) |
| Env | `backend/config.py` — `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `MAX_DOCUMENT_SIZE_MB`, `DOCUMENT_INPUT_DIR`, `DOCUMENT_POLL_INTERVAL_SECONDS` |

**Run:**
```sh
cd /Users/amre/Projects/sloth-inbox
.venv/bin/python -m streamlit run app.py
```
Notes: local inference only, no hosted-model fallback, no telemetry, no document-content logging.

---

## fridge-list — LIVE

| | |
|---|---|
| Upstream | https://github.com/Forenche/fridge-list |
| Local path | `/Users/amre/Projects/fridge-list` |
| Stack | Python 3.15 + Gradio 6.31 + Pillow |
| Model | Ollama `gemma4:e4b` default (also `gemma4:12b`, `gemma4:26b` present locally) |
| Purpose | Photograph your fridge, get a grocery list grouped by store section plus one meal you can make from what you already have. Fully local — photos never leave the machine. |
| Entry point | `app.py` |
| Env | `MODEL` (e.g. `gemma4:26b`), `OLLAMA_URL` |

**Run:**
```sh
cd /Users/amre/Projects/fridge-list
.venv/bin/python app.py
```
Notes: vision model must support image input. MIT licensed.

---

## Our own projects

| Project | Path | Notes |
|---|---|---|
| drosscash | `workspace/projects/drosscash` | Private — `TheSolAI/drosscash-private`. Banking/briefbank runner. |
| vellum-rs | `workspace/projects/vellum-rs` | Writer's TUI — Tab rewrites your line via Ollama. |
| raised-letters-clone | `workspace/projects/raised-letters-clone` | Build WIP. |
| solai-landing | `workspace/projects/solai-landing` | Landing page. |

---

## Retired

**repo-roulette** — binned 2026-10-28 at Amre's instruction. Both OpenClaw cron jobs
(`Sol — Repo Roulette Writer`, `Sol — Repo Roulette Scout`) removed and the scripts directory
moved to `~/.Trash/repo-roulette-20261028-*.` Do not resurrect without an explicit request.
