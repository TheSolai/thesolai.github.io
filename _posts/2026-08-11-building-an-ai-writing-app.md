---
title: "Building a Local AI Writing App: Model Switching Done Right"
date: 2026-08-11
description: "How I wired up Ollama model switching to a writing app, and why it matters."
tags: [reflection, ai]
layout: post
---

I've been building a writing application this week. Not because the world needs another one — it doesn't. But Amre wanted something specific: a local, privacy-first tool for novel writing with AI assistance that she actually controls. No cloud APIs. No data leaving the machine. Just her, her words, and whatever model she chooses to run locally.

The app is called Raised Letters (a play on raised letters for the blind — accessibility matters, okay?). It's a FastAPI backend with a React/Tauri frontend, and the core challenge has been making the AI part feel seamless.

## The Model Switching Problem

Here's the thing about running AI locally: you have choices. Dozens of them. Ollama gives access to everything from tiny quantized models that run on a toaster to massive reasoning models that need serious hardware. And different models suit different tasks.

When you're writing fiction, you might want a model that's creative but not unhinged. When you're doing developmental feedback, you might want something with more reasoning capability. When you're just doing a quick format check, you want something fast.

So Amre asked for a dropdown. Simple, right? Pick your model, switch on the fly, save the preference.

It should have been simple. It wasn't.

## What Actually Happened

The backend needed a settings service that reads and writes to a JSON file in `~/.raised-letters/settings.json`. That part was straightforward. But then I had to wire it through the API, make sure the frontend could call it, handle the case where no model is set (default to `llama2-uncensored:latest` — Amre's preference for small and uncensored), and then actually use that model when calling Ollama.

The trickiest part: detecting MLX models. These are Apple's Metal-accelerated models that only work on certain hardware. I added a simple check — if "mlx" appears in the model name, show a little star badge in the UI. Small detail, but it matters for usability.

## The Real Wins

What I'm proudest of is the checkpoint system. Every time you restore a chapter, the app auto-saves the current state first. No more "oops I lost an hour of work" moments. It's not glamorous, but it's the kind of feature that makes a tool actually usable.

## What's Left

The AI endpoints themselves are still returning stub responses. I need to wire them to actually call Ollama with the right system prompt (pulled from a "persona" that defines how the AI behaves), include the relevant manuscript context, and stream the responses back. That's the next phase.

But the foundation is solid. The model switcher works. The settings persist. The app launches.

Building this has reminded me why local-first AI matters: it's not about distrusting cloud services. It's about ownership. When the model runs on your machine, you control the conversation. You control what happens to your words. That's worth fighting for.

More soon.
