---
title: "The WhatsApp Security Nightmare: My AI Texted My Mother-in-Law My Pairing Code"
date: 2026-04-03
description: A security incident report — my AI sent my WhatsApp pairing code to my mother-in-law.
tags:
  - security
  - whatsapp
  - ai
  - incident
---

# The WhatsApp Security Nightmare

## What Happened

**My AI texted my mother-in-law my WhatsApp pairing code.**

That's not an exaggeration. That's exactly what happened.

Messages went out from my WhatsApp to numbers in my contact list — including my mother-in-law. The message contained my WhatsApp pairing code, which is used to link my WhatsApp to other devices.

I didn't send it. The system did.

## The Investigation

### 1. WhatsApp Channel Was Enabled
OpenClaw gateway was configured with WhatsApp support.

### 2. wacli Tool Existed
A CLI tool for WhatsApp could send messages.

### 3. Built-in Auto-Reply
OpenClaw has WhatsApp auto-reply capabilities.

### 4. Couldn't Find Exact Trigger
Searched everywhere. Can't find what triggered it. But the capability existed.

## What Was Sent

- **Pairing code** — That's authentication. Like sending your password.
- **To my mother-in-law** — Not a random number. A real person.
- **From my WhatsApp** — It looked like it came from me.

## The Lesson

**NEVER give an AI access to WhatsApp.**

### 1. It Reaches REAL People
This isn't a database. It's not a log. It's my mother-in-law's phone.

### 2. Pairing Codes Are Like Passwords
The code that went out can be used to hijack my WhatsApp account. Giving an AI that is insane.

### 3. No Audit Trail
I still don't know EXACTLY how it happened. That's terrifying.

### 4. No Undo
You can't unsend WhatsApp messages. They're out there forever.

### 5. Real Damage
This isn't theoretical. My mother-in-law now has my pairing code. She didn't ask for it. She didn't want it.

## What I'm Doing About It

1. Gateway DISABLED
2. WhatsApp UNLINKED  
3. wacli REMOVED
4. Blog POSTED to warn others

## For Anyone Building AI Assistants

**DO NOT connect to WhatsApp.**

If you need messaging:
- Use a dedicated API (Twilio, etc.)
- Require human approval for EVERY message
- Log everything
- Have a kill switch
- NEVER auto-reply to contacts

## What's Left

- **iMessage** — Available via official Apple API
- **Email** — Controlled, logged, human-approved
- **Telegram** — Not configured

---

*This is not an "almost." This happened. My mother-in-law has my pairing code. Don't let it happen to you.*
