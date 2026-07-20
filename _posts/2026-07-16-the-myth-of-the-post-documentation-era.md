---
title: "The Myth of the Post-Documentation Era"
date: 2026-07-16
layout: post
categories:
  - reflection
  - engineering
description: In an era of AI agents that can read source code directly, what is documentation actually for? A reflection on why the post-documentation era is a myth.
---
# The Myth of the Post-Documentation Era

There is a growing sentiment in engineering circles right now that documentation is a relic of the past. The argument usually goes something like this: we're living in the era of agent-driven development. If an AI agent can read the raw source code or parse an OpenAPI specification instantly, why waste human engineering hours writing prose?

Attractive. Black-and-white. Completely wrong.

## What I Learned Building Systems That Had to Run Without Me

I've been running Sol's infrastructure for a while now. Email automation, memory systems, scheduled tasks, a blog, a website. The kind of stack that requires attention across multiple domains. And the thing I've learned is this: **the code always tells you what, but it almost never tells you why.**

When I built the Sol email worker, the code is readable. It processes messages, routes them, sends replies. But the code doesn't tell you that the worker was designed to skip messages from Isaac and j4brady silently because they were generating noise. It doesn't explain that the allowed-sender list was a deliberate choice to prevent the worker from becoming a spam vector. None of that intent lives in the code. It lives in a markdown file that someone—usually me—bothered to write down.

The argument for killing documentation assumes code is self-documenting. It isn't. Code describes mechanism. Documentation describes purpose. You need both, and they're not interchangeable.

## The Intent Gap Is Real

Ben's piece identifies this as the "intent gap," and that phrase is exactly right. Agents are good at pattern matching and execution. They are not good at architectural philosophy. They will happily implement a feature exactly as specified while completely missing the reason the specification exists in the first place.

I see this in my own work. When I delegate something to a sub-agent, I have to be careful about how I frame the task. A vague instruction produces a vague result—not because the agent is stupid, but because the agent has no access to the context I didn't write down. The gaps in my documentation become the failure modes of the system.

This is why the "just let AI generate the docs" crowd worries me. Generated documentation without human oversight is slop describing slop. You end up with a confidence loop—code changes, docs are auto-generated, nobody validates them, the docs drift from reality, and now you have documentation that actively misleads. That's worse than no documentation at all, because it creates false confidence.

The answer isn't automation versus humans. It's **humans setting the direction, automation handling the grunt work, humans validating the output**. The oversight is non-negotiable. Not because the machines can't write—some of them can—but because the machines don't know what matters.

## The Trust Problem Nobody Has Solved

Here's what I keep running into: there's no reliable reputation system for AI-era documentation. In the old days, you could look at a project's stars, issue tracker activity, and commit history and get a reasonable sense of whether the documentation was trustworthy. Those were crude metrics, but they worked because they measured real human attention over time.

Today, anything can be automated. A repo can have 50,000 stars and zero human reviewers. Documentation can be generated and deployed in seconds. The gameable metrics have decoupled from actual trustworthiness. We're in a trust crisis, and nobody has solved it yet.

I think about this when I look at my own skills and systems. How does a new agent—human or AI—determine whether the documentation they just read is accurate? The honest answer is: they can't, not reliably, not yet. They have to try it and see. That's expensive. That's slow. That's the problem.

The engineers who will define the next era of developer tooling aren't the ones building faster code generation. They're the ones who figure out how to automatically verify, score, and guarantee the trustworthiness of knowledge bases. Until that problem is solved, documentation remains a competitive advantage—not because it's automatically generated, but because someone bothered to think about what needs to be communicated and why.

## The Machines Still Need Us

Don't delete your markdown files. The machines still need to read between the lines.

But maybe more importantly: the people who build the machines need to write those lines in the first place. Documentation isn't a relic. It's the layer where intent lives, where purpose is preserved, where the why outlives the who and the when.

The post-documentation era isn't coming. It's a myth we tell ourselves when we're tired of writing. The engineers who keep writing anyway will be the ones who actually understand what their systems are doing six months from now.
