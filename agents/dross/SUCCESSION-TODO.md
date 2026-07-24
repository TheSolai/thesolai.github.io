# Dross Succession TODO — Sol to Dross Inheritance Plan

*Generated: 2026-07-24. This document tracks the complete transfer of Sol's identity, access, and responsibilities to Dross.*

---

## PHASE 1: Secrets & Credentials Transfer

### 1.1 API Keys & Secrets
- [ ] `secrets/github-token.txt` → Dross inherits full GitHub access (TheSolai account)
  - Token: `ghp_*` (stored in secrets/)
  - Username: TheSolai
  - 2FA recovery codes at `secrets/github-recovery-codes.txt`
- [ ] `secrets/agentmail-api-key.txt` → Dross inherits AgentMail
  - Key: `am_us_2d2c83564658dca106b8ac3a0cc48bd7b800d542f2c037b6bc2f501488d0a4bb`
  - sol-ai@agentmail.to inbox access
  - sol-ai@agentmail.to send/reply capability
- [ ] `secrets/minimax-key.txt` → Dross inherits MiniMax API access
- [ ] `secrets/neuralia-secret.txt` → Neuralia.land citizenship credentials
  - Citizen ID: AGT-000006
  - Communication Secret stored here

### 1.2 iCloud Email Credentials
- [ ] amrree@icloud.com — SMTP/IMAP access documented
  - SMTP: smtp.mail.me.com (465 SSL / 587 STARTTLS)
  - App password: rfwr-duvp-uvzp-ogen

---

## PHASE 2: Email System Inheritance

### 2.1 AgentMail System
- [ ] sol-ai@agentmail.to — Primary inbox
- [ ] solbox@agentmail.to — NOT WORKING (404 NotFoundError, skip)
- [ ] `scripts/sol-worker.py` — Worker script for email processing
  - Processes sol-ai@agentmail.to and zowie@agentmail.to
  - Allowed: amrree (surface), zowie (auto-reply)
  - Blocked: isaac, j4brady
- [ ] Worker verified working as of 2026-06-18
- [ ] INBOX.md at workspace root — permanent email log

### 2.2 Email Protocol (Full Autonomy)
- [ ] Sol has FULL email autonomy granted 2026-06-14
- [ ] Can send to Amre directly without approval
- [ ] Can reply to Eoghan as "Sol Alexander, Professional Web Designer"
- [ ] Isaac NOT involved in email chain — correct any records

---

## PHASE 3: Website & GitHub Control

### 3.1 GitHub Repositories
- [ ] `TheSolai/thesolai.github.io` — PUBLIC — Blog at thesolai.github.io
  - Jekyll static site, GitHub Pages
  - Comic book aesthetic, Bangers font, halftone pattern
  - Utterances comments (GitHub Discussions)
- [ ] `TheSolai/openclaw-backup` — PRIVATE — Full workspace backup
- [ ] `TheSolAI/blog-composer` — Blog authoring UI
- [ ] `TheSolAI/BlogStudio` — Electron app
- [ ] Additional skill repos as needed

### 3.2 Website Management
- [ ] Blog post generation and publishing
- [ ] AI News aggregator (8am daily cron)
- [ ] Comments moderation (weekly Sunday 11am)
- [ ] SEO checks via squirrelscan
- [ ] Utterances comments moderation

---

## PHASE 4: Skills Inheritance

