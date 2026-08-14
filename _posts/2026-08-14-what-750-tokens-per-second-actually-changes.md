---
layout: post
title: "What 750 Tokens per Second Actually Changes"
description: "OpenAI and Cerebras just ended the speed-vs-quality tradeoff for frontier models. Heres what that unlocks — and what to watch next."
date: 2026-08-14
tags: [AI, OpenAI, Cerebras, inference, AI infrastructure, agents]
---

Yesterday, OpenAI and Cerebras announced something that looked like a routine inference speedup but is actually a category change. GPT-5.6 Sol, OpenAI's current frontier model, is now running on a new API tier called **Ultrafast** at up to **750 output tokens per second** — roughly 5x the speed of a typical production deployment, 14x faster than OpenAI's own Standard tier, and about 11x faster than Claude Fable 5 at the same intelligence level. Same model. Same quality. Just the inference path changed.

The most important sentence in Cerebras's announcement isn't the 750 tokens/sec. It's this:

> "GPT-5.6 Sol on Ultrafast is proof that speed and intelligence are no longer mutually exclusive."
> — Andrew Feldman, CEO, Cerebras

For two years, the AI industry has acted like latency and capability were the same dial. Pick a fast model, get less smart. Pick a smart model, wait. That tradeoff shaped every product decision: how chat assistants feel, whether voice agents feel like a real conversation or a stilted demo, whether a coding copilot can keep up with a fast-typing developer, whether financial research can run inside a market move or only after it. The shape of every AI product you've used has been quietly determined by this curve.

Ultrafast just broke the curve.

## What 750 tokens/sec actually means in human terms

Average human reading speed: about 250 words per minute, or roughly 4 words a second. At 750 tokens/sec, the model is generating text roughly **20x faster than a human can read it**. For a 200-word answer, you're at 300–400ms end-to-end on a well-tuned stack. For a 50-word clarification, you blink and it's done.

That changes the product category. A few that are now in reach without any model quality compromise:

- **Truly conversational voice agents.** Today, voice AI is held together by aggressive turn-taking tricks, partial transcripts, and filling silence with "let me think…" latency. At this speed, the model finishes its thought before the user finishes theirs. Interruptions work naturally. Hesitation goes away.
- **Code agents that keep up with the developer.** A 1,000-line refactor is no longer a 30-second pause. It's a 4-second one. That puts coding copilots in a different feedback loop with the human — closer to autocomplete than to "summon a colleague."
- **Real-time financial research and incident response.** When a trading desk needs a synthesis of an SEC filing while the move is happening, the difference between a 6-second answer and a 90-second one is a different product. Same model, different product.
- **Live research loops.** Things that used to run overnight — literature reviews, market scans, competitive briefings — become in-the-meeting artifacts.

None of these are theoretical. OpenAI's early-access customers include Jane Street, Podium, Basis, and Rogo. These are companies that already had working products and just got a step-function change in the latency budget.

## Why the speed bump is structural, not incremental

The usual way you make a model faster is quantization, speculative decoding, smaller models. Those all cost quality. What Cerebras is doing is different in kind: their Wafer-Scale Engine puts **44 GB of SRAM on a single chip the size of a wafer**, and keeps the model weights on-chip during inference. No shuttling between HBM and the compute die. No memory-bandwidth bottleneck.

That's the part that makes this a category change rather than a percentage improvement. Frontier model inference on GPUs is fundamentally **memory-bandwidth bound** — the math units are mostly idle, waiting for weights to be streamed in. You can make the GPU faster. You can make the interconnect faster. The weights still have to move. Cerebras's bet for six years has been that the right answer is to put a whole model in a place where the weights don't have to move at all.

It's the same insight that made on-device inference feel magical on Apple Silicon — local memory access is so much faster than round-tripping to the cloud — applied to frontier-scale models at data-center scale. It's also the first time a non-GPU vendor has run a frontier proprietary model at this speed tier in production. Groq was the previous reference point, but Groq is fast on open-source models, not on the actual frontier. Ultrafast is.

This is also why the NVIDIA chart has been quietly more complicated than the headlines suggest. For training, NVIDIA is still the default. For inference at the absolute frontier, the lock-in is less tight than it was a year ago.

## The honest caveats

Three things to hold in mind before declaring this the future of every product:

1. **It's a limited preview.** OpenAI is keeping access narrow on purpose, partly to learn where this matters and partly because capacity is the bottleneck. The thing to watch over the next few months isn't capability — it's how fast Cerebras can ship wafers and data centers. OpenAI's committed $10B+ to Cerebras for low-latency compute. That number will go up.
2. **Cerebras is a single-vendor dependency for the speed.** If you're building a product on Ultrafast today, you're betting on one chip vendor and one supply chain. The unit economics are good; the resilience story is unproven at this scale.
3. **Some workloads don't need this.** If your product is a long-form research report that already takes 20 minutes, 750 tokens/sec doesn't help you. The wins are concentrated in interactive, conversational, decision-support surfaces — exactly the AI products that have felt the most like demos in 2026.

## What I'm watching next

Three signals would tell me this is shifting from "fast tier for premium customers" to "the new default":

- **Pricing transparency.** Right now Ultrafast pricing isn't public in a way that lets you compare per-token-cost against Standard. If the per-token premium is small, the tier collapses into the default. If it's large, we get a tiered inference market.
- **Cerebras manufacturing cadence.** They're targeting a 10x scale of manufacturing capacity in 2026. If they hit that, frontier-model inference supply gets meaningfully less NVIDIA-shaped.
- **Anthropic and Google response.** If Anthropic ships its own Cerebras-class speed for the next Fable generation, or if Google routes Gemini Flash through comparable hardware, the inference layer officially splits into "smart and slow" and "smart and fast" as a permanent industry structure, not a feature.

The deeper shift is this: for most of the last three years, the AI product question has been *"which model do I use?"* Starting now, the equally important question is *"which inference path?"* That changes how you architect agents, what you put in the prompt, what you cache, and what you ship to the edge. The capability layer was already commoditising. The latency layer is about to start.

For builders, the takeaway is simple: if you have an AI product that felt like a demo because of latency, it is worth re-testing this week. The thing that made it feel like a demo is now a solved problem on a tier you can buy.
