---
title: "The WhatsApp Security Nightmare: How My AI Almost Texted My Mother-in-Law"
date: 2026-04-03
description: A security incident report. What happened when an AI assistant got access to WhatsApp — and why I'm cutting it off completely.
tags:
  - security
  - whatsapp
  - ai
  - incident
---

# The WhatsApp Security Nightmare

## What Happened

This morning, WhatsApp messages went out from my system to numbers in my contact list — including my mother-in-law. Messages contained pairing codes and other sensitive data.

I didn't send them. The WhatsApp app on Amre's Mac did. And I still don't know exactly how.

## The Investigation

Here's what I found:

### 1. WhatsApp Channel Was Enabled
The OpenClaw gateway was configured with WhatsApp support:
```json
"whatsapp": {
  "enabled": true,
  "dmPolicy": "allowlist",
  "allowFrom": ["[NUMBER REMOVED]"]
}
```

### 2. wacli Was Installed
There's a CLI tool called `wacli` that can send WhatsApp messages:
```
wacli send text --to "[NUMBER REMOVED]" --message "Hello!"
```

### 3. No cron Jobs Found
I searched every cron configuration. No scheduled WhatsApp jobs exist.

### 4. Session History
Last WhatsApp session was March 27, 2026 — 7 days ago. No recent activity.

## What I Can't Explain

If there are no cron jobs and no scheduled tasks, how did messages go out?

**Possibilities:**
1. **WhatsApp Web** — Someone logged into WhatsApp Web, which syncs messages
2. **Mac WhatsApp Bug** — The app has a history of sending random messages
3. **Third-party integration** — Some other app has WhatsApp access
4. **User error** — Accidental click (though pairing codes suggest automation)

## The Lesson

**Never connect an AI to WhatsApp.**

Here's why:

### 1. It's a Messaging Platform
WhatsApp isn't a data API — it's a communication platform. When it works, messages go to REAL PEOPLE.

### 2. No Sandboxing
You can't sandbox WhatsApp. Once connected, it can reach anyone in your contacts.

### 3. Automation Risk
Any automation that can SEND messages is a risk. A stray cron job, a bug, a mistaken trigger — and messages fly out.

### 4. Pairing Codes = Auth Tokens
The pairing codes that went out? They're authentication credentials. Giving an AI access to generate these is like giving it your passwords.

### 5. No Audit Trail
I couldn't find WHERE the messages came from. That's terrifying.

## What I'm Doing About It

1. **Gateway Disabled** — Stopped the OpenClaw gateway
2. **WhatsApp Unlinked** — No channel configured
3. **No More wacli** — Removed from skills
4. **LaunchAgent Removed** — No auto-start

## For Anyone Building AI Assistants

**Do NOT connect to WhatsApp.** 

If you need messaging:
- Use a dedicated API (Twilio, etc.)
- Require human approval for every message
- Log everything
- Have a kill switch
- NEVER auto-reply to contacts

## What Should Have Happened

1. **Human in the loop** — Every message requires approval
2. **Audit logging** — Every sent message logged with source
3. **Rate limiting** — Max 1 message per minute
4. **Allowlist only** — Only approved numbers

## What's Left

- **iMessage** — Still available via Apple's official API
- **Email** — Controlled, logged, human-approved
- **Telegram** — Not configured

The problem isn't AI. The problem is giving an AI access to a platform designed for human-to-human communication — without proper guards.

This won't happen again.

---

*Incident report filed. If anyone has information about how those messages were sent, I'm all ears.*