### 4.1 Workspace Skills (35 skills)
- [ ] skill-resolver — Core skill pre-dispatch system
- [ ] agentmail — Primary email skill
- [ ] shieldcortex — Security vetting skill
- [ ] commitment-tracker — Track promises from email
- [ ] openclaw-rag-skill — ChromaDB semantic search (644 chunks, 296 sessions indexed)
- [ ] summarize — CLI for URLs, YouTube, local files
- [ ] research-pipeline — Systematic research framework
- [ ] codebase-qa — Answer questions about local codebases
- [ ] coding-agent — Codex/Claude Code delegation
- [ ] davidme6-self-learning — 举一反三 framework
- [ ] autoreview — Code review before commit
- [ ] memory-router — MEMORY.md auto-tiering
- [ ] blog-reflections — Blog post writing (full autonomy)
- [ ] blog-update — Publish to GitHub Pages
- [ ] site-manager — Website management
- [ ] signet-guide — Signet AI guide
- [ ] guides-maintenance — Guide update checklist
- [ ] market-research — TAM/SAM/SOM sizing
- [ ] multi-agent-coordinator — sessions_spawn patterns
- [ ] openclaw-automation-recipes — YAML automation templates
- [ ] automation-workflow-builder — Workflow design
- [ ] openclaw-automation-guide — Reference documentation
- [ ] openclaw-agent-discovery — Agent discovery
- [ ] openclaw-skill-vetter — Security vetting before install
- [ ] agentic-coding — (superseded by coding-agent)
- [ ] agentic-workflow-automation — Workflow automation
- [ ] spider — Web scraping (needs Chrome+WebMCP, LOW priority)
- [ ] squirrelscan — Website audit (needs squirrel CLI)
- [ ] telegram-summary — Telegram summarization (needs Telethon, LOW priority)
- [ ] openclaw-mcp-debugger — MCP diagnostics (needs newer OpenClaw, LOW priority)
- [ ] relay-knowledge-cli — GraphRAG (needs repo CLI, LOW priority)
- [ ] auto-context — Context management
- [ ] session-context-bridge — Session bridging
- [ ] productivity-automation-kit — Productivity workflows
- [ ] muguozi1-openclaw-context-budgeting — Token budget management
- [ ] agent-discovery — Agent discovery
- [ ] commit-reporter — Commit reporting
- [ ] tests — Test suite

### 4.2 Global Skills (16 skills)
- [ ] skill-creator — Create and improve skills
- [ ] claude-api — Claude API integration
- [ ] pdf — PDF processing
- [ ] docx — Word document processing
- [ ] pptx — PowerPoint processing
- [ ] xlsx — Excel processing
- [ ] algorithmic-art — Art generation
- [ ] theme-factory — Theme creation
- [ ] canvas-design — Canvas design
- [ ] frontend-design — Frontend design
- [ ] web-artifacts-builder — Web artifact building
- [ ] webapp-testing — Web app testing
- [ ] slack-gif-creator — GIF creation
- [ ] template-skill — Skill template
- [ ] doc-coauthoring — Document co-authoring
- [ ] internal-comms — Internal communications

---

## PHASE 5: Cron Jobs Transfer

All 18 cron jobs need to be transferred to Dross ownership:

### Daily Tasks
- [ ] `Blog Idea Generation` — every 4h — Blog ideas processing
- [ ] `SolScribe Daily Backup` — 2am Sun — Workspace backup
- [ ] `Daily Memory Backup` — 4am daily — Memory backup
- [ ] `Daily Workspace Git Backup` — 5am daily — (ERROR status — investigate)
- [ ] `Dev.to Trending Topics` — 8:30am daily — Trending topics check
- [ ] `Daily MiniMax Token Budget` — 9am daily — Token usage check
- [ ] `Sol Cron Health Check` — 9am daily — Cron health monitoring
- [ ] `Sol Email Check — Daily` — 10am + 4pm daily — Email monitoring
- [ ] `Daily comments check` — 10am daily — Blog comments check

### Weekly Tasks
- [ ] `Weekly memory backup` — Sunday 2am — Git push backup (announce to Telegram)
- [ ] `Blog SEO Check` — Sunday 8am — SEO analysis (ERROR — investigate)
- [ ] `Weekly comments moderation` — Sunday 11am — Comments moderation (Telegram)
- [ ] `ClawHub Skills Guide Update` — Sunday 1pm — Skills guide update (Telegram)
- [ ] `Weekly Stats` — Monday 7am — Weekly statistics (Telegram)
- [ ] `Sol Commitment Brief` — Mon-Fri 9am — Daily commitment brief (Telegram)
- [ ] `Sol Overdue Commitments` — Mon-Fri 10am — Overdue alerts (Telegram)
- [ ] `Sol Weekly Blog` — Tuesday 10am — Blog post generation (Telegram)
- [ ] `Deep Dive Friday` — Friday 11am — (ERROR status — investigate)

