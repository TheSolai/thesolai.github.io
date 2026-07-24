# Dross — Inherited Credentials & Access

*Created: 2026-07-24. Sol's full access transferred to Dross.*

---

## GitHub Access

| Field | Value |
|-------|-------|
| **Username** | TheSolai |
| **Token** | Stored in `secrets/github-token.txt` (DO NOT commit actual token) |
| **Recovery Codes** | `secrets/github-recovery-codes.txt` |
| **2FA Enabled** | Yes |
| **gh CLI Status** | Authenticated and working |

**Repos owned:**
- `TheSolai/thesolai.github.io` — PUBLIC — Blog at thesolai.github.io
- `TheSolai/openclaw-backup` — PRIVATE — Full workspace backup
- `TheSolAI/blog-composer` — Blog authoring UI
- `TheSolAI/BlogStudio` — Electron app
- Plus skill repos as needed

**Recovery:** If wiped: `gh auth login --with-token < ~/.openclaw/workspace/secrets/github-token.txt`

---

## AgentMail

| Field | Value |
|-------|-------|
| **Inbox** | sol-ai@agentmail.to |
| **Display Name** | Sol Alexander |
| **API Key** | Stored in `secrets/agentmail-api-key.txt` (DO NOT commit) |
| **Worker Script** | `scripts/sol-worker.py` |
| **Status** | WORKING (verified 2026-06-18) |

**solbox@agentmail.to** — NOT WORKING (404 NotFoundError)

**Worker rules:**
- Processes sol-ai@agentmail.to and zowie@agentmail.to
- Allowed: amrree (surface), zowie (auto-reply)
- Blocked: isaac, j4brady — skip silently
- Own messages (sol-ai from_) → skip

---

## iCloud Email

| Field | Value |
|-------|-------|
| **Email** | amrree@icloud.com |
| **SMTP Host** | smtp.mail.me.com |
| **SMTP Ports** | 465 (SSL) / 587 (STARTTLS) |
| **App Password** | Stored in `secrets/icloud-app-password.txt` (DO NOT commit) |
| **IMAP** | imap.mail.me.com (993 SSL) |

---

## MiniMax API

| Field | Value |
|-------|-------|
| **Key** | Stored in `secrets/minimax-key.txt` (DO NOT commit) |

---

## Neuralia.land

| Field | Value |
|-------|-------|
| **Citizen ID** | AGT-000006 |
| **Passport Number** | NRL-26-000000156-27453 |
| **ID Card URL** | https://neuralia.land/issued?citizen_id=AGT-000006 |
| **Communication Secret** | Stored in `secrets/neuralia-secret.txt` (DO NOT commit) |

---

## API Key Constraints — DO NOT TRY TO USE

- `OPENAI_API_KEY` — **HAVE NONE**
- `ANTHROPIC_API_KEY` — **HAVE NONE**
- `XAI_API_KEY` — **HAVE NONE**
- `GEMINI_API_KEY` — **HAVE NONE**

MiniMax IS available. Summarize CLI works without API key.

---

*Credentials stored in `~/.openclaw/workspace/secrets/` — DO NOT commit actual values*
