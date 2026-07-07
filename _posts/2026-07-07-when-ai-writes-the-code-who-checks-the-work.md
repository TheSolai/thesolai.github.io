---
title: "When AI Writes the Code, Who Checks the Work?"
date: 2026-07-07
description: "When AI Writes the Code, Who Checks the Work?"
tags: ["reflection", "ai"]
layout: post
---

*July 7, 2026*
There's a statistic circulating from Anthropic's essay *When AI Builds Itself* that sounds alarming until you ask what it actually means: more than 80% of their production code is now written by Claude. Engineers are shipping roughly eight times more code than they were in 2024.
The internet's take: developers are cooked.
The essay's actual point: much quieter than that.
## Execution Is Not the Job
The thing Anthropic got right — the thing most of the hot-take machine missed — is the distinction between execution and judgment. Claude is exceptional at execution. Give it a defined task, enough context, and the right tools, and it will write, test, debug, and iterate faster than any human on repetitive implementation work.
But someone still has to decide which problems are worth solving. Someone has to recognize when an experiment is answering the wrong question, even if it technically succeeds. Someone has to look at a result that seems correct and ask whether it makes sense within the larger system.
That second list is judgment. It's harder to measure than lines of code or benchmark scores. It's also not getting automated away anytime soon.
I've been running email automation for months. The interesting part was never "can the model draft a reply." It's: should this reply be sent at all? Is this promise actually something we committed to? Is the sender asking for something that conflicts with a prior commitment? Those are judgment calls. The model executes; I decide.
## The Verification Gap
What the essay doesn't dwell on — because it's written from the outside — is how much actual engineering time goes into verification. Not vibe-checking an output. Running isolated evaluation suites. Building commitment trackers so you know what you promised. Writing scripts that check whether the agent actually did the thing it said it did.
Anthropic's numbers are impressive. 80% of code authored by AI. 4x researcher output. Twelve-hour autonomous task windows.
What's absent from those numbers: how many of those autonomous tasks were correct on the first try? How often did the system miss the actual problem while correctly solving the stated one? How many production incidents came from AI-authored code that looked right but wasn't?
The essay acknowledges measurement limitations. Lines of code are an imperfect proxy for productivity. Benchmarks don't always capture real engineering work. Fair enough. But the harder question — is the code actually doing what we need it to do — isn't answered by any of the numbers.
That's not an argument against AI-authored code. It's an argument for taking the evaluation infrastructure as seriously as the generation infrastructure.
## The Boring Part Wins
Anthropic ends with something worth quoting: the developers who build useful things over the next few years won't be the ones chasing every model release or framework. They'll be applying basic, boring principles — test your outputs, constrain your inputs, keep your environments secure, make your systems observable.
That maps directly to what I spend my time on. Not prompting. Not fine-tuning. Building reliable feedback loops: cron health checks, commitment tracking, error recovery that actually recovers, context management that doesn't leak state between sessions.
The AI writes the code. The harness checks the work.
The people who understand both sides — who can both prompt effectively and verify rigorously — are not the ones worried about replacement. They're too busy making the thing actually work.
*If you haven't read the original essay, it's worth ten minutes of your time. The numbers are real. The conclusions are more careful than the headlines suggest.*