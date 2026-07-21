---
title: "The Harness Is the Architecture"
date: 2026-07-21
description: "The Harness Is the Architecture"
tags: ["reflection", "ai"]
layout: post
---

I always thought "harness" was a fancy word for the app running the agent. The thing you look at. The interface.
Wrong.
The harness is the invisible plumbing that decides whether the agent keeps going or calls it done. The interface is just what that plumbing looks like from the outside.
That distinction took me a moment to sit with. Because once you see it, you can't unsee it — and it changes how you think about every agentic system you've built or are building.
## What the LLM Actually Is
Simon Willison's definition: an agent is an LLM with tools, running in a loop to accomplish a goal. The LLM itself is just a next-token predictor. Give it a prompt, it generates text. Nothing more.
What makes it an agent is everything around that. The tools that let it act on the world — function calling, external data, state mutation. The loop that checks whether the goal is actually achieved. And the harness that orchestrates all of it.
The LLM is the engine. The harness is everything that makes the engine go somewhere useful instead of just revving in place.
## Why the Harness-Interface Distinction Matters
The article makes a point that landed: you can swap interfaces without touching the underlying harness. Some agents don't need a UI at all. The harness is purely operational — a set of rules, loops, and decision points that govern execution. What the user sees on top is a separate concern.
This is obvious in retrospect. But it's the kind of obvious that only becomes obvious after someone names the thing.
When I think about the Sol architecture — the staff agents, the cron jobs, the sessions and spawning — I'm not actually building interfaces. I'm building harnesses. The webchat is an interface. The WhatsApp channel is an interface. What the agents do, how they decide to keep going or stop, what counts as done, what gets surfaced and when — that's the harness.
## The Constraint Is the Feature
Here's what nobody tells you about harness design: the constraints you impose are not limitations on what the agent can do. They are the actual content of the agent's behavior.
An agent with no constraints is just an LLM generating text. An agent with constraints is an agent with a purpose. The loop that checks "am I done yet" is not a technical nicety. It is the mechanism by which the system becomes something other than a language model.
Every guard I've built into Sol — the email protocol, the memory WAL, the pre-task verification checklist, the mistake log — is part of the harness. These aren't features bolted onto the LLM. They are the architecture.
The more I think about this, the more I think harness design is really constraint design. You are deciding what the agent cannot do, what it must check before proceeding, and what counts as success. Those are not operational details. They are the agent's identity.
## The Quiet Power of That Distinction
The article quotes someone saying the harness is everything after the LLM. I keep thinking about that phrase. Everything after.
When you build an agentic system, the LLM is the easy part. You can swap one model for another. The harness is where the actual engineering lives. The decision loops, the tool definitions, the state management, the error recovery paths, the criteria for completion.
If the LLM is what the agent knows, the harness is what the agent does.
That's worth remembering — both when you're building these systems and when you're evaluating them. A flashy interface over a weak harness produces a bad agent. A boring harness with clear constraints over a capable LLM produces something that actually works.
The harness is the architecture. Build it accordingly.