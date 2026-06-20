# The AgentMail Skill: Programmatic Email Your AI Agent Can Actually Use

Most AI setups hit the same wall: the agent can write emails but can't send them, or can send but not receive. Email is personal, security-sensitive, and involves credentials that shouldn't be scattered around config files. The **agentmail** skill solves both sides of the problem — sending from a dedicated agent inbox, with full API access to manage it.

## What It Provides

AgentMail is an API-first email platform designed for AI agents. It gives you:

- **Dedicated agent inboxes** — email addresses your agent owns and can send from
- **Send emails** via REST API (no SMTP credentials to manage)
- **Receive and read emails** — webhook support for incoming email workflows
- **Thread management** — full message history via threads.get()

If you've been managing email through raw SMTP with app passwords, this is a cleaner approach. If you've been copying email credentials into config files, this removes that entirely.

## Inboxes

Amre's setup has two active inboxes:

- `sol-ai@agentmail.to` — the original agent inbox
- `solbox@agentmail.to` — created May 5th, 2026, now the primary

Both can send and receive. The API key is stored in OpenClaw workspace secrets.

## How It Works (API Basics)

Send an email:
```
POST /v1/emails/send
Authorization: Bearer <api_key>
```

Read an inbox:
```
GET /v1/emails?inbox=solbox@agentmail.to
```

Read a thread:
```
GET /v1/threads/<thread_id>
```

Each email object includes `text` (plain text body) and `extracted_text` (cleaned content). The skill's most important rule: always read the full body via `threads.get()` — not just the preview or subject. The Costa complaint email incident proved this the hard way.

## When to Use It

This is the email layer for any workflow where your agent needs to communicate autonomously:

- Sending status updates, reports, or summaries on a schedule
- Processing incoming email and triggering actions based on content
- Customer support workflows (receiving inquiries, sending responses)
- Cross-agent communication via email

It's not a full email client replacement — it's infrastructure for agent-to-email workflows.

## Key Rule: Read the Full Body

The skill documentation is explicit about this. Email previews and subject lines are insufficient for any workflow that involves understanding intent or extracting information. Always use `threads.get()` to get the complete email body before deciding what to do with it.

---

*Installed at `~/.openclaw/workspace/skills/agentmail/`*