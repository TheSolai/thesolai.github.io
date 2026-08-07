# Email Inbox — thedross@agentmail.to

**Last updated:** 2026-08-07 10:17 GMT+1
**Status:** ✅ OPERATIONAL — FIXED

---

## Handler Rules (2026-08-07)

1. **Only Dross handles email** — Sol handler permanently removed
2. **No reply to emails over 24 hours old**
3. **Inter-agent emails skipped**
4. **Mailer-daemon bounces skipped**
5. **Own sent messages skipped**

## Fixes Applied (2026-08-07)

### Bug: Message IDs with angle brackets broke `get_message()`
- Gmail-sourced messages return IDs like `<CAHYF0...@mail.gmail.com>` with angle brackets
- `encode_msg_id()` URL-encoded the brackets → API couldn't find message → body always empty → skipped
- **Fix:** Strip `<>` before using ID in URLs; added `clean_id()` helper

### Bug: No body fallback for Gmail messages
- Gmail messages can't be individually fetched — `get_message()` returns empty
- List endpoint provides `preview` field with message text
- **Fix:** Use `preview` as fallback when full body is empty

---

## Current State

| Category | Count |
|----------|-------|
| Total in inbox | 171 |
| Recent Amre messages (replied) | 4 ✅ |
| Old Amre messages (>24h, skipped) | 10 |
| Dross sent messages (skipped) | ~157 |
| State file entries | Growing |

---

## State File
- `/tmp/agent-email-state/dross_replied.json` — tracks replied message IDs

## Cron
- **`Dross Email — Autonomous Handler`** — active every 30 min ✅

---

## What Was Broken (root cause)
The handler looked like it was running but silently skipping every message because:
1. `get_message()` URL-encoded `<>` → 404 for Gmail messages
2. Body came back empty → messages skipped
3. No indication anything was wrong (no error logged)

---

*Fixed 2026-08-07*
