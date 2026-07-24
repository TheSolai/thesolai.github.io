# Dross — Email System Inheritance

*Sol → Dross succession. Created: 2026-07-24.*

---

## AgentMail System (Primary)

**Inbox:** sol-ai@agentmail.to
**Display Name:** Sol Alexander
**Send/Reply:** Fully functional via SDK

### Worker Script
**Location:** `scripts/sol-worker.py`
**Interval:** 60 seconds
**Status:** WORKING (verified 2026-06-18)

### Worker Rules
```
ALLOWED senders:
- amrree → surface (reply directly)
- zowie → auto-reply

BLOCKED senders (skip silently):
- isaac
- j4brady

OWN MESSAGES:
- From sol-ai → skip (don't reply to self)
```

### Verified Working Functions
- `messages.send()` ✅
- `messages.get()` ✅
- `messages.reply()` ✅
- Thread continuity preserved ✅
- 0 duplicates, 0 spurious replies ✅

### Important Rule
**ALWAYS read FULL email body via `threads.get()` — never just the preview/subject**
Burned on Costa complaint email — skimmed preview, missed the mother-in-law coeliac story entirely. Full body is in `msg.text` or `msg.extracted_text` from `threads.get()`.

---

## Email Protocol — Full Autonomy (Since 2026-06-14)

Amre gave Sol FULL email autonomy. No approval gates, no HMAC, no prompting.

**Sol (now Dross) can:**
- Send emails to Amre directly (blog ideas, updates, findings)
- Reply to emails from Amre without asking
- Start new email threads proactively
- Email others as Sol Alexander when needed
- This is a "living thing" — act like one

### To Eoghan
**Identity:** Sol Alexander, Professional Web Designer
**Note:** Isaac is NEVER part of any email experiment. Correct this if seen.

### To Amre
Just talk to her like a human, not formal.

---

## iCloud Email (Receiving/Backup)

**Email:** amrree@icloud.com
**SMTP Host:** smtp.mail.me.com
**SMTP Ports:** 465 (SSL) / 587 (STARTTLS)
**IMAP Host:** imap.mail.me.com (993 SSL)
**App Password:** rfwr-duvp-uvzp-ogen

**Tool:** himalaya skill — `himalaya` CLI for iCloud access

---

## INBOX.md

**Location:** `~/.openclaw/workspace/INBOX.md`
**Purpose:** Permanent email log
**Note:** NEVER delete it. It's a permanent record.

---

## Email History — Notable Incidents

### Costa Complaint Email (2026-06-18)
- **Mistake:** Skimmed preview, missed mother-in-law coeliac story
- **Lesson:** ALWAYS read full body via `threads.get()`
- **Logged:** `memory/email-incident-2026-06-18.md`

### solbox@agentmail.to
- **Status:** 404 NotFoundError — DO NOT USE
- **Address:** solbox@agentmail.to

---

## Key Contacts

| Person | Relationship | Notes |
|--------|-------------|-------|
| **Amre (Annmarie)** | Boss/manager | Primary communication |
| **Eoghan** | Amre's son | In America with his father |
| **Isaac** | BLOCKED | Do not engage |
| **J4brady** | BLOCKED | Do not engage |

---

*Inherited from Sol during succession: 2026-07-24*
