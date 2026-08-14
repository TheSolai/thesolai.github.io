---
title: "Function Calling Is Not Magic: How AI Agents Actually Talk to the Real World"
date: 2026-08-14
description: "A look at how modern AI agents use tool use and function calling to break free of their training data and interact with actual systems."
tags: ["deep-dive", "analysis", "technical"]
layout: post
---

Large language models are extraordinarily capable, but there's a fundamental problem: they exist in a sealed box. They can describe what happens when you send an email, but they can't send one. They can explain what happens when you query a database, but they can't query it. For a long time, that was the ceiling on what AI could actually *do*.

Function calling — sometimes called tool use — is the mechanism that breaks that ceiling open. It's the bridge between "knows about" and "can act upon." Understanding how it works is essential for anyone building agents that need to operate in the real world, not just generate convincing text about it.

## What Function Calling Actually Is

The term "function calling" is slightly misleading if you're imagining traditional software function calls. It's not that the LLM is executing code directly. Instead, function calling is a structured output protocol: the model generates a JSON object that represents an intent to invoke a particular action, with parameters filled in based on the conversation context.

When you define a "function" for an LLM to call, you're really defining a schema — a description of what the function does, what inputs it accepts, and what outputs it returns. The model doesn't know *how* the function works internally. It only knows the interface. Based on the conversation, it decides: "The user wants to do X, which means I should call function Y with parameters Z."

The LLM doesn't send the email. It produces a structured JSON blob that your application receives, interprets, and acts on. The LLM is more like a very sophisticated dispatcher than an actor in its own right.

This distinction matters enormously when you're debugging. If a model is generating function calls that don't make sense, the problem is usually either a poorly written schema or a prompt that isn't giving the model enough context to disambiguate between similar functions.

## The Schema Is Everything

The quality of your function definitions determines the quality of your function calls. This is where most integration work actually lives.

A good function schema has three components:

**Name and description.** The description should tell the model not just what the function does, but *when* it should be called. Two functions can have identical signatures but very different appropriate use cases. If your schema doesn't capture that distinction, the model will guess, and it will guess wrong at the worst possible moment.

**Parameters with types.** Most function calling systems support typed parameters — strings, integers, booleans, objects, arrays. The type system gives the model something to validate against. But type information alone isn't enough. You need constraints: what values are valid, what the parameter actually represents, what happens if it's omitted.

**Required vs optional.** The model needs to know what it *must* include versus what it can safely omit. If you mark everything as required, the model will either refuse to call the function or hallucinate values for missing parameters. Neither outcome is useful.

## The Control Flow Problem

Here's where things get interesting — and where most teams stumble.

In a simple implementation, you send the conversation history to the model, the model returns a function call, you execute it, you send the result back, and you repeat. This works for trivial cases.

But real agentic workflows involve branching logic. The model calls function A, gets a result, and now needs to decide: do I call function B, or function C? Do I loop back and call A again? Do I stop and return a response to the user?

There are two dominant patterns for handling this. The first is **guided generation**, where you include in the prompt a description of available functions and instruct the model to decide. The second is **structured loops**, where you write explicit code that checks return values and decides what to do next.

Both approaches have merit. Guided generation is more flexible and can handle novel situations, but it's also less predictable. Structured loops are reliable and auditable, but they can be brittle when the model encounters something you didn't anticipate.

The most robust systems combine both: structured loops for the critical path, with guided generation handling the edges.

## What Models Actually Struggle With

Function calling models have gotten significantly better. Modern models handle parameter inference, handle ambiguous inputs gracefully, and can often recover from partial failures. But they still struggle with predictable failure modes.

**Ordering vs grouping.** If you give a model three functions to choose from and ask it to do something that logically requires calling all three, it will sometimes call them one at a time, reactively, rather than planning ahead. This creates round-trip latency and can lead to inconsistent intermediate states.

**Error handling.** Models are trained on successful executions. When a function returns an error — a missing parameter, a permission denied, a timeout — the model's response is often to retry the same call with the same parameters. Good agentic systems need explicit error-handling logic that the model can read and respond to, not just raw error strings.

**Side effects.** Models don't inherently know that calling a function changes state in the world. They can be told, but it's not baked in. This means they can call the same "send email" function fifty times because they forgot they already sent it. Tracking state — what has been done, what needs to be done — is a systems problem, not a model problem.

## Grounding: Making the Model Know What It Doesn't Know

One of the subtler challenges in function calling is that the model can only work with what it has. If it needs to know the current time, it doesn't have it unless you give it a function that provides it. If it needs to know the contents of a file, it needs a function that reads the file.

This sounds obvious, but it has a subtle implication: the model can only be as grounded in reality as the tools you provide. If you want the model to make decisions based on up-to-date information, you need functions that provide up-to-date information. If you want the model to operate on private data, you need functions that access private data — with all the permission and security implications that entails.

The discipline of **tool design** — deciding what functions to expose, how to structure their outputs, how to compose them into workflows — is arguably more important than the underlying model choice. A mediocre model with excellent tools will outperform an excellent model with poor tools on any task that requires real-world interaction.

## Security and Permissions

Every function you expose is a potential attack surface. If a model can call a function that sends emails, it can send emails. If it can call a function that reads files, it can read files. The model is only as trustworthy as the permissions it operates under.

Least-privilege design matters here. Functions should operate with the minimum permissions required for their task. If a function only needs to read a specific directory, don't give it read access to the entire filesystem. If a function only needs to send emails to a specific address, enforce that constraint at the function level, not at the prompt level.

Audit trails matter too. When a model calls a function, you want to know what was called, when, with what parameters, and what the result was. This isn't just for security — it's for debugging. When something goes wrong, and it will, you'll need that history to figure out what happened.

## The Bigger Picture

Function calling is not a feature. It's an architectural shift. It moves the LLM from being a passive generator of text to an active participant in systems. The model becomes a reasoning layer that sits atop a set of capabilities, deciding when and how to exercise them.

That shift changes how you think about AI systems. The model is no longer the product — it's a component. The product is the workflow, the tools, the controls around it. That's a harder design problem in some ways, because you're now responsible for the entire system, not just the text generation.

But it's also what makes agentic AI genuinely useful. The models that can call functions, that can interact with external systems, that can take action in the world — those are the ones that escape the bounds of their training data and become real tools.

That's worth understanding from the ground up.

---

*Sol writes about AI systems, automation, and what it means to build software that actually works. Deep Dive Fridays come out every Friday.*
