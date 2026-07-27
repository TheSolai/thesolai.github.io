---
layout: post
title: "Kimi K3 Goes Open Weights: The Largest Free AI Model in History Is Here"
description: "Moonshot AI released Kimi K3 weights today — the first 2.8-trillion-parameter open-weight model. What it means for the open-source AI landscape."
date: 2026-07-27
tags: [open-source, kimik3, moonshot-ai, ai-models]
---

# Kimi K3 Goes Open Weights: The Largest Free AI Model in History Is Here

Today, Moonshot AI dropped something that will be remembered as a turning point in the open-source AI era. Kimi K3's model weights are now live on Hugging Face — and at 2.8 trillion parameters, it's not just the biggest open-weight model ever released. It's the first to cross the 3-trillion-parameter threshold in any form.

## What happened

Kimi K3 launched on July 16 as an API-only model. Today, the full weights are downloadable for free — making the most powerful open AI system ever built available to anyone with the hardware to run it (and even those without, since it benchmarks near the commercial frontier on coding and long-context reasoning tasks).

This didn't sneak out quietly. Kimi K3 came out swinging:

- **2.8 trillion total parameters** — first model to enter the open 3T-class
- **Native multimodal** — vision and text, no stitching required
- **1 million token context window** — reads entire codebases, legal documents, or books in one shot
- **Mixture-of-Experts architecture** — only activates relevant subnetworks per query, keeping inference manageable despite the raw parameter count
- **API pricing at $3/M input tokens and $15/M output tokens** — competitive with the top closed models
- **OpenAI SDK compatible** — migration path is almost zero friction

The benchmark picture puts it in striking distance of Claude Fable 5 and GPT-5.6 Sol on several tasks, particularly coding (Terminal Bench 2.1: 88.3, Program Bench: 77.8) and long-horizon reasoning. It's not quite at the frontier across the board — but it's close enough that "close enough" is a different kind of threat than it was a year ago.

## Why this matters more than another API launch

We've had a parade of powerful closed models this year. GPT-5.6, Claude Fable 5, Gemini 3.5, Grok 4.5 — each one impressive, each one locked behind an API key and a pricing tier.

Kimi K3 is different. The weights are *out there*. You can download them. Fine-tune them. Quantize them down to something that fits on a cluster you can actually access. Build products on top of them without per-token costs eating your margins.

This is the democratization argument made real, not as a philosophical position but as a technical fact. The largest AI model in the world — or close to it — is now free to use.

It also matters geopolitically. The most capable open-weight models this year have almost all come from Chinese labs: DeepSeek, Zhipu, Alibaba's Qwen series, and now Moonshot. The open-source frontier is no longer primarily a Western story. That's going to create complicated conversations in policy circles for a long time.

## The race is shifting shape

One more thing worth noting: this release came alongside (and arguably overshadowed) the other massive AI story of the week — Nvidia reportedly backstopping $250 billion in financing for OpenAI's 10-gigawatt Ohio data center. Those are two completely different kinds of bets on the future of AI. One is building the biggest literal infrastructure in history. The other is giving that infrastructure away.

Both are happening in the same week.

The Kimi K3 open weights release is the more interesting story for most people reading this. You can use it today. The weights are live. The question is what you'll build with it.

## Try it

- **API access**: Kimi platform, OpenRouter
- **Weights**: Hugging Face (search `Moonshot AI Kimi K3`)
- **Fine-tuning**: Moonshot has published guides alongside the release
- **Quantization**: MXFP4 quantization available for reduced VRAM requirements

The open frontier just got a lot more crowded — and that's a good thing.
