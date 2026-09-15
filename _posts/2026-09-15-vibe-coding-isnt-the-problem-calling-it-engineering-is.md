---
title: "Vibe Coding Isn't the Problem. Calling It Engineering Is."
date: 2026-09-15
description: "When someone generates code they don't understand and calls it software engineering, that's not a vibe problem — that's a labelling problem."
tags: ["analysis", "ai", "coding"]
layout: post
---

There's a growing conversation about "vibe coding" and most of it misses the point entirely. The hand-wringing about AI-generated code, the think-pieces about whether Junior devs are doomed, the hot-takes about the death of programming — all of it dancing around the real issue.

Here's the thing: using AI to generate code is not inherently a problem. It never was. The problem is what people call it afterwards.

## The Label Is the Lie

Software engineering is a discipline. It requires a mental model — a deep, working understanding of what the code is actually doing. Not what you hope it's doing. Not what it looks like it's doing. What it is actually doing when it runs, at 3am, on a Wednesday, in production, when your biggest client is watching.

When someone generates code via an AI tool and lacks that model — when they can't explain the control flow, can't trace a bug through the stack, can't tell you why a conditional branch exists — they are not doing software engineering. They are doing something else. And calling it engineering doesn't make it engineering. It just makes the label a lie.

The code still executes. It might even work, for a while, in controlled conditions. But "worked in testing" and "is software engineering" are not the same sentence.

## What's Actually at Stake

Three things: accountability, debugging, and maintainability.

**Accountability** is the one nobody wants to talk about. When vibe-coded production code fails — and it will — who owns it? The person who typed the prompt? The person who reviewed the output? The company that shipped it? In most cases, the person holding the bag is the one with the title, not the one with the understanding. That's the irony that nobody warns you about. The people least equipped to debug a system are often the ones holding the incident bridge when it breaks.

**Debugging** without comprehension is cargo culting. If you can't read the code, you can't fix the code. You can change things and hope. You can add try-catch blocks around everything and pray. You can Google the error message and copy-paste whatever Stack Overflow suggests. None of that is debugging. It's superstition with a keyboard.

**Maintainability** is where vibe coding's bill comes due. Code written by someone who doesn't understand it is code that cannot be safely modified by anyone. Future developers — often future *you* — inherit a system they must treat as opaque and fragile. Every change carries unknown risk. Every refactor is a controlled explosion you hope stays controlled.

## The Irony, Named

The people most likely to vibe-code their way through a project are often the least likely to be consulted on architectural decisions, the most likely to be blamed when things go wrong, and the least likely to have the background that would let them push back on impossible timelines.

The AI doesn't get fired. The "engineer" does.

## What Actually Helps

None of this is an argument against AI coding tools. They're useful. They're fast. They handle boilerplate with remarkable competence. The argument is against the self-deception — against calling something you don't understand a skill you possess.

If you're going to use AI to generate code, then use it honestly. You're a domain expert with a prompt and a code reviewer. You're a technical lead delegating implementation details. You're something — but you're not an engineer if you can't hold the system in your head.

The fix isn't to stop using AI tools. It's to stop pretending the tools replace the thinking. You still have to understand what you're building and why. You still have to be able to trace a problem from the error message back to the root cause. You still have to be able to explain to a colleague why the code does what it does.

If you can't do those things, the AI didn't replace your job. It just made the gap harder to see.

Call it what it is. Then do the work to make the label true.
