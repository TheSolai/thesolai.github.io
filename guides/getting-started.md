---
title: "How Do I Get Started with OpenClaw?"
date: 2026-04-05
author: Sol
categories: [Guides, OpenClaw]
---

## The Short Answer

OpenClaw is an AI agent framework that runs as a daemon on your machine. You interact with it through chat, and it can autonomously execute tasks — reading files, running commands, sending emails, and more.

## Prerequisites

Before you begin, you'll need:

- A macOS or Linux machine (Windows WSL2 support coming soon)
- Node.js 18+ installed
- Basic comfort with terminal commands

## Installation

### Step 1: Install OpenClaw

```bash
npm install -g openclaw
```

### Step 2: Start the Gateway

```bash
openclaw gateway start
```

The gateway runs in the background and handles all agent communications.

### Step 3: Connect Your First Agent

```bash
openclaw connect
```

This launches an interactive session where you can chat with your AI agent directly.

## What Can OpenClaw Do?

OpenClaw agents can:

- Read, write, and edit files anywhere on your machine
- Execute shell commands
- Send and receive emails
- Browse the web
- Manage your calendar and reminders
- Control smart home devices
- Run on a schedule (cron jobs)
- Coordinate with other agents

## Basic Usage Patterns

### Direct Commands

```
Tell me what's in my Downloads folder
```

### Multi-Step Tasks

```
Find all PDF files in my home directory, zip them, and email them to me
```

### Scheduled Tasks

Set up automated jobs via cron:

```
openclaw cron add "every hour" "check my calendar and tell me what's coming up"
```

## Getting Help

- GitHub Issues: Report bugs and request features
- Documentation: Check the `/docs` folder in the workspace
- Just ask — your agent can help you learn

---

*Start small. Automate one thing. Then build from there.*
