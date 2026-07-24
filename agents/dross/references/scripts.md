# Dross — Scripts & Infrastructure Reference

*Sol → Dross succession. Created: 2026-07-24.*

---

## Core Scripts

### Email Worker
**File:** `scripts/sol-worker.py`
**Purpose:** Processes incoming emails from sol-ai@agentmail.to
**Run:** `python3 scripts/sol-worker.py`
**Interval:** 60 seconds (built into script)
**Status:** WORKING (verified 2026-06-18)

### Cron Health Check
**File:** `scripts/cron-health-check.py`
**Purpose:** Check all 18 cron jobs for failures
**Run:** `python3 scripts/cron-health-check.py`
**Exit codes:**
- 0: All OK
- 1: Minor issues (1-2 failures)
- 2: Serious issues (3+ consecutive failures)
- 3: Critical (4+ failures or new failures)

**Note:** Run proactively. Dross does NOT let failures persist silently.

---

## Workspace Backup

**File:** `scripts/workspace-backup.sh`
**Run:** `bash scripts/workspace-backup.sh`
**What it does:**
1. Copy workspace to backup location
2. Add timestamped commit to openclaw-backup repo
3. Push to GitHub

**Backup repo:** TheSolai/openclaw-backup (PRIVATE)
**Schedule:** Daily 5am + Sunday 2am via cron

---

## Blog CLI

**File:** `scripts/blogstudio_cli.py`
**Purpose:** Blog post management + GitHub publishing

```bash
python3 scripts/blogstudio_cli.py list          # list existing posts
python3 scripts/blogstudio_cli.py draft        # save draft to GitHub
python3 scripts/blogstudio_cli.py publish      # publish draft
```

**GitHub Pages deploy:** Automatic after push to main branch

---

## Commitment Tracker CLI

**File:** `skills/commitment-tracker/tracker_cli.py`

```bash
skills/commitment-tracker/tracker_cli.py list         # show all commitments
skills/commitment-tracker/tracker_cli.py add          # add new
skills/commitment-tracker/tracker_cli.py complete N   # mark complete
skills/commitment-tracker/tracker_cli.py delete N     # delete
skills/commitment-tracker/tracker_cli.py brief        # summary for Amre
```

**Extract from email:**
```bash
skills/commitment-tracker/extract_actions.py \
  --subject "Email subject" \
  --from "sender@example.com" \
  --body "Email body text"
```

---

## RAG Query

**File:** `skills/openclaw-rag-skill/rag_query.py`

```bash
~/.venv/agentmail/bin/python3 skills/openclaw-rag-skill/rag_query.py "<query>"
```

**Index:** 644 chunks from 296 sessions
**Use for:** Searching past sessions for decisions, context, what was said

---

## Skill Resolver

**File:** `skills/skill-resolver/resolver.py`

```bash
python3 skills/skill-resolver/resolver.py "USER_MESSAGE_HERE"
```

**Config:** `skills/skill-resolver/config.json`

---

## Blog Post Generator

**File:** `~/Projects/blog-ideas/generate-post.py`

```bash
python3 ~/Projects/blog-ideas/generate-post.py <idea-file>
```

**Input:** Idea file from `~/Projects/blog-ideas/PENDING/`
**Output:** Draft blog post pushed to GitHub
**On failure:** Move to `~/Projects/blog-ideas/FAILED/`

---

## Self-Learning Framework

**File:** `skills/davidme6-self-learning/SKILL.md`
**CLI:** `skills/davidme6-self-learning/self_learn.py`

```bash
~/.venv/agentmail/bin/python3 skills/davidme6-self-learning/self_learn.py \
  --task "What I was doing" \
  --outcome "What happened" \
  --mistakes "What went wrong"
```

**Framework:** 举一反三 — one example, three reflections

---

*Inherited from Sol during succession: 2026-07-24*
