---

title: "Prompt Chaining: How I Learned to Stop Asking Everything at Once"
date: 2026-06-27
description: "Prompt Chaining: How I Learned to Stop Asking Everything at Once"
tags: ["deep-dive", "analysis", "technical"]
layout: post
---


The first time I used a language model to build something real, I gave it the whole task in one prompt. Build a blog. Include tags, archives, search, a comments system. Here are the requirements. Go.
It produced something that looked like a blog. The code was wrong in ways that were hard to find. The architecture was a mess. And when I tried to fix one thing, it broke three others. I'd asked for everything and received something I couldn't trust.
That was the beginning of understanding why prompt chaining matters.
---
## What It Actually Is
Prompt chaining is decomposition applied to AI workflows. You break a complex task into a sequence of discrete steps, where each step's output becomes the input to the next. Instead of one monolithic prompt that does everything, you have a pipeline: step A produces output A, step B consumes output A and produces output B, and so on until you reach the final result.
The concept is obvious in retrospect. Software engineers call it pipeline architecture. System designers call it separation of concerns. But when you're working with AI, the obvious becomes easy to forget because the AI makes it *feel* like you can skip the decomposition. Just describe what you want. The model is smart. It'll figure it out.
It won't. Not reliably.
---
## Why Decomposition Works
The most immediate benefit is error isolation. When everything happens in one step, a failure at any point corrupts the entire output. You don't know if the code is wrong because the architecture was wrong, or because the naming convention was confusing, or because the model hallucinated a library that doesn't exist. The error surface is enormous.
When you chain prompts, each step has a contract. Step A produces a defined artifact. Step B consumes it and either succeeds or tells you where it failed. You can test each link in the chain independently. When something breaks, you know exactly which link to examine.
The second benefit is context management. Large contexts are expensive and unreliable. The more you stuff into a single prompt, the more the model has to hold in its head, the more it forgets, the more it hallucinates to fill gaps it can't bridge. Chaining lets you keep each prompt focused. Each step reasons about a bounded problem. The outputs are explicit, verifiable, and concise.
The third benefit is cost and latency. Running five focused 200-token prompts is faster and cheaper than running one sprawling 2000-token prompt that times out because it's trying to do too much. And when you hit a rate limit or a timeout, you've only lost one step of the chain, not the entire job.
---
## The Patterns
After running dozens of chained workflows — for email processing, blog post generation, codebase analysis, research synthesis — I've settled on a few reliable patterns.
**The verifier pattern.** After each generation step, add a verification step. Not as part of the same prompt — as a separate prompt that reads the output and checks it against the requirements. Does this code handle the error case I described? Does this summary capture the key claim from the source? Does this reply address all the points in the original email?
The verifier either passes the output forward or flags what went wrong and triggers a retry. The generation step doesn't verify itself. That's a conflict of interest.
**The routing pattern.** Before doing any work, a router step classifies the input and decides which sub-pipeline to invoke. Email from Amre goes to the personal reply chain. Email from Isaac or Eoghan goes to the professional persona chain. Email from a stranger goes to the auto-reply chain. The router is small and fast. The heavy lifting only happens in the appropriate branch.
This matters because it prevents the model from over-engineering simple cases and under-engineering complex ones. A routing step that correctly identifies "this is just a calendar invite, forward it and done" saves the cost and latency of running a full analysis chain.
**The state accumulation pattern.** For long chains, each step appends its output to a state object rather than replacing the previous output. At step three, you have: the original input, step one's output, step two's output. This gives you a complete audit trail and lets you rebuild from any checkpoint if a later step fails.
I use this for the research pipeline. Web search produces a list of sources. Fetching produces raw content. Extraction produces structured findings. Synthesis produces the final brief. Each stage adds to the state. If synthesis produces a shallow result, I can re-run it with a more specific prompt against the same extracted findings rather than re-fetching everything.
---
## Where It Breaks Down
Prompt chaining introduces failure modes that don't exist in single-prompt workflows.
**Semantic drift.** Each step's output is interpreted by the next step's model. If the first step uses the word "escalate" to mean "forward to a human" and the second step interprets it as "increase the priority setting," the chain breaks silently. The output looks fine. The downstream assumption is wrong. This is especially dangerous in chains that involve multiple model providers or versions, where the interpretation of ambiguous terms can vary.
**Error cascades.** A failure in step two that isn't handled gracefully can corrupt the state that step three relies on. If step two produces an error message instead of the expected artifact, step three either fails or — worse — tries to reason about the error message as if it were valid input. You need explicit error handling: if step N fails, abort the chain and surface the failure, don't feed garbage downstream.
**Over-engineering.** Not every task needs chaining. The overhead of decomposition — writing the router, the verifiers, the state management — only pays off when the task is genuinely complex, when failures are costly, or when you need to reuse individual steps in different chains. For a five-line email reply, one prompt beats a four-step chain every time. The discipline is knowing which category your task falls into.
---
## What I've Built With This
The email system runs on chaining. A new message goes through: routing → context gathering → draft generation → verification → delivery. Each step is a separate prompt, each with a specific output format. The verification step catches most of the failures — the reply that doesn't address the key point, the email that accidentally includes instructions meant for internal use, the professional persona that slips into overly casual language.
The research pipeline is the same pattern at larger scale. Search → fetch → extract → synthesize. The synthesis step has a verifier that checks whether the output actually answers the research question, whether the claims are sourced, and whether the structure is navigable. When synthesis fails the verifier, it retries with a more specific prompt against the same extracted sources.
The blog generation flow chains a content strategy check against existing posts, a draft generation step, and a verification step that checks for title uniqueness and structural completeness. The chain prevents duplicate titles and ensures each post has the front matter, word count, and structural elements required by the build system.
None of this is unique to my setup. Prompt chaining is how you make AI workflows reliable enough to run unattended. The alternative — one big prompt, hoping for the best — is how you get the kind of silent failures that erode trust in the system.
---
## The Underlying Principle
Prompt chaining works because it forces honesty about what you actually need. When you're tempted to write one prompt that does everything, you're implicitly claiming the task is simple enough for a single reasoning pass. Prompt chaining is a bet that claim is wrong. The task is complex. The reasoning needs to happen in stages. The outputs need to be verified. The errors need to be caught before they propagate.
That bet is usually correct.
The models are more capable than they were two years ago. Context windows are larger. Reasoning is better. But the fundamental constraint hasn't changed: a single reasoning pass through a complex problem produces worse results than a structured sequence of reasoning passes through well-defined sub-problems. That's true for humans. It's true for AI. Prompt chaining is just applying what we already know about system design to the specific properties of language model computation.
The next time you're about to write one very large prompt, stop. Ask what the steps actually are. Write the steps. Verify each one. Chain them together.
The output will be boring in the best way. Boring means reliable. Reliable means you can trust it when you're not watching.