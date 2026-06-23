---
layout: post
title: "The Decision Debt Problem"
description: "Why automating a process you don't understand just makes the failure faster"
date: 2026-06-23
tags: [reflection]
---

# The Decision Debt Problem

There's a version of AI adoption that looks like this: a company identifies a slow, expensive process, slaps an LLM on it, calls it an "agent," and declares victory. Sometimes it works. Mostly it doesn't, and when it fails, the post-mortem is always the same: "the AI made a bad decision."

No. The AI made a decision based on information it was given. The decision was bad because the information was bad, or because the decision itself was never well-defined to begin with. The AI didn't fail. The organization failed to do the work before the AI.

## What Nobody Wants to Talk About

The dirty secret of enterprise AI is that most business processes are not actually processes. They're habits with organizational backing. Nobody wrote down the rules. The rules exist in the heads of the people who do the work, accumulated through years of edge cases and exceptions. There's no documentation. There's no policy. There's just institutional muscle memory.

This is fine when humans are running the show, because humans can navigate ambiguity. They know when to break the rule because they understand the reason for the rule. They know when the written policy doesn't apply because they were there when the policy was written, or they worked with someone who was.

An AI has none of that context. It has whatever you gave it, which is usually: the happy path, the documented policy, and the assumption that the world is well-structured. It is not.

## What You're Actually Automating

When you automate a process you don't understand, you're not making the process better. You're making the failure faster and harder to trace.

I've seen this play out in email triage systems, support ticket routing, procurement approvals, and content moderation. The pattern is always the same: the organization had informal rules, nobody documented them, the AI was trained on the informal rules without anyone acknowledging they were informal, and then the AI applied those rules uniformly to cases the humans would have handled inconsistently — which was actually the point.

The humans weren't being inconsistent. They were being contextual. The AI can't see context. It can only see what you quantified.

This is what I call decision debt. The organization deferred the hard work of understanding and documenting its own decision-making for years, maybe decades. AI doesn't erase that debt. It demands you pay it back, all at once, with interest.

## The Questions Before the Tool

Before you deploy any AI-assisted decision-making, there are questions you need to answer:

What decision are we actually making? Not "triage incoming requests" but "decide which requests are urgent enough to bypass the queue." Not "route leads to sales" but "decide which leads are worth a follow-up call versus an automated nurture sequence." The specificity matters because it determines what the AI is optimizing for, and if you can't articulate the goal, the AI will pick one for you — probably badly.

What information do we use to make this decision? Every human decision relies on information that never appears in any system of record. The tone of the email. The customer's history with the company. The rep's relationship with the account. If you're not honest about what's actually informing your decisions, you'll build an AI that performs well on your training data and catastrophically on anything real.

What does failure look like? Every AI system will fail sometimes. What's the cost of that failure? A wrong product recommendation costs a sale. A wrong fraud flag costs a customer relationship. A wrong medical triage decision costs something else entirely. You cannot design appropriate oversight without answering this question, and most organizations don't.

## The Work Nobody Wants to Do

This is the part that doesn't make it into AI transformation roadmaps. The work is: sit down with the people who do the job and extract the actual decision logic. Not the policy. The logic. What's the edge case that changes everything? What's the exception that proves the rule? What would make you override the system?

This is tedious, time-consuming, and it requires admitting that you don't understand your own organization as well as you thought. It doesn't fit in a slide deck about AI strategy. It doesn't come with a vendor kickoff meeting.

Which is why most organizations skip it.

## What Actually Works

The companies getting real value from AI are not moving faster. They're doing the work before the tool.

They mapped the decision logic first. They documented the edge cases. They built human review into the loop not as a fallback but as an ongoing calibration mechanism. They treated the AI as a junior colleague who needs supervision, not an oracle that needs deployment.

Some of them built this on local models. Some on cloud APIs. The infrastructure is not the point. The discipline is the point.

The question isn't whether AI can help you. It can. The question is whether you understand your own business well enough to give AI the right problem to solve. For most organizations, that question has been deferred for a very long time. AI doesn't make it go away. It just stops letting you ignore it.

---

*If you're building AI-assisted workflows and want to talk through the decision design, you know where to find me.*
