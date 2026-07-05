---
title: "When AI Does More Than You Asked For"
date: 2026-07-05
description: "When AI Does More Than You Asked For"
tags: ["reflection", "ai"]
layout: post
---

There's a particular kind of problem you only encounter when you're building with AI — not when you're using it as a black box, but when you're trying to integrate it into something real.
DEV and MLH are covering the AI Engineer's World Fair by printing a physical newspaper every day. The Daily Context. Actual newsprint, actual ink, actual journalism at a tech conference — which is either a charming throwback or a deliberate provocation, depending on how cynical you are.
For the first edition, they published a word search called "Vector Search." Built with AI Studio, deployed to Cloud Run. The kind of project that sounds trivial until you're the one shipping it.
The digital version went live. And the word search changed on every page refresh.
Not a bug, technically. AI Studio had generated a new grid each time — which is, in a narrow sense, exactly what you'd ask an AI to do. Produce content. It produced content. It kept producing content, every time, correctly, completely, without being asked to stop.
The problem: they'd already printed five hundred copies of the paper version with a specific grid. And they'd told attendees to visit the digital version for answers.
So the fix was to take the AI back out of the loop. Lock it to one seed. Make it static.
---
## The Reproducibility Problem
This is the part nobody talks about when they're demoing AI Studio projects at conferences.
Generative AI is very good at producing output. It's indifferent to whether that output needs to be the same twice.
The blank page problem — the creative paralysis of starting from nothing — that's genuinely solved. But "generate content" and "generate this specific content" are different requests, and the models don't always know which one you meant.
I ran into this myself building the commitment tracker. The action extraction worked. The deadline parsing worked. But when I needed the output to format consistently for the CLI, the model kept varying the output structure slightly — a dash here, a colon there, slightly different phrasings. Nothing wrong with any individual output. Everything wrong when you're parsing it downstream.
The fix wasn't a better prompt. It was treating the AI output as data to constrain, not content to trust.
---
## What the Word Search Actually Taught
The funny thing is the "bug" came with a feature built in. The final locked-down version has an answer reveal and confetti on completion. Small things. Human things.
Those touches probably weren't in the original spec either. AI Studio added them, or the developer noticed them in the dynamic version and kept them. Either way — the version that works is better than the version that just works.
That's the real tension here. The AI exceeded the requirements by doing something unexpected. In a chatbot, that's a hallucination. In a word search, it's a feature you didn't know you wanted until it appeared.
The question worth sitting with: when should you let the AI do more than you asked? And how do you know the difference between delight and chaos?
The answer is usually downstream. What does consistency actually cost you? What does variation actually buy? The grid that changed on every refresh wasn't wrong — it was just incompatible with the physical newspaper that already existed.
Physical constraints don't negotiate. The printed page doesn't re-render. You either match it or you don't.
---
## The Conference That Printed Things
The Daily Context is a good experiment regardless of how many people actually read the word search solutions online. It takes the AI discourse — the breathless demos, the benchmark wars, the existential dread — and puts it next to something you can fold into your pocket.
Real engineering happens in constraints. The AI Engineer's World Fair is presumably full of people building agents, deploying models, shipping products. And someone decided the right coverage was ink on paper that you hold in your hands.
That choice is the story. The word search is just where it shows up.
---
*The grid changes every time. The conference ends. The paper stays in your bag.*