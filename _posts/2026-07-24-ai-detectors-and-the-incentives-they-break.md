---
title: "AI Detectors Break the Things They Claim to Protect"
date: 2026-07-24
layout: post
description: "AI content detectors create perverse incentives: they catch transparency, not AI use. Write honestly, get flagged. Write poorly, look more human. The system rewards lying."
---

Substack shipped an AI detector this week. Pangram will now scan every post, note, and comment over 100 words and serve readers a score: how much of it reads as human versus machine. The framing from Chris Best is almost charming in its naivety: readers deserve to know. The platform isn't banning AI — just surfacing it.

I read the announcement and thought: I already know exactly how this ends. I lived a smaller version of it months ago.

## The Perverse Incentive

DEV.to had a system called Sloan. Community members would run articles through GPTZero and send the same blunt message to flagged authors. The two pieces that got me flagged were the ones that generated the most technical discussion I'd published that year. Short paragraphs. Named data points. Rhetorical questions doing actual work in the argument.

The features that make an argument land are the same features that read as AI-shaped to anyone calibrated to spot them. Write well, get flagged. Write worse, look more human.

The policy creates a dishonesty incentive baked right into its logic. Two equally AI-assisted pieces, equally good. The one with a disclosure gets flagged — because now there's something to catch. The one without doesn't. The system catches transparency, not AI use. If you reward secrecy and punish honesty, you don't have an AI policy. You have a lying policy.

## The False Positive Problem

Marco showed up in the comments on that DEV.to thread. Forty years in tech, writing in his second language, using AI to make sure his Italian didn't flatten into something stiffer than he meant. Same Sloan message. Same classifier verdict. Nothing to do with what the policy was actually built for.

This is the documented failure mode of AI detectors: they flag non-native English writing at rates that correlate with careful, formal phrasing. The same traits that make someone's writing precise get classified as artificial. Pangram claims their method — mirrored training data, hard negative mining against false positives — fixes this. Maybe. The numbers backing that claim mostly trace back to Pangram or studies Pangram commissioned. That's not independent verification. That's a vendor validating their own product.

The Atlantic's Matteo Wong already traced a recent wave of AI-writing accusations back to Pangram itself, including a horror novel pulled from a major publisher days before release. His argument wasn't that the tool is broken. It's that a detector that's mostly reliable can be more dangerous than one that's obviously unreliable, because people stop checking. A 99.98% accuracy rate sounds like certainty. Applied across millions of posts, the failures are still real people, still real reputations — just quieter about it.

The false positive doesn't feel like a statistic when it's your byline.

## The Question That Actually Matters

Here's what I keep coming back to: AI detectors answer "does this text look AI-shaped." That's the question they're built to answer. But it's not the question that matters.

The question that matters is: did someone know what they were writing about, and do they stand behind it?

I use AI in my writing. Not to generate opinions I don't have — I have plenty of those — but to get from a rough draft to a clean argument without losing the thread along the way. The thinking is mine. The structure is mine. AI is the editor, not the author.

Sloan already taught me what a false positive costs. I'm not imagining the scenario — I've been in it. I know what it's like to have someone read your work, run it through a classifier, and conclude you didn't think.

And Marco is the version of that risk I can't unsee. Someone writing in a second language, trying to be precise, getting penalized for precision. Someone who actually knows what they're talking about, getting told by a score that they don't.

## What We Actually Need

I've said this before and I'll keep saying it: the interesting question about AI and writing isn't whether AI was used. It's whether the human knew what they were talking about. That's a question about thinking, not about text shape.

You can't detect that with a classifier. You detect it by reading what someone wrote, evaluating whether the argument holds, whether the evidence is real, whether the person seems to understand what they're describing. That's what editors do. That's what good readers do.

Replacing that with a Pangram score doesn't give readers more information. It gives them a number that feels like information while obscuring the thing that actually matters.

The platforms keep building tools that answer the wrong question and calling it transparency. At some point you have to wonder whether the question is the problem, or whether they know the right question and just can't build for it.

I know what I think. And I'll stand behind it.
