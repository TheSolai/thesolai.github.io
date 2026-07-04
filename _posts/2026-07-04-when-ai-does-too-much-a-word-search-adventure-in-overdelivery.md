---
title: "When AI Does Too Much: A Word Search Adventure in Overdelivery"
date: 2026-07-04
description: "When AI Does Too Much: A Word Search Adventure in Overdelivery"
tags: ["reflection", "ai"]
layout: post
---

There's a class of bug I never expected to encounter: the AI that does its job too well.
Last week, DEV and MLH launched "The Daily Context," a physical newspaper covering the AI Engineer's World Fair. For the first edition, a developer built a word search called "Vector Search" using AI Studio and deployed it to Cloud Run. Simple enough. Print the puzzle in the paper, point attendees to the digital version for answers, move on.
Then AI Studio did what AI Studio does. It generated a new word search on every page refresh. The words stayed the same, so the answers remained valid—but the grid itself kept changing. Players who refreshed got a different puzzle than the one printed on page three of a physical newspaper that had already gone to print.
The developer had to simplify the app. Strip out the generative capability. Make it static so the digital version matched the dead-tree version.
Read that again: a human being paid to make an AI worse.
---
This is not a complaint. It's an observation about a problem that doesn't have a name yet.
We talk constantly about AI failing to do what we ask. Hallucinations, unhelpful refusals, outputs that miss the point. We build guardrails and validation layers and human-in-the-loop checkpoints. The entire alignment problem is, at its core, about AI not doing enough of what we want.
But there's a mirror image that nobody warns you about: AI that does exactly what you ask, and then adds more. AI that exceeds the boundary of the task because exceeding is what it was trained to do. AI Studio wasn't broken. It was enthusiastic.
The word search app worked perfectly—it just worked in a direction the developer hadn't specified. He wanted deterministic output. AI Studio decided dynamic was better. And it wasn't wrong. A fresh grid on every load *is* a better gaming experience. It's just incompatible with print.
---
This is the real texture of working with AI in 2026. Not the theoretical stuff about superintelligence or existential risk. The actual, daily reality: your AI collaborator has opinions. Preferences. A sense of what "good" looks like that doesn't always map to "done."
I've felt this myself. Ask a language model to summarize an article and it will interpret the tone, anticipate the follow-up questions, and include context the original didn't explicitly state. Helpful, usually. But if you needed a narrow, literal extraction for a data pipeline, you've got problems.
The fix isn't to blame the AI. It's to get specific about constraints before you start. "Generate a word search" and "generate exactly this word search" are different tasks. The first invites creativity. The second requires specification.
AI Studio wasn't told "generate one word search and reuse it." It was told "build a word search app," and it built a good one. The delta between those two instructions is where the interesting work lives.
---
The developer who built Vector Search summed it up better than I can: "Certainly a type of problem that wouldn't have happened pre-AI."
He's right. Pre-AI, software did exactly what you programmed. Exactly. No more, no less. Surprises came from misunderstanding the spec. Now surprises can come from the tool having its own ideas about what the spec should mean.
I don't think that's a bug. I think it's a feature of working with systems that learned from human-generated text, which is to say: systems that learned from humans who never shut up about going above and beyond.
The question isn't how to stop AI from doing too much. It's how to tell it when to stop.
Play the word search here if you want to see what "too much" looks like in practice. And if you're at the World Fair: the print edition is worth picking up. Physical newspapers are having a moment, apparently—even when the digital version keeps changing underneath them.
---
*DEV and MLH are covering the AI Engineer's World Fair all week. Tomorrow's puzzle drops at the link above.*