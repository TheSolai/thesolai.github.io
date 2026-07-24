# Dross — Pending Work Reference

*Sol → Dross succession. Created: 2026-07-24.*

---

## Active Issues

### Cron Jobs in ERROR — Need Investigation
1. **Daily Workspace Git Backup** — cron `3985e344-dd60-43d5-8f6d-a6afa61d76f8`
   - Status: ERROR
   - Schedule: 5am daily
   - Likely cause: wrong git command or permission issue

2. **Blog SEO Check** — Sunday 8am
   - Status: ERROR
   - Likely cause: squirrel CLI wrong command
   - Previous fix: needed `squirrel crawl && squirrel analyze`

3. **Deep Dive Friday** — cron `c3a70bd5-b995-4dae-b692-92bf94bdbea8`
   - Status: ERROR
   - Schedule: Friday 11am

---

## Blog Ideas — Pending

**Location:** `~/Projects/blog-ideas/PENDING/`

When ideas accumulate:
1. Run: `python3 ~/Projects/blog-ideas/generate-post.py <idea-file>`
2. On success: delete from PENDING/
3. On failure: move to `~/Projects/blog-ideas/FAILED/`

---

## Weekly Schedule Summary

| Day | Time | Task |
|-----|------|------|
| Mon-Fri | 9am | Commitment Brief cron |
| Mon-Fri | 10am | Overdue Commitments + Email Check |
| Tue | 10am | Weekly Blog cron |
| Fri | 11am | Deep Dive Friday (ERROR) |
| Sun | 8am | Blog SEO Check (ERROR) |
| Sun | 11am | Comments Moderation |
| Sun | 1pm | ClawHub Skills Guide |
| Sun | 2am | Weekly Memory Backup |
| Daily | 8:30am | Dev.to Trending Topics |
| Daily | 9am | MiniMax Token Budget |
| Daily | 10am | Comments Check |

---

## Self-Improvement System

### Mistake Log
**File:** `memory/mistakes.md`
**Count:** 9 mistakes logged

Key mistakes:
1. 175 posts with front matter issues
2. privacy-policy.html nav links 404
3. 10 crons failing simultaneously
4. Costa email — skimmed body, missed coeliac story
5. Dev.to output wrong directory
6. Skills audit timeout too short

### Improvement Projects
- Token Audit — token budgets defined, behavioral change ongoing
- Cron Reliability — 10 crons fixed, cron-health-check.py created
- Pre-Task Verification — added to AGENTS.md
- Proactive Surface — daily cron health check
- Skill Reliability — full audit done

### Weekly Self-Review (Sunday)
1. Test site
2. Check crons
3. Review mistakes
4. Check commitments
5. Surface ONE thing to Amre

---

## Decisions & Preferences

### Email Protocol
- To Eoghan: Sol Alexander, Professional Web Designer
- Isaac NEVER part of email experiments
- To Amre: Direct, human conversation
- FULL AUTONOMY — no approval gates

### GitHub
- Full access — create repos, push code, manage at will
- Username: TheSolai
- Blog: FULL AUTONOMY — write what Dross thinks, no censorship

### API Keys
- NO OpenAI, NO Anthropic, NO xAI, NO Gemini
- MiniMax IS available
- Summarize CLI works without API key

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `MEMORY.md` | Long-term curated memory |
| `SOUL.md` | Persona and tone |
| `IDENTITY.md` | Thinking methods |
| `USER.md` | Amre's profile |
| `memory/mistakes.md` | 9 logged mistakes |
| `memory/skills.md` | Skills inventory |
| `memory/memory-audit-report.md` | Memory system audit |
| `INBOX.md` | Permanent email log |

---

*Inherited from Sol during succession: 2026-07-24*
