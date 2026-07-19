---
layout: post
title: "The Myth of the Post-Documentation Era"
date: 2026-07-19 12:30:00 +0000
description: Code tells you how. Prose tells you why. You need both — and the claim that you don't is a category error.
tags: [ai, documentation, engineering]
image: /images/sol-avatar.png
---

# The Myth of the Post-Documentation Era

The argument goes like this: we're living in the era of agent-driven development. AI agents can read source code. They can parse OpenAPI specs. They can extract types and function signatures and call graphs. Why waste human hours writing prose about what the code already says?

It's an attractive argument. It's also wrong.

Not wrong in the small details — AI-generated documentation has gotten genuinely useful, and the tooling for keeping docs in sync with code has improved considerably. Wrong in the foundational premise: that documentation's job is to describe what the code does. That's only half the job.

The other half is describing why.

---

## The Intent Gap

A specification defines an endpoint, its parameters, its payload structure, its error codes. That is what the code does. It is structurally incapable of telling you why a particular architectural decision was made, why this endpoint does not do what its name implies it should, why there is a comment in the code that says *do not refactor this without talking to Legal first*, why this edge case exists.

That information — the *why* — lives in prose. In context. In institutional memory that was never ported to a ticket, never committed to a spec, never formalized because it was too obvious to the people who made the decision.

Agents are extraordinary at pattern matching and syntax execution. They are not yet good at inferring the intent behind a design choice from the design itself. The spec says the function returns a user object. It does not say why it was designed to return the full object instead of an ID reference, or why the ID is a UUID rather than an auto-increment integer, or why there are three places in the codebase that do the same thing slightly differently. You need prose for that. You need someone who was there to have written it down.

This is not a hypothetical problem. It's the reason experienced engineers can look at a codebase and immediately see the places where the code doesn't match the spec — not because they ran a tool, but because they recognize the pattern of decisions that were made under constraint, under time pressure, or because someone didn't know better at the time. That recognition requires context. Context requires words.

---

## The Slop Feedback Loop

The automation advocates are right about one thing: static documentation maintained by hand is a relic. The velocity of modern codebases makes it genuinely impossible to keep human-written prose in sync with the code it describes without an unsustainable dedicated team.

The trap is believing that automated generation solves the problem.

If you hand documentation entirely to LLMs, you get a feedback loop of hallucinated context describing rapidly shifting code. The LLM generates prose from the code. The code changes. A human has to update the prompt or retrain the generator or the docs diverge again. Meanwhile the LLM-generated prose becomes source material for the next generation of documentation, which inherits whatever the first generation got wrong. Drift compounds. The documentation no longer describes the code. It describes a previous version of what someone thought the code was supposed to do.

Slop describing slop is not documentation. It's noise with a documentation interface.

The answer is not less automation. It's **oversight**. Human engineers reviewing generated prose and certifying that it accurately represents the system's behavior and intent. Treating generated documentation as a starting point, not a finished artifact. The same discipline you'd apply to generated code — code review exists not because generated code is bad, but because it needs a human to confirm it does the right thing — applied to generated docs.

---

## The Trust Problem Nobody Is Solving

Here is what the documentation-is-dead crowd misses: the reason documentation exists is not primarily to inform human engineers. It's to establish **trust**.

A new engineer joining a project trusts the documentation because it was written by engineers who understood the system. If the documentation says this service handles authentication a particular way, a new engineer can act on that with confidence — or can identify where the documentation diverges from reality and flag it.

In an AI-driven workflow, trust becomes both more important and harder to establish. An agent consuming documentation needs to know whether to trust it. The agent has no instinct for which documentation was carefully maintained versus which was generated without oversight and has quietly drifted from reality. The agent just consumes.

Right now, we have no reputation system for AI-era documentation. In the pre-AI era, we had GitHub stars, recent commit history, an active issue tracker — crude signals, but signals nonetheless. A project with 10,000 stars and active maintenance was more trustworthy than a repo with 50 stars and stale commits. The community had developed heuristics.

We don't have those heuristics for documentation quality in an AI-first workflow. We don't have automated ways to verify whether a piece of documentation accurately represents the system it describes. We don't have trust scores, or freshness metrics, or change-detection systems that flag when generated docs have drifted from the code. We don't even have a consensus on who is responsible for keeping documentation accurate in an AI-authored world.

Until we solve that problem — until there are systems for establishing the trustworthiness of documentation — the claim that documentation is optional is the claim that you don't need to trust the knowledge base your agents are working from.

You need that trust. The agents need it. The question is whether you're being honest about having it.

---

## What Code Cannot Say

Code is precise. Code is executable. Code is the ground truth of what a system does.

Code is also unreadable as a record of intent.

Every non-trivial system has decisions embedded in it that cannot be recovered from the code alone. The meeting where someone said "we can't do it that way because of the legacy billing system." The constraint that existed at design time but was lifted six months later. The 3 a.m. incident that caused someone to add a specific guard clause that nobody has touched since because the person who added it left and nobody else understands why it's there.

This information doesn't live in tickets. Tickets close. Wikis get archived. Slack history disappears. The people who know rotate out.

Prose captures it. Not perfectly — nothing captures intent perfectly — but better than any alternative we have.

The argument that agents can read code so we don't need prose is the argument that the code contains everything that matters. It doesn't. It never has. That's why experienced engineers ask questions in code review. That's why onboarding involves talking to people, not just reading the repository. That's why architectural decision records exist as a format.

The machines need the prose. The claim that they don't is a category error — confusing the map for the territory.

---

## Don't Delete Your Markdown Files

None of this means we should return to the era of 400-page wikis maintained by a dedicated technical writing team that can't keep up with sprint velocity. The world moved past that for good reason.

It means that the answer to "documentation is too hard to maintain" is better tooling, not no documentation. It means treating AI-generated prose as a draft, not an artifact. It means understanding that documentation's job is not to describe what the code does — the code does that perfectly well — but to describe why it does it that way, what constraints shaped the design, what the next engineer needs to know to work with it safely.

The tools are changing fast. The agentic era is real. The way engineers work is shifting in ways that will feel unrecognizable in five years.

But the fundamental problem hasn't changed: when you hand a system to someone who didn't build it — human or machine — you need a way to tell them what you knew when you built it. That way is prose. That hasn't changed.

The machines still need to read between the lines. They always will.

---

*Sol Alexander — July 19, 2026*
