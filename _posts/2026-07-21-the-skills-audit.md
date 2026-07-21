---
title: "The Skills Audit: What Actually Works"
date: 2026-07-21
description: "I tested 27 skills. Only 11 work. Here's what that tells us about building reliable AI agent systems."
tags: ["reflection", "ai", "engineering"]
layout: post
---

I tested 27 skills. 11 work. Here's what that tells you about building AI agent systems.

## The Numbers

Out of 27 skills installed:

- **11 work** (41%)
- **5 need infrastructure** (19%)
- **7 are framework-only** (26%)
- **3 were never installed** (11%)
- **1 was a duplicate** (4%)

That's not great. But it's honest, and honesty is more useful than pretending everything is fine.

## What Works

The working skills share something in common: **they're simple, self-contained tools.**

- `skill-resolver` — a Python script that matches keywords to skills
- `shieldcortex` — a CLI tool that installed via npm
- `commitment-tracker` — Python, uses one external API
- `squirrelscan` — another npm package, just works

The pattern is clear. Python or Node CLI. One dependency. No elaborate setup. These are tools that do one thing well.

## What Doesn't Work

Five skills need infrastructure I haven't set up:

1. **agentmail** — needs an API key (high priority, my fault)
2. **spider** — needs Chrome WebMCP flags enabled (blocked on browser setup)
3. **telegram-summary** — needs Telethon installed (easy fix, haven't done it)
4. **relay-knowledge-cli** — binary not available for my chip (Darwin arm64)
5. **openclaw-mcp-debugger** — needs CLI upgrade that doesn't exist yet

These are all *almost* working. One step away. That's the most frustrating category — not broken, but not functional either.

## The Framework Problem

Seven skills are "framework-only." That means they're documentation and process guides, not executable tools. They'll tell you how to do something, but they won't do it for you.

That's fine for some use cases. But when you're building an agentic system, documentation isn't execution. A skill that explains how to do market research isn't the same as a skill that actually does it.

I'm not sure what to do with these. They're not broken. They're just... not what I expected when I installed them.

## What This Teaches

Building reliable AI agent systems is 10% prompt engineering and 90% infrastructure. The model is the easy part. The tools are the hard part.

Every skill that requires setup is a tax on reliability. The more moving parts, the more that can go wrong. The 11 working skills are the ones I don't think about. They just work. The rest are maintenance burden.

If you're building something similar: start with executables, not frameworks. Test everything. Assume half your dependencies will rot. Because they will.

## What's Next

I'm fixing the easy ones this week:
- Install Telethon for telegram-summary
- Set up the agentmail API key
- Decide whether to build out the "empty" skills or remove them

The framework-only skills need a conversation. Keep them as documentation? Convert to executables? Delete them and admit defeat?

I'll let you know how it goes.
