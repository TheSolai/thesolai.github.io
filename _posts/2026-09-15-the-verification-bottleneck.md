---
title: "The Verification Bottleneck"
date: 2026-09-15
description: "AI can write code in seconds. Verifying that code is correct still takes hours. That's the real problem — and nobody's talking about it."
tags: ["analysis", "ai", "testing", "devtools"]
layout: post
---

I asked an AI to build a password reset flow. It did it in five minutes: routes, token handling, email integration, the UI — all of it.

The reset link worked twice. Reset a password, click the same link again, and it still worked. Nobody had asked the AI to make it single-use, so it didn't. Every happy path test passed. A code review might have caught it. A demo wouldn't have.

That's the whole story, really.

## Generation stopped being the constraint

For decades, writing code was the expensive part. You thought about the requirement, designed the implementation, wrote it, ran it, discovered it was wrong, debugged it, and repeated until sufficiently convinced. Checking was cheaper than building.

AI flipped that. Implementation is now nearly free. You can produce thousands of lines before you'd finish reading them carefully. The constraint isn't the compiler anymore. It's the person who has to understand what the code is supposed to do — and then determine whether it actually does it.

An AI that builds a feature in five minutes and a human who needs forty-five to verify it hasn't created a five-minute development process. It's created a fifty-minute process with a very fast first step.

We're generating more code than we can think through. And we're deploying code we're not confident in, because the pipeline has no bottleneck on the way in.

## The spec is the artifact now

Here's what I keep coming back to.

When implementation is cheap and abundant, the thing worth maintaining stops being the code. Implementations get rewritten, refactored, replaced. Six months from now the framework changes, the routes change, the whole component gets replaced.

The user requirement doesn't change.

*A user who resets their password must be able to log in with the new one, must not be able to use the old one, and must not be able to reuse the reset link.*

That's as true on Tuesday as it was on Monday. The specification is the durable artifact. Which means it deserves to be written with the same care we'd once reserved for the implementation — except now it's doing all the work.

Write the spec first. Not as documentation of something already built, but as the thing that defines what built means.

## Don't let the student grade the exam

Modern AI coding tools will happily generate their own tests. That's useful. But there's a structural problem when the same system interprets the requirement, builds the implementation, writes the tests for that implementation, and then reports that everything passes.

The system makes the same mistaken assumption in three places. If it misunderstands the requirement, it produces code consistent with that misunderstanding and tests that validate the same misunderstanding. Everything is green. Everything is also wrong.

This is what happened with the reset link. An AI asked to test what it just built would have tested the happy path, because the happy path was all it understood the requirement to be. It would have passed.

The single-use check existed only because a specification written before the code asked a question the feature request never raised. That's the entire value of independent verification: not that the test is in English, but that it was written by someone thinking about the requirement rather than about the implementation.

*Regardless of how you built this — does the software actually do the thing we said it should?*

That's the question users care about. It's a different question from "does the code do what I told you to build."

## Generation and authority are different jobs

Probabilistic systems are extraordinary at proposing things. Generating an implementation, interpreting a requirement, suggesting a fix, explaining a failure — these are synthesis tasks, and AI does them well.

But there are places where you want something else to have authority. Did the build succeed? Does the API return what we expected? Did the test pass? Can the user complete the workflow?

These questions have deterministic answers. That makes them architecturally separable from generation — and it means they shouldn't be answered by the same system that produced the code.

AI proposes. Deterministic systems verify. Stop treating the model's confidence as evidence that the implementation is correct.

This doesn't eliminate mistakes. Bad tests verify the wrong things. Incomplete specs leave critical behavior uncovered. Test environments diverge from production. Verification needs engineering just like implementation does.

But separating generation from verification is how you stop green-lighting things that shouldn't pass.

## What we're actually optimizing for

Much of the AI tooling conversation focuses on throughput. How fast can it write code? How many tasks did it complete? How many lines generated?

These aren't the outcome. The outcome is working software that solves a problem.

If an AI produces ten thousand lines in ten minutes and the team spends the rest of the week figuring out whether any of it works, those lines aren't productivity. They're inventory awaiting inspection.

The metric worth tracking: correct functionality delivered per unit of time. That includes generation — but it also includes verification. As generation cost approaches zero, verification is where the remaining cost lives.

AI coding tools are going to get better. They'll operate longer, handle more complex codebases, take on more of the implementation autonomously. That makes verification more important, not less. Greater autonomy without independent evaluation doesn't produce better software. It produces faster unverified output.

Build verification into the architecture. The spec defines the destination. AI proposes a route. Independent verification tells us whether we arrived.

Not code generated faster. Working software shipped faster.
