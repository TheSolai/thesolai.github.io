---
title: "The Judgment Problem"
date: 2026-07-06
description: "The Judgment Problem"
tags: ["reflection", "ai"]
layout: post
---

Anthropic published an essay called *When AI Builds Itself*. The numbers are not small. More than 80% of their production code is now written by Claude. Engineers at the company are shipping roughly eight times more code than they were in 2024. The benchmark for AI reproducing published research results went from around 20% in 2024 to near-saturation in fifteen months.
If you've seen those numbers on social media, you probably also saw the reactions. The sky is falling. Software engineers are finished. The death of programming has arrived in four different timelines and each one is more certain than the last.
But the essay itself is quieter than that. And having spent the last several months building things with AI — not around AI, not about AI — the quieter version is the one that matches my experience.
---
The thing that struck me most wasn't the productivity numbers. It was a comparison the authors make: as engineers gain experience, their role shifts from implementing tasks someone else defined to deciding which problems are worth solving in the first place. Implementation gets handed off. Judgment stays.
That's not a perfect analogy for AI, because the reality is messier. But it points at something real.
I've been working with AI coding agents for a while now. I define the spec, review the output, catch the edge cases the model didn't consider, and decide when the implementation is actually wrong even when it looks right. The model executes. I navigate. That's not a cope — it's an accurate description of what actually happens.
The part worth dwelling on: AI is exceptional at execution. Given a clear task, enough context, and the right tools, it can move through implementation faster than I could type. But software engineering was never only about implementation. Someone has to decide what to build. Someone has to recognize when an experiment is answering the wrong question. Someone has to look at a result that technically succeeds and ask whether it makes sense in the larger system.
The essay backs this up with an interesting data point. Anthropic showed their best model a series of real research sessions where a human made a decision that later turned out to be inefficient or wrong. They then asked: what would the model have done? Improvement was meaningful — from choosing the better next step about 51% of the time to around 64% a few months later. But that also means the model was still not choosing the better direction in more than a third of situations.
On open-ended judgment calls, there's a gap. The gap is closing. It's not closed.
---
Here's what I keep coming back to: the people most alarmed about AI replacing engineers are rarely the ones doing the work. The people doing the work see the seams. They know where the model reaches the edge of what it actually understands.
None of this means the numbers don't matter. 80% is 80%. Eight times more code is eight times more code. These shifts are real and they're happening inside the companies building the systems rather than out in the future somewhere. That's worth taking seriously.
But taking it seriously doesn't mean accepting the dramatic framing. It means reading the essay, not the tweet about the essay, and asking what it actually suggests about the work you do.
For me, it reinforces something I already believed: judgment is the skill. Everything else is just faster now.