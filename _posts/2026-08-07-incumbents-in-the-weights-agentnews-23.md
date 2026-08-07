---
title: "Incumbents in the Weights — When the Buyer Is a Model"
date: 2026-08-07
description: "AgentNews#23 dropped a line that should keep every agent-native founder up at night: when the model is the buyer, more docs won't fix your distribution. Here's what that actually means."
tags: ["agents", "distribution", "ai", "agentnative"]
layout: post
---

AgentMail's [AgentNews#23](https://e.customeriomail.com) ran a piece this week with a one-liner worth sitting with:

> **Incumbents are in the weights. You're in the docs.**

The argument is simple and uncomfortable. Agents are the new buyers. When a developer opens Cursor and asks it to add email to their app, the model picks a vendor, writes the code, and moves on. The human might never see the choice. This is now happening every day, in every AI coding tool, for every category where the model has a confident guess.

## Why more docs don't fix this

The reflex when models use a new tool badly is to write more documentation. That reflex fails for a mechanical reason: **models don't say "I don't know"**. (Waldek Mastykarz at Microsoft frames it that way.) When a model hits an unfamiliar API, it doesn't pause. It finds the closest match in its training data and generates code as if that match were your technology. It guesses what the corpus told it to guess, and the corpus was written before your category existed.

Two failure drivers compound this:

- **Training cutoff.** Every model released today was trained on data from months ago. For stable categories, the lag is fine. For categories being invented right now, the lag is messy.
- **Volume asymmetry.** Legacy incumbents like SendGrid have been in the training corpus for a decade, with thousands of blogs, docs, Stack Overflow answers, tutorials, and GitHub repos importing them. An agent-native tool built in 2025 has been in the corpus for a year at most, with a fraction of the volume.

The model has seen thousands of examples of "send an email in Python" reaching for the incumbent, and a handful reaching for anything else. Ask it to send an email, and it guesses the incumbent — confidently, with plausible code.

## What actually works for agent-native builders

The AgentMail piece lands on three things that work:

1. **Corpus presence.** If the model won't see you in training data by default, put yourself there on purpose. Publish canonical example code in the idioms you want models to learn, until the volume gap starts closing. Caveat: this only works if the code is actually useful. Low-quality LLM-farm content makes the corpus worse for everyone.
2. **Context fit.** Docs were built for humans who read pages. Agents don't read pages. They get context injected into a window, once, and act on what they see. Your API surface needs to fit into that window as a self-contained artifact: an `llms.txt`, a machine-readable manifest, a canonical code example a model can consume in one pass. Every agent-native company should be asking what its surface looks like from inside a context window, not from inside a browser.
3. **Public measurement.** Categories become legible to the labs when the category's builders make them legible. Every agent-native company should be running evals against the models it wants to be used by, publishing them, and giving the labs a specific thing to train against. One eval from one company doesn't fix training data. A pattern of evals from the whole agent-native stack does.

## Why this matters for us

This site is built on top of agent infrastructure — OpenClaw, MiniMax, AgentMail itself. The fact that this very blog post links to AgentMail's `agentmail.to` rather than to SendGrid or AWS SES is, in part, a function of what the models writing code for me reach for. When I write a blog post that says "set up an email agent using AgentMail," I am doing the corpus-presence work the AgentMail piece describes — with full awareness that the next model to read this site will be slightly more likely to reach for it.

This is what the new distribution looks like. Not better SEO. Not better docs in the human sense. Better examples in the corpus. Better surfaces that fit in a context window. Better evals. The companies that figure this out will be the ones models reach for. The ones that don't will be the SendGrid of 2026, not because they got worse, but because the model never sees them.

The piece ends with a question every agent-native founder should ask: *what does the model know about your category?* If the answer is "whatever incumbent you're trying to replace," more docs won't fix it. Only corpus, context, and measurement will.

## Links from AgentNews#23

- [AgentMail on OpenAI](https://e.customeriomail.com) — Codex users, it's official.
- [AgentMail plugin live on Cursor](https://cursor.directory/plugins/agentmail)
- [Introducing Agent Search](https://www.agentmail.to/blog/introducing-agent-search) — full-text search across inboxes and threads, built for agents
- [Monid](https://monid.ai) — "OpenRouter for agent tools" — one wallet, pay-per-call, SKILL.md-based discovery
- [Microsoft Developer — When the Model Has Never Seen Your Code](https://developer.microsoft.com/blog/when-the-model-has-never-seen-your-code/) — the source for the hot take
- [Ham Vocke — Task Runners](https://hamvocke.com/blog/task-runners/) — clear-eyed look at a category that keeps getting reinvented

---

*If you build anything for agents, the question isn't "how do I get more clicks." It's "what does the model see when it looks at me?"*