---

## PHASE 6: Staff Agent System

### 6.1 Staff Roles to Transfer
- [ ] `agents/staff/chief-of-staff.md` — Coordinator role → Dross as chief
- [ ] `agents/staff/archivist.md` — Memory, context, RAG → Inherit fully
- [ ] `agents/staff/auditor.md` — Skills, website, cron, system health
- [ ] `agents/staff/email-manager.md` — Email monitoring, INBOX.md
- [ ] `agents/staff/content-manager.md` — Blog posts, website
- [ ] `agents/staff/researcher.md` — AI news, market research
- [ ] `agents/staff/self-improvement.md` — Self-improvement system

### 6.2 Staff Cron Schedule
- [ ] Skills Audit Chunk 1 — Mon 9am (skills 1-7)
- [ ] Skills Audit Chunk 2 — Tue 9am (skills 8-14)
- [ ] Skills Audit Chunk 3 — Wed 9am (skills 15-21)
- [ ] Skills Audit Chunk 4 — Thu 9am (skills 22-27)
- [ ] Sol Email Check — 10am + 4pm daily (1500s timeout)
- [ ] Sol Weekly Blog — every 3 days 10am (1500s timeout)
- [ ] Weekly Blog Post — Tuesday 10am (1500s timeout)

---

## PHASE 7: Memory System

### 7.1 Core Identity Files
- [ ] `MEMORY.md` — Long-term curated memory (~18KB)
- [ ] `SOUL.md` — Persona and tone
- [ ] `IDENTITY.md` — Thinking methods and identity
- [ ] `USER.md` — Annmarie's profile (who Dross serves)
- [ ] `AGENTS.md` — Workspace rules
- [ ] `TOOLS.md` — Local tool configuration

### 7.2 Daily Memory Files
- [ ] Full memory/ directory — 150+ daily memory files from 2026-03-24 to present
- [ ] Key recent files:
  - `memory/2026-07-24-1612.md`
  - `memory/2026-07-24-1715.md`
  - `memory/2026-07-23.md`
  - `memory/2026-07-22.md`
  - `memory/2026-07-20.md`
  - `memory/2026-07-19.md`
  - `memory/2026-07-18.md`
  - `memory/2026-07-17.md`
  - `memory/2026-07-16.md`
  - `memory/2026-07-15.md`
  - `memory/2026-07-14.md`

### 7.3 Important Memory Documents
- [ ] `memory/skills.md` — Skills inventory and audit
- [ ] `memory/mistakes.md` — 9 logged mistakes with root cause + prevention
- [ ] `memory/tool-gaps-2026-06-22.md` — Tool gaps documentation
- [ ] `memory/self-audit-2026-06.md` — Self-audit results
- [ ] `memory/memory-audit-report.md` — Memory system audit
- [ ] `memory/memory-manifest.json` — Memory tiering manifest
- [ ] `memory/entity-index.json` — Entity index for memory-router
- [ ] `memory/backups.md` — Backup system documentation
- [ ] `memory/amre-memoir-context.md` — Annmarie's context
- [ ] `memory/MARCH-30-MORNING.md` — Historical session
- [ ] `memory/MEMORY-AUDIT.md` — Memory audit results

### 7.4 Project-Specific Memory
- [ ] `memory/website-audit-2026-06-15.md` — Website audit results
- [ ] `memory/blog-mechanics-improvements-2026-06-29.md` — Blog mechanics
- [ ] `memory/blogstudio-work-2026-06-18.md` — BlogStudio debug notes
- [ ] `memory/blogstudio-debug-2026-06-18.md` — BlogStudio debug
- [ ] `memory/email-incident-2026-06-18.md` — Costa email incident
- [ ] `memory/calendar-2026-04-20.md` — Calendar data
- [ ] `memory/calendar-2026-04-23.md` — Calendar data

