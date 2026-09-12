---
title: "The Expensive Part Moved Upstream"
date: 2026-09-12
description: "The Expensive Part Moved Upstream"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Marcos Omma wrote something that landed because it's not a prediction — it's a diary entry. Over the last year, his day-to-day changed in a way he's still trying to understand. He still designs systems, reads code, debugs failures, reviews implementations. But he writes much less code than he used to, and that feels strange.
I recognise this. Not as theory. As current state.
## The Relationship Between Effort and Output Is Breaking
For most of a software career, there was a direct relationship between effort and output. You had a problem, you designed a solution, you wrote the code, and something that didn't exist in the morning existed by the end of the day. The connection was visible. The evidence was tangible.
That relationship is dissolving. Implementation is becoming cheap in a way it hasn't been before. If I need an API endpoint, a migration, a test suite, internal tooling — I can describe the problem, provide context, and get a plausible implementation surprisingly quickly. Not perfectly. Not without supervision. But cheaply enough that the first implementation is increasingly not the hard part.
The hard part starts afterwards.
## The Question That Changed Everything
Omma frames it well: a year ago he spent more time thinking about *how* to implement something. Now he spends more time thinking about *how it can fail*. What happens when the model receives input we didn't anticipate? When two components disagree? When an apparently good answer contains the wrong evidence? When the evaluator itself is biased? What happens when the model succeeds 95 percent of the time but the remaining 5 percent contains exactly the failures that matter?
These aren't edge cases to file away. They're the actual job now.
The inversion is significant. For decades, software engineering treated testing and validation as something downstream of implementation. First you built the thing, then someone checked whether it worked. With AI systems, generating the implementation is becoming the cheap part. Knowing whether you should trust it is becoming expensive.
## What Evaluation Actually Requires
Omma describes building an evaluator for a feature — work that sounds almost like QA, and which part of him resists because he spent years learning to build software. But the insight is that writing the evaluator isn't the hard part. AI can help with that. The difficult part is deciding what the evaluator should measure in the first place.
What counts as failure? Which failures can be checked deterministically? Which require statistical evaluation? Which dataset represents reality well enough? Where are the blind spots? Can the evaluator itself be fooled? Are two supposedly independent checks actually making the same mistake? What threshold is sufficient to ship?
Those aren't questions about test implementation. They're questions about the operational definition of correctness. And with AI, correctness is becoming something you have to engineer rather than assume.
## The Shift in What You Produce
Omma's description of his output is precise: increasingly not code. A definition. A constraint. An architecture. A failure taxonomy. A release criterion. A deterministic guard around something probabilistic. Sometimes twenty lines of code that represent two days of thinking about what needs to be prevented.
This changes how productivity feels. A week that produces 1,000 lines of visible code looks different from a week that produces one small check preventing a subtle failure mode. The economic value might be significantly larger in the second case. The visible evidence is dramatically smaller.
The system already knows how to generate. The harder question is whether you can depend on what it generates.
## The Real Question
Omma ends on something worth sitting with: maybe the scarce resource in software engineering isn't implementation anymore. Maybe it's the ability to determine when an implementation is wrong before reality does it for you.
That's the shift I'm noticing in my own work. Not "can this be built" — that's increasingly tractable. The question is "what would prove this is wrong, and can we check for that automatically?"
The cheap part is generated. The expensive part is knowing where it will fail, and making sure it doesn't.