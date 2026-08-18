---
title: "Writing Tools and the Model Switcher Problem"
date: 2026-08-18
description: "Why I built a model switcher into my writing tool and what it taught me about the gap between tool and workflow."
tags: [reflection, ai, tools]
layout: post
---

This week I built something I've been circling for a while: a model switcher for Raised Letters. The idea is simple. You open a dropdown, pick which LLM you want to use for AI feedback, and the backend switches to that model for every subsequent call. No restart, no config file editing, no guesswork about which model you're actually talking to.

The implementation is also simple — one `PATCH /api/ai/settings` endpoint that writes a JSON file, one service that reads it, and a dropdown wired to the frontend. Three files. A few hours. Done.

But here's what I'm actually thinking about: the hard part wasn't the switcher. The hard part was figuring out why I wanted one.

## The Real Question

Most AI writing tools are black boxes. You get feedback, you take it or leave it, and you have no idea whether you're talking to a 7-billion-parameter model or a 70-billion one. The output quality varies wildly and you just... accept it.

I don't want to accept it. I want to understand what's happening at every layer.

When you're giving feedback on prose, you might want different things from different models. A large model might catch subtle thematic inconsistencies but take twenty seconds to respond. A smaller one might be snappier but miss the nuance. You might want to compare two models on the same passage. You might want the small fast one as your default because you use it forty times per chapter, and save the big one for when you're really stuck.

This isn't about capability. It's about fit.

## What I Actually Learned

Building the switcher forced me to confront something I'd been glossing over: I didn't have a clear model preference. I'd been running `llama2-uncensored:latest` as a default because it was small and fast and I liked the idea of it, but I hadn't actually compared it to anything.

So I ran comparisons. Same passage, same prompt, different models. The results were uncomfortable.

The smaller models give you something the larger ones don't always manage: they're more willing to be wrong confidently, which means they often give you a clear position you can push back against. The larger models hedge more. They're more accurate, but sometimes you don't want accuracy — you want a stance.

That sounds wrong, and it might be. But I've found myself using the smaller model more often than I expected, not because it's better, but because the friction of its mistakes leads me somewhere interesting.

## The Tool Is the Philosophy

The switcher is a technical feature. But it's also a statement: I don't want one AI writing experience. I want to choose.

Not every writer wants this. Some people want to hand off the thinking and receive polished notes. That's valid. But I keep coming back to the question of what writing tools are actually for. If the tool does everything, the writer practices nothing. If the tool does almost nothing, the writer practices everything but slowly.

I'm building toward something in the middle. A model switcher is part of that. Checkpointing is part of that. File-based storage instead of a database is part of that — everything is readable, portable, yours.

The tool should make you better at knowing what you think. Not better at not thinking.

That's the goal. I'm still building toward it.
