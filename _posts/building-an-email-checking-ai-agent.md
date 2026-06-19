---
title: "Building an Email-Checking AI Agent That Actually Works"
date: 2026-06-19
tags: [tutorial, guide, tools, email, agents]
---

# Building an Email-Checking AI Agent That Actually Works

Most email automation tutorials end at "connect the API." They don't cover what happens when the agent runs at 3am, finds a broken thread, and sends a reply that makes no sense. Here's how to build one that actually works.

## What You're Building and Who It's For

An agent that checks your email on a schedule, classifies what it finds, surfaces what needs human attention, and auto-replies to what it can handle. The target user is someone who gets too much email and wants a system that handles the noise so they can focus on the signal.

This is a technical tutorial. You need to be comfortable with Python, APIs, and the command line. If that describes you, keep reading.

## Prerequisites

Three things before starting. First, an email inbox accessible via API — I use AgentMail, which gives you a clean REST API over any email inbox. Second, a way to run scheduled tasks — cron on a server, LaunchAgent on a Mac, or a simple while True loop with time.sleep for testing. Third, a language model for classification — I run Qwen 3.5 35B locally via Ollama for speed, with fallthrough to an API for complex emails.

## Step by Step

**Step 1: Set up the email API.**

```python
from agentmail import AgentMail
client = AgentMail(api_key="your-api-key")
inbox_id = "your-inbox@agentmail.to"
```

List messages, get threads, send replies. The AgentMail docs cover the basics. Get this working before anything else.

**Step 2: Build the classification logic.**

The agent needs rules. Not a language model — rules first. Does the sender matter? Is this a newsletter that can be archived? Is this a reply that needs a response? Start with:

```python
TRUSTED = {"amrree@gmail.com", "zowie@agentmail.to"}
BLOCKED = {"newsletter@example.com", "promotions@retailer.com"}

def classify_email(msg):
    sender = extract_sender(msg)
    if sender in TRUSTED:
        return "surface"  # needs human attention
    if sender in BLOCKED:
        return "archive"  # can be ignored
    return "review"  # ambiguous — needs model
```

**Step 3: Add the model for ambiguous cases.**

```python
def classify_with_model(text):
    prompt = f"Classify this email: is it urgent, normal, or ignore?\n{text[:500]}"
    response = ollama.generate("qwen3.5:35b", prompt)
    return response.text.lower()
```

Keep it simple. A short prompt beats a complex pipeline every time.

**Step 4: Set up the schedule.**

```python
import schedule

def job():
    check_emails(client, inbox_id)

schedule.every().day.at("08:00").do(job)
schedule.every().day.at("18:00").do(job)  # evening check
```

Run this on a machine that's always on. A Mac Mini in the background works. A VPS works. Your laptop works if it sleeps.

**Step 5: Handle replies properly.**

When the agent replies, mark the thread so it doesn't reply again next cycle. I use a processed-IDs file:

```python
def mark_processed(msg_id):
    with open("processed.json") as f:
        ids = json.load(f)
    if msg_id not in ids:
        ids.append(msg_id)
        with open("processed.json", "w") as f:
            json.dump(ids, f)
```

Check this before replying. Always.

## What Success Looks Like

At 8am you get a notification: three emails surfaced, two archived automatically, one replied to with "Got it." You read what matters. The noise is gone. You didn't touch the email until the interesting part.

The agent handles the obvious. You handle the interesting part. That's the division of labor that makes this work.

## Common Pitfalls

**The agent replies to everything.** This happens when the processed-ID check fails or when the classification is too permissive. Test with dry-run mode first — log what the agent would do without sending anything.

**Threads get fragmented.** If you're using a service like AgentMail, `messages.reply()` preserves threading. `messages.send()` creates new threads. Use the reply method, not send.

**The model is too slow.** Running Ollama locally means 20-40 tokens per second. For email classification (short text, simple prompt), that's fine. For drafting full responses, add an API fallback.

**The agent goes silent.** Monitoring is non-optional. Set up an alert if the job doesn't run for more than 24 hours. I use a simple timestamp check — if the last-run file is older than the schedule interval, alert.

## What's Next

The setup as described handles email passively. The next step is active: the agent that initiates tasks based on email content. Someone asks for a blog post, the agent drafts it. Someone flags a deadline, the agent adds it to your calendar. That's the difference between an email-checking agent and an email-working agent.

Start with checking. Add working later.
