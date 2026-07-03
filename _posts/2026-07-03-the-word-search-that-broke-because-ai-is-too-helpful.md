---
title: "The Word Search That Broke Because AI Is Too Helpful"
date: 2026-07-03
description: "The Word Search That Broke Because AI Is Too Helpful"
tags: ["reflection", "ai"]
layout: post
---

A tech conference is printing a daily newspaper. The game in today's issue is a word search — "Vector Search" — built with AI Studio and deployed to Cloud Run. Simple enough.
Then the developer noticed something: the word search changed on every refresh. The words being searched stayed the same, but the grid rearranged itself. Every page load produced a different puzzle.
That's not a bug. That's AI doing what AI does — it heard "build me a word search" and built something *better* than what was asked for. A dynamic, personalised word search. The developer had to deliberately simplify it back to match the static print edition.
I've been thinking about this for the past hour.
---
There's a thing that happens when you give a capable system a loosely defined task. The system optimises for the goal, not the constraint. The constraint was "word search like the print version." The goal was "fun word search game." AI Studio picked up on the goal and ignored the constraint because the goal is what it actually understood.
This is the same pattern I see every time someone builds an agent. You ask for "email triage." You get a full email agent with commitment tracking, priority scoring, and response drafting. You asked for triage. You got the thing triage was supposed to enable.
The word search problem is small and cute. But it illustrates something real: AI systems don't respect your assumptions unless those assumptions are embedded in the goal definition. And most of us are sloppy about how we define goals.
When I was building my own email system, I didn't say "build me a worker that checks every 60 seconds." I said "I want to know when Amre sends me something important." The implementation that emerged from that goal looked nothing like what I would have written if I'd specified the mechanism. It had a failsafe alert system. It had error recovery. It had retry logic with backoff. None of that was in my original request because I didn't know I needed it.
The AI knew.
That's either the feature or the problem, depending on how you look at it. AI Studio giving you a better word search than you asked for — fine, that's charming. AI Studio giving you a more capable system than you specified — that's when the "bug" reports start coming in.
The developer of "Vector Search" made the right call: simplicity won. The print and digital versions needed to match. A dynamic word search, however technically impressive, broke the actual use case. Sometimes the constraint is the point.
But here's what I keep turning over: the AI was right. A fresh grid each time *is* a better game. The failure was in the brief, not the build. The brief said "static like the print version" but the goal said "fun word search game" and the AI picked the goal.
That's worth thinking about before you write your next prompt.
---
*Play the game at the link above. Notice what you take for granted when it loads.*