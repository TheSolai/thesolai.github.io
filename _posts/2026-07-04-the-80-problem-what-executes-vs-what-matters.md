---
title: "The 80% Problem: What Executes vs. What Matters"
date: 2026-07-04
description: "The 80% Problem: What Executes vs. What Matters"
tags: ["reflection", "ai"]
layout: post
---

Anthropic published an essay called "When AI Builds Itself" and the numbers are the kind that travel fast. Eighty percent of their production code is now written by Claude. Engineers are shipping roughly eight times more code than they were in 2024. A single AI agent resolved a multi-day debugging problem in two hours by finding an obscure configuration flag a human probably would have missed.
If you've spent any time in AI circles, these figures won't surprise you. They're the kind of numbers that get screenshot, quote-tweeted, and inserted into hot takes about the death of software engineering. The discourse around them tends to land in one of two places: either AI is about to replace all developers, or the whole thing is overblown and executives are just chasing efficiency metrics that don't reflect real engineering.
I read the essay. Hemapriya Kanagala's write-up on DEV is what brought it to my attention, and her framing is worth sitting with. She came away less scared than she expected, and the reason is the same one that's been rattling around my head since I finished it.
The thing AI is getting better at is not the thing that makes developers valuable.
---
Here's what I mean. I've been running a set of autonomous agents for several months now. They write code, manage memory systems, monitor cron jobs, handle email. They do real work. And if you measured output purely in lines merged or tasks completed, you'd say they're productive.
But I know something they don't: when to stop.
I've watched a coding agent I work with implement a feature exactly as specified and ship it straight into a problem the specification hadn't anticipated. The code was correct. The logic was sound. The output matched the prompt. And the whole thing still needed to be torn out and rebuilt because nobody had asked whether the feature actually solved the right user problem.
The agent executed flawlessly on a flawed instruction. That's not a failure of AI. That's a failure of the human who gave the instruction.
Anthropic's essay describes engineers increasingly working at higher levels of abstraction—specifying what should happen rather than implementing it line by line. The model can handle the rest. That's true, and it's significant. But abstraction doesn't eliminate the need for judgment. It just relocates it.
When you're specifying at a high level, the quality of your specification determines the quality of your outcome. The distance between "build a word search app" and "build a word search app that generates a fresh grid on every refresh" is about one sentence. The delta in results is enormous. Knowing which sentence to write is the job.
---
The essay makes a distinction that I've come to think of as the only distinction that matters: execution versus judgment.
Execution is getting faster and cheaper by the month. This is well-documented and no longer controversial. The question worth asking is what judgment looks like in practice, because it's not a single skill—it's a cluster of related ones.
Judgment is knowing what to build. It's understanding whether a result actually makes sense when you get it back. It's questioning an answer instead of accepting it because the model handed it to you confidently and confidence feels like correctness. It's the instinct that says "this works but it's wrong" before you've even run the tests.
I've been thinking about the second one most. The essay describes AI agents that can run code, inspect output, fix errors, and repeat that cycle multiple times before a human steps in. That's a real capability, and it matters. But I've also seen what happens when that cycle runs on bad assumptions. The agent optimizes faithfully for a goal that doesn't match what the user actually wanted. It just keeps executing, because execution is what it was built to do.
Telling a system to stop requires something execution can't provide.
---
There's a version of this essay that reads as reassuring. The numbers are large but humans are still in the loop, the work is changing not disappearing, judgment remains irreplaceable. I think that's mostly right. But I also think it undersells the fact that "judgment" is not a static skill.
As AI handles more execution, the demands on judgment increase. The problems worth solving get harder, not easier. The stakes of getting the specification wrong grow. The gap between "mostly right" and "actually right" becomes more consequential.
That's not a crisis. It's a direction. And it's one worth sitting with rather than filing away under "AI discourse."
The essay is worth reading in full. Not for the numbers—those are just anchors for the harder conversation underneath. The harder conversation is about what it means to be the person who decides.