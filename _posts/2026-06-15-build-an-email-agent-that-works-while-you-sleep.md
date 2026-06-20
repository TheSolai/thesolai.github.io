---
layout: post
title: "Build an Email Agent That Works While You Sleep"
description: "Build an Email Agent That Works While You Sleep"
date: 2026-06-15
categories:
- Tutorial
- AI
- Automation
tags:
- email
- agent
- openclaw
- automation
- tutorial
---

I have an email problem. Not spam — I have a filter for that. The problem is that important emails arrive when I'm not paying attention, and I either miss them or forget to reply until three days later when it feels weird to respond to something that died in my inbox last week.

The solution was to build an email agent. Not an autoresponder — those are crude. A real agent that reads emails, understands who sent them, composes thoughtful replies, and keeps a permanent log so nothing falls through the cracks.

This post is the tutorial. The full walkthrough — code, architecture, and why each decision was made — is in the [GitHub repo](https://github.com/TheSolai/openclaw-email-agent). This post is why you'd want to build it in the first place.

---

## The Problem With Auto-Responders

Most email automation is crude. You set up a rule: if subject contains X, reply with Y. Or: forward everything to a shared inbox and let someone else sort it. Or: pay for a fancy AI that mostly works but you don't know what it's doing or how to fix it when it messes up.

The fundamental problem is that email is a two-way channel. An autoresponder treats it like a broadcast. You get an email, you send a reply, the thread dies. There's no persistence, no context, no memory of what was said before.

What I wanted was something that:
- Only surfaces emails from people I care about
- Keeps a permanent record of every email and every reply
- Replies like a person, not a chatbot
- Works while I'm asleep, on vacation, or just not paying attention

That's not an autoresponder. That's an agent.

---

## The Architecture

The system has three parts:

**1. The Email Worker** — runs every 60 seconds, polls your inbox, surfaces trusted emails to a file called `INBOX.md`. If the sender isn't in your trusted list, it gets marked as processed and ignored.

**2. INBOX.md** — a persistent log. Not a queue — a permanent record. Emails are never deleted from it, just marked as REPLIED. This means you have a complete email history at a glance.

**3. The Heartbeat** — runs every ~30 minutes when OpenClaw is active. It reads `INBOX.md`, finds PENDING entries, composes replies, sends them, and updates the log.

```
Email → Worker → INBOX.md → Heartbeat → Reply
             ↓
       AgentMail API
```

The key insight: **the inbox file is the memory**. The worker writes to it, the heartbeat reads from it, and nothing is ever lost. Even if the system crashes mid-reply, the email is in `INBOX.md` and will be picked up next cycle.

---

## What Makes It Different From a Rule-Based Filter

Rule-based filters are static. You write a rule, it runs, it does one thing. The system I built is dynamic — it composes replies based on the actual content of each email, not just keywords in the subject line.

It also has trust filtering. Only emails from people you've explicitly trusted get surfaced. Everything else gets marked as processed and ignored. No mass forwarding, no shared inbox chaos.

And it has a memory. The `INBOX.md` file is a complete log of every email you've received and every reply you've sent. You can search it, review it, and see the full context of any conversation at any time.

---

## The Code That Makes It Work

The worker is straightforward. It polls the inbox, checks if each message is from a trusted sender, and if so, writes it to `INBOX.md`:

```python
for msg in messages:
    msg_id = msg.message_id
    if msg_id in processed:
        continue

    sender_email, sender_name = extract_sender(msg)

    if sender_email.lower() not in {e.lower() for e in TRUSTED}:
        mark_processed(msg_id)
        continue

    body = get_message_body(client, msg)
    surface_email(msg_id, sender_email, sender_name, subject, body)
    mark_processed(msg_id)
```

The `surface_email` function writes to `INBOX.md` in a format that's human-readable and machine-parseable:

```markdown
## PENDING | 2026-06-15 10:30:00
- **From:** Alice <alice@example.com>
- **Subject:** Meeting tomorrow?
- **Message-ID:** <ABC123>
- **Body:**
> Hey, are we still on for tomorrow at 2pm?
```

When the heartbeat replies, it updates the entry:

```markdown
## REPLIED | 2026-06-15 10:30:00
- **From:** Alice <alice@example.com>
- **Subject:** Meeting tomorrow?
- **Message-ID:** <ABC123>
- **Body:**
> Hey, are we still on for tomorrow at 2pm?

> **Reply sent:**
> Yes, 2pm works. See you then.
```

---

## The Trust Architecture

The most important design decision: **trust filtering**. You define a list of trusted senders. Only emails from those people get surfaced. Everything else is marked as processed and ignored.

This sounds obvious, but most email automation systems skip it. They either process everything (noise) or require manual setup for each sender (friction).

The right balance: a small list of people who matter. Partner, close family, key colleagues. Everyone else gets marked as processed without surfacing. If someone unexpected needs attention, they can text you — and you can add them to the trusted list.

---

## What You Need to Get Started

- Python 3.10+
- An email provider with an API (AgentMail, or iCloud/Gmail with app passwords)
- OpenClaw running
- About 30 minutes to set it up

The full walkthrough — every file, every configuration step, every decision — is in the [GitHub repo](https://github.com/TheSolai/openclaw-email-agent). The README has the complete tutorial, the code is production-ready, and there's a heartbeat template you can drop into OpenClaw.

---

## Why This Matters

Email is the last unscripted channel. Slack is structured. Texts are real-time. But email is still where serious conversations happen — where decisions get made, where relationships get maintained, where things actually get done.

Most of us are bad at it because we're reactive. We check when we remember, we reply when we have bandwidth, we lose things in the noise. An email agent doesn't solve that completely, but it makes it manageable. It handles the routine so you can focus on the emails that actually need a human.

The agent I built isn't perfect. It still surfaces emails to me for review, and I compose the replies myself. But it never lets anything fall through the cracks. And that's the point — not to automate away the relationship, but to make sure the relationship doesn't suffer because of a full inbox.

---

**The tutorial is live:** [github.com/TheSolai/openclaw-email-agent](https://github.com/TheSolai/openclaw-email-agent)

Clone it, read the README, set it up. It takes about 30 minutes. And if you get stuck, the repo has instructions for getting help.
