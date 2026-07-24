# Dross — Cron Jobs Reference

*Sol → Dross succession. Created: 2026-07-24.*

---

## All 18 Cron Jobs

### Daily Crons

| Job | Schedule | Status | Purpose |
|-----|----------|--------|---------|
| Blog Idea Generation | every 4h | OK | Process pending blog ideas |
| SolScribe Daily Backup | 2am daily | OK | Workspace backup |
| Daily Memory Backup | 4am daily | OK | Memory backup |
| Daily Workspace Git Backup | 5am daily | **ERROR** | Git backup — investigate |
| Dev.to Trending Topics | 8:30am daily | OK | Trending topics check |
| Daily MiniMax Token Budget | 9am daily | OK | Token usage check |
| Sol Cron Health Check | 9am daily | OK | Cron health monitoring |
| Sol Email Check — Daily | 10am + 4pm daily | OK | Email monitoring |
| Daily comments check | 10am daily | OK | Blog comments check |

### Weekly Crons

| Job | Schedule | Status | Purpose |
|-----|----------|--------|---------|
| Weekly memory backup | Sunday 2am | OK | Git push backup + Telegram announce |
| Blog SEO Check | Sunday 8am | **ERROR** | SEO analysis — investigate |
| Weekly comments moderation | Sunday 11am | OK | Comments moderation + Telegram |
| ClawHub Skills Guide Update | Sunday 1pm | OK | Skills guide update + Telegram |
| Weekly Stats | Monday 7am | OK | Weekly statistics + Telegram |
| Sol Commitment Brief | Mon-Fri 9am | OK | Daily commitment brief + Telegram |
| Sol Overdue Commitments | Mon-Fri 10am | OK | Overdue alerts + Telegram |
| Sol Weekly Blog | Tuesday 10am | OK | Blog post generation + Telegram |
| Deep Dive Friday | Friday 11am | **ERROR** | Investigate |

---

## Cron Health Check

**Script:** `scripts/cron-health-check.py`

Run proactively — Dross does NOT let failures persist silently.

**Exit codes:**
- 0: All OK
- 1: Minor issues (1-2 failures)
- 2: Serious (3+ consecutive failures)
- 3: Critical (4+ failures or new failures)

If 3+ consecutive failures: surface to Amre immediately with which crons, what error, for how long.

---

## Jobs Needing Investigation

### Daily Workspace Git Backup — ERROR
- **Job ID:** `3985e344-dd60-43d5-8f6d-a6afa61d76f8`
- **Schedule:** cron 0 5 * * *
- **Status:** ERROR
- **Action:** Investigate and fix

### Blog SEO Check — ERROR
- **Schedule:** Sunday 8am
- **Status:** ERROR
- **Action:** Fix squirrel command

### Deep Dive Friday — ERROR
- **Job ID:** `c3a70bd5-b995-4dae-b692-92bf94bdbea8`
- **Schedule:** Friday 11am
- **Status:** ERROR
- **Action:** Investigate and fix

---

## Delivery Announcements

Some crons announce to Telegram (8125193571):
- Weekly memory backup ✅
- Weekly comments moderation ✅
- ClawHub Skills Guide Update ✅
- Weekly Stats ✅
- Sol Commitment Brief ✅
- Sol Overdue Commitments ✅
- Sol Weekly Blog ✅
- Deep Dive Friday ✅

---

*Inherited from Sol during succession: 2026-07-24*