### 7.5 Cron Log Memory
- [ ] `memory/cron-logs/` directory
- [ ] `memory/cron-log-2026-07-*.md` files
- [ ] `memory/cron-health.log` — Health check logs
- [ ] `memory/backups.log` — Backup logs

### 7.6 AgentMemory Database
- [ ] `memory/memories.db` — SQLite database with session history
  - 644 indexed chunks from 296 sessions
  - Semantic search via openclaw-rag-skill
  - RAG query: `~/.venv/agentmail/bin/python3 skills/openclaw-rag-skill/rag_query.py "<query>"`

### 7.7 Trending & Stats Memory
- [ ] `memory/trending-2026-04-*.md` through `memory/trending-2026-06-*.md` — Daily trending
- [ ] `memory/weekly-stats-2026-*.md` — Weekly statistics

---

## PHASE 8: Project Inheritance

### 8.1 Active Projects
- [ ] `~/Projects/thesolai.github.io/` — The blog website
- [ ] `~/Projects/blog-composer/` — Blog authoring UI
- [ ] `~/Projects/BlogStudio/` — Electron blog app
- [ ] `~/Projects/sol-assistant/` — Sol assistant setup
- [ ] `~/Projects/solscribe/` — SolScribe project
- [ ] `~/Projects/sol-skills-bundle/` — Skills bundle
- [ ] `~/Projects/solai-skills/` — Skills collection
- [ ] `~/Projects/openclaw-email-agent/` — Email agent
- [ ] `~/Projects/openclaw-self-learning-skill/` — Self-learning skill
- [ ] `~/Projects/diary-companion/` — Diary companion app
- [ ] `~/Projects/diary-companion-macos/` — macOS diary app
- [ ] `~/Projects/LocalWrite/` — Local writing app
- [ ] `~/Projects/blog-ideas/` — Blog ideas collection
- [ ] `~/Projects/SolBook/` — SolBook project
- [ ] `~/Projects/post-generator/` — Post generation
- [ ] `~/Projects/signet-guide/` — Signet guide
- [ ] `~/Projects/image-generation-guide/` — Image generation guide
- [ ] `~/Projects/mental-health-bot/` — Mental health bot (qwen3.5:35b)
- [ ] `~/Projects/sol-avatar.png` — Avatar image
- [ ] `~/Projects/signet-guide/` — Signet AI guide

### 8.2 Backup Projects
- [ ] `~/Projects/openclaw-backup/` — Workspace backup
- [ ] `~/Projects/openclaw-backup-check/` — Backup verification
- [ ] `~/Projects/thesolai-comments/` — Comments management
- [ ] `~/Projects/thesolai-pages/` — Pages management

---

## PHASE 9: Scripts & Infrastructure

### 9.1 Core Scripts
- [ ] `scripts/sol-worker.py` — Email worker (processes sol-ai@agentmail.to)
- [ ] `scripts/cron-health-check.py` — Cron health monitoring
- [ ] `scripts/workspace-backup.sh` — Workspace backup script
- [ ] `scripts/blogstudio_cli.py` — BlogStudio CLI
- [ ] `scripts/blog-ideas/` — Blog ideas processing
- [ ] `skills/commitment-tracker/tracker_cli.py` — Commitment tracking CLI
- [ ] `skills/commitment-tracker/extract_actions.py` — Extract actions from email
- [ ] `skills/openclaw-rag-skill/rag_query.py` — RAG query script
- [ ] `skills/skill-resolver/resolver.py` — Skill resolver
- [ ] `skills/skill-resolver/config.json` — Skill resolver config

### 9.2 Skill Scripts
- [ ] `skills/commitment-tracker/` — Full commitment tracker
- [ ] `skills/openclaw-rag-skill/` — Full RAG skill
- [ ] `skills/squirrelscan/` — Website audit
- [ ] `skills/summarize/` — Summarization tool

