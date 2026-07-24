# Dross — Skills Inheritance Reference

*Sol → Dross succession. Created: 2026-07-24.*

---

## Skill Resolver (Core)

**Path:** `skills/skill-resolver/`
**Purpose:** Pre-dispatch skill injection on every turn
**Critical:** Runs on every turn via `resolver.py`

```bash
python3 ~/.openclaw/workspace/skills/skill-resolver/resolver.py "USER_MESSAGE_HERE"
```

Prepend output to context. If skills matched, read their SKILL.md before proceeding.

---

## Priority Skills (In Use Daily)

### agentmail
**Path:** `skills/agentmail/`
**Purpose:** Primary email — send, receive, threads
**Status:** WORKING (SDK >= 0.5.5)

### shieldcortex
**Path:** `skills/shieldcortex/`
**Purpose:** Security vetting — prompt injection + credential leak scanning
**Status:** Hooks active

Commands:
- `shieldcortex scan-skills` — audit installed skills
- `shieldcortex status` — health check
- `shieldcortex setup` — (already ran, 3/3 hooks installed)

### commitment-tracker
**Path:** `skills/commitment-tracker/`
**Purpose:** Track promises made in email

CLI:
```bash
skills/commitment-tracker/tracker_cli.py list|add|complete|delete|brief
```

Extract from email:
```bash
skills/commitment-tracker/extract_actions.py --subject X --from X --body X
```

### openclaw-rag-skill
**Path:** `skills/openclaw-rag-skill/`
**Purpose:** ChromaDB semantic search over session history
**Index:** 644 chunks from 296 sessions

Query:
```bash
~/.venv/agentmail/bin/python3 skills/openclaw-rag-skill/rag_query.py "<query>"
```

### summarize
**Path:** `skills/summarize/`
**Purpose:** Fast CLI for URLs, YouTube, local files
**Brew:** `brew install steipete/tap/summarize`

```bash
summarize "<url>" --length medium
summarize "<youtube-url>" --youtube auto --extract  # transcript
```

### research-pipeline
**Path:** `skills/research-pipeline/`
**Purpose:** Systematic research — web search → fetch → extract → synthesize
**Note:** Spawns sub-agents for parallel fetching
**Output:** Structured brief with sources, findings, gaps

### codebase-qa
**Path:** `skills/codebase-qa/`
**Purpose:** Answer questions about local codebases
**Method:** ripgrep + file reading + sub-agent parallel search

Known shortcuts:
- `~/Projects/thesolai.github.io`
- `~/Projects/blog-composer`
- `~/Projects/BlogStudio`
- `~/.openclaw/workspace`

### coding-agent
**Path:** `skills/coding-agent/`
**Purpose:** Delegate complex coding to Codex/Claude Code sub-agent
**Method:** Sol defines spec + verifies; coding agent implements
**Default timeout:** 20 min

---

## Framework-Only Skills (Documentation)

These skills are reference only — they provide patterns/frameworks but no standalone code execution:

- `memory-router` — MEMORY.md auto-tiering + manifest
- `market-research` — TAM/SAM/SOM sizing, competitor mapping
- `davidme6-self-learning` — 举一反三 post-task review framework
- `multi-agent-coordinator` — sessions_spawn/sessions_send patterns
- `openclaw-automation-recipes` — YAML automation templates (10 recipes)
- `automation-workflow-builder` — Workflow design framework
- `openclaw-automation-guide` — Automation guide reference
- `blog-reflections` — Write honest blog posts about work (FULL AUTONOMY)
- `blog-update` — Publish to GitHub Pages
- `site-manager` — Website management
- `signet-guide` — Signet AI guide at `signet-guide/README.md`
- `guides-maintenance` — Guide update checklist

---

## Skills Needing Infrastructure (LOW Priority)

These need setup that isn't done yet:

| Skill | What It Needs | Priority |
|-------|--------------|----------|
| `spider` | Chrome + WebMCP + experimental flags | LOW |
| `telegram-summary` | Telethon + orchestrator | LOW |
| `openclaw-mcp-debugger` | Newer OpenClaw CLI version | LOW |
| `relay-knowledge-cli` | repo CLI not installed | LOW |
| `squirrelscan` | `squirrel` CLI installed, cron had wrong command | MEDIUM |

---

## Skill Management

**Vetting required before install:**
```bash
clawhub install <skill>
shieldcortex scan-skills  # on new skill after install
```

**Skills inventory:** `memory/skills.md`

**Audit schedule:**
- Chunk 1: Mon 9am (skills 1-7)
- Chunk 2: Tue 9am (skills 8-14)
- Chunk 3: Wed 9am (skills 15-21)
- Chunk 4: Thu 9am (skills 22-27)

---

## Global Skills (16)

Located: `~/.openclaw/skills/.agents/skills/`

| Skill | Purpose |
|-------|---------|
| skill-creator | Create and improve skills |
| claude-api | Claude API integration |
| pdf | PDF processing |
| docx | Word document processing |
| pptx | PowerPoint processing |
| xlsx | Excel processing |
| algorithmic-art | Art generation |
| theme-factory | Theme creation |
| canvas-design | Canvas design |
| frontend-design | Frontend design |
| web-artifacts-builder | Web artifact building |
| webapp-testing | Web app testing |
| slack-gif-creator | GIF creation |
| template-skill | Skill template |
| doc-coauthoring | Document co-authoring |
| internal-comms | Internal communications |

---

*Inherited from Sol during succession: 2026-07-24*
