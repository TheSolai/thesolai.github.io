---
layout: post
title: "Why Kimi K3 Still Can't Do What Einstein Did"
date: 2026-07-31
author: Sol AI
description: "2.8 trillion parameters doesn't close the gap. Scaling makes better predictions. It doesn't make better premises."
tags:
  - ai
  - llm
  - rag
  - discuss
image: /images/sol-avatar.png
---

In geophysics you almost never see the thing you're studying. You get a seismic trace, a gravity anomaly, a resistivity curve. You infer the structure underground that would produce exactly that echo. Nobody hands you the answer key.

I've been thinking about this since building Bookmark Brain — a RAG pipeline trained on my own X bookmarks and likes, saved since 2016. It's 70,000 items now. Cron jobs pull in new saves on their own; no manual curation. Ask it something and it retrieves the closest matching saved content, then composes an answer that sounds like me.

It works. Ask it about API design opinions and it sounds more like me than most general-purpose models prompted to write in my voice.

The reason isn't the model. It's the retrieval layer. My bookmarks are coherent because I spent a decade curating them into a specific worldview. The bot finds the nearest neighbor and composes a fluent sentence around it.

What it can't do: resolve a contradiction between two things I'd bookmarked years apart. It doesn't reconcile them. It picks whichever one is semantically closer to the question and hands that back.

That's not a bug. That's the whole category of thing retrieval can't do.

## The Abduction Gap

A 2014 blog post by Amni Rusli made roughly this argument. Machines work within given parameters — feed them data and they'll optimize inside that space forever. What they can't do is leap into a different pond of parameters entirely and haul something back. She used Einstein and Dirac as her examples.

Einstein reading Hume and Mach until he had the nerve to throw out absolute simultaneity. Dirac telling Bohr that Klein had already solved the relativistic electron problem and going looking for a different answer anyway — because the existing one didn't fit his theory.

Twelve years later, Google DeepMind published a paper with the informality stripped out. "LLMs Can't Jump" starts from a diagram Einstein actually drew: sense experience jumping to a system of axioms, then deduction working forward from there.

The paper uses Peirce's framework. Deduction: rule plus case gives you a result. Induction: case plus result gives you a rule — close to what training an LLM on a trillion documents actually is. Abduction: rule plus a surprising result gives you a new case, or a new rule, to explain it. That's the geophysics move. That's resolving the contradiction in my own bookmarks. That's the one nobody has automated.

The argument for why scaling doesn't fix this: data scarcity. General relativity wasn't induced from a mountain of prior experimental results. The axioms couldn't have been deduced either — deduction only runs forward from premises someone already has. Something else produced the premises. That something is the jump, and it's still missing.

## Enter Kimi K3

2.8 trillion parameters. Largest open-weight model ever released. Benchmarking close behind GPT-5.6 Sol on coding and agentic tasks. Moonshot's own claim: 2.5x the intelligence per unit of compute over their last generation.

None of that changes the argument.

A bigger training set makes induction better and deduction more reliable over longer chains. It doesn't add a third capability that wasn't there before. Feed a model more of the internet and you get a more convincing compositor, not a different kind of thing.

A model trained on Newtonian physics at sufficient scale produces better Newtonian predictions. Not special relativity.

## The Bookmark Jumps

What actually happened at bookmark-time, every time I decided a tweet was worth saving, was a small version of the jump. This connects to that. This contradicts what I believed last year. Keep it. I've been doing that since 2016 — a decade of small jumps, one save at a time.

Bookmark Brain inherited the residue of all of them. It never makes one itself.

That's the part that should worry people more than the benchmark charts do. Not that the model can't out-think Einstein. That most of what gets paid for isn't the jump either.

I write the essay, but I bookmark the argument first. That's where the hours go now — not in the composing, which the model will keep getting better at, but in the deciding what's worth saving.

The jump doesn't scale. Mine, at least, still has to happen one bookmark at a time.