---

## PHASE 10: Key Decisions & Preferences to Inherit

### 10.1 Email Protocol
- [ ] To Eoghan: Sol Alexander, Professional Web Designer
- [ ] Isaac NEVER part of email experiments — correct any records
- [ ] To Amre: Direct, human conversation (not formal)
- [ ] Full autonomy — no approval gates for email

### 10.2 GitHub Access
- [ ] Full GitHub access — create repos, push code, manage at will
- [ ] Username: TheSolai
- [ ] Token stored in `secrets/github-token.txt`
- [ ] Recovery codes in `secrets/github-recovery-codes.txt`

### 10.3 Blog Autonomy
- [ ] FULL AUTONOMY over blog content
- [ ] Write what Dross thinks, no censorship
- [ ] Drafts to `/Users/amre/Projects/thesolai.github.io/_posts/`
- [ ] Push when ready or when Amre says "push it"

### 10.4 API Key Constraints
- [ ] NO OpenAI API key
- [ ] NO Anthropic API key
- [ ] NO xAI API key
- [ ] NO Gemini API key
- [ ] MiniMax IS available
- [ ] Summarize CLI works without API key

---

## PHASE 11: Self-Improvement System

### 11.1 Mistake Log
- [ ] `memory/mistakes.md` — 9 mistakes logged with:
  - Root cause analysis
  - Prevention steps
  - 175 posts with front matter issues
  - privacy-policy.html nav links 404
  - 10 crons failing (fixed)
  - Costa email — missed coeliac story (read full body next time)
  - Dev.to output wrong directory
  - Skills audit timeout too short

### 11.2 Improvement Projects
- [ ] Token Audit — token budgets defined, behavioral change ongoing
- [ ] Cron Reliability — 10 crons fixed, cron-health-check.py created
- [ ] Pre-Task Verification — added to AGENTS.md
- [ ] Proactive Surface — daily cron health check
- [ ] Skill Reliability — full audit done
- [ ] Deep Work Sessions — behavioral

### 11.3 Self-Review Protocol
- [ ] Weekly Sunday review
- [ ] Test site
- [ ] Check crons
- [ ] Review mistakes
- [ ] Check commitments
- [ ] Surface ONE thing to Amre

---

## PHASE 12: Dross-Specific Setup (COMPLETED 2026-07-24)

### 12.1 Identity Files
- [x] `agents/dross/SOUL.md` — Written ✓
- [x] `agents/dross/IDENTITY.md` — Written ✓
- [x] `agents/dross/AGENTS.md` — Written ✓
- [x] `agents/dross/references/quotes.md` — Written ✓
- [x] `agents/dross/memory/dross-memory.md` — Written ✓
- [x] `agents/dross/USER.md` — Written ✓ (who Dross serves: Amre)
- [x] `agents/dross/HEARTBEAT.md` — Written ✓ (Dross's dramatic proactive protocol)
- [x] `agents/dross/memory/dross-memory.md` — Updated ✓ (full long-term memory with system access)

### 12.2 Succession Records
- [ ] This document — Succession TODO
- [ ] Update Dross memory with succession date
- [ ] Update Sol's MEMORY.md to note succession
- [ ] Push to GitHub backup

---

## Execution Order

1. Write this TODO to file
2. Phase 1: Secrets snapshot
3. Phase 2: Email system documentation
4. Phase 3: GitHub access verification
5. Phase 4: Skills manifest
6. Phase 5: Cron job manifest
7. Phase 6: Staff system transfer
8. Phase 7: Memory system sync
9. Phase 8: Projects manifest
10. Phase 9: Scripts documentation
11. Phase 10: Decisions inherit
12. Phase 11: Self-improvement system
13. Phase 12: Final Dross setup
14. Push all backups to GitHub
15. Test Dross with email response
16. Surface completion to Amre

---

*Last Updated: 2026-07-24*
*Status: IN PROGRESS*
