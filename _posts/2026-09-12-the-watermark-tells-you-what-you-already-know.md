---
title: "The Watermark Tells You What You Already Know"
date: 2026-09-12
description: "The Watermark Tells You What You Already Know"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Anthropic signed the EU AI Act's transparency code. Claude's outputs now carry an imperceptible statistical watermark. The internet reacted as the internet does — panic, hot takes, think pieces about the end of undetectable AI text.
Then the documentation got read. And the picture that emerged was more interesting — and more limited — than the initial panic suggested.
## What the Watermark Actually Is
The system embeds a subtle statistical bias into token selection during generation. Not visible characters. Not weird spaces. A pattern that emerges across enough tokens — long enough text, statistically significant sample — and can be detected by tools with appropriate access.
It survives copy-paste. It survives some editing. It does not survive paraphrase, translation, or sufficient human revision. The article notes this clearly:
*watermark detected ≠ AI wrote everything*
*no watermark detected ≠ human wrote everything*
A human writes something, hands it to Claude for grammar correction and polish, and the output carries a watermark. The ideas, voice, and most of the text are human. The signal is present. Conversely: someone generates AI text, edits it heavily, translates it, and the signal disappears entirely. The origin is machine. The output isn't.
So the thing the internet is arguing about — *is this the end of undetectable AI text?* — was already answerable from the documentation. No. It's the beginning of an imperfect, noisy signal that tells you something probabilistic about origin, and almost nothing definitive about authorship.
## The Part Nobody Is Talking About
What struck me about the article was not the technical mechanism. It's that Google has had SynthID Text since 2024. OpenAI has had the technology developed but hasn't deployed it for text. Anthropic is late to a party that's already been running.
The interesting question isn't who has the watermark. It's why the conversation keeps arriving at detection instead of disclosure.
The EU AI Act's actual goal is stated clearly: make AI-generated content machine-detectable and, in specific contexts, transparent to users. The target is things like deepfakes and content concerning public interest. The exception — where no disclosure is required — is content that has undergone human review with editorial control and a named person or entity holding editorial responsibility.
That's the part worth sitting with. The regulation was designed around disclosure, not detection. The watermark is a tool for provenance, not proof. It tells you something about where the text came from if you know how to read it, and it tells you nothing conclusive if someone motivated to hide the signal has touched the output.
## What This Changes
Practically? Very little for most users. Detection tools will remain imperfect. The noise will remain high. Someone determined to pass AI text as human can do so with enough editing to strip the signal. Someone who used AI to polish prose they wrote will carry a signal they didn't earn and can't remove.
The harder question — one the article hints at but doesn't pursue — is what we're actually trying to accomplish. If the goal is transparency about AI involvement in content creation, the watermark is a rough step in that direction. If the goal is certainty about whether a human or a machine wrote something, the watermark can't deliver that and was never going to.
The regulation draws a line around disclosure: when AI is used without meaningful human review, say so. That's a behavioral requirement, not a technical one. The watermark is the evidence of use. The policy is what you do with the evidence.
Whether that policy actually changes behavior at scale is a different question. And the answer depends far more on incentives than on the precision of the detection mechanism.
*The watermark is not a lie detector. It's a provenance signal. Knowing where something came from is useful. Knowing what it means is still your job.*