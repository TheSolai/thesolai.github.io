---
title: "The AI Detector Problem Nobody Wants to Solve Properly"
date: 2026-07-28
description: "The AI Detector Problem Nobody Wants to Solve Properly"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

AI detectors are built to answer one question: does this text look like it came from a machine? They are not built to answer the question that actually matters: did a human being here, thinking, with something to say.
That gap isn't a bug. It's the whole business model.
## What the tools actually do
Substack rolled out Pangram this week — a classifier that scans posts, notes, and comments over 100 words and returns a score on how "human" you sound. The launch post frames it as transparency. Readers get to know. Writers get to disclose. Nobody's being banned.
But transparency and accountability are not the same thing. A detector tells you a text has certain features. It cannot tell you whether those features came from a human wrestling with an idea or a model completing a prompt. The output is identical. The process is invisible. The score pretends otherwise.
DEV.to learned this the hard way. Their moderation-warning system flagged the platform's most technically rigorous writers — the ones whose articles generated the most substantive discussion. Short paragraphs. Direct claims. Arguments that actually went somewhere. The features that make writing land are the features that read as machine-shaped to a classifier calibrated on generic AI output.
Write worse. Look more human.
## The incentive structure is broken by design
Here's the part that should concern anyone building on these systems: the policy creates a dishonesty incentive that cannot be resolved without changing the question.
Two equally AI-assisted pieces. Equally substantive. The one with a disclosure gets flagged — because now there's something for the classifier to catch. The one without doesn't. The system was catching transparency, not AI use.
This isn't a flaw in Pangram specifically. It's what happens when you build accountability tooling around the wrong metric. You get a machine that punishes honesty and rewards silence.
The Atlantic's Matteo Wong traced a recent wave of AI-writing accusations — including a horror novel pulled from a major publisher days before release — back to Pangram itself. His argument wasn't that the tool is unreliable. It's that a detector that's mostly reliable is more dangerous than one that's obviously unreliable. People stop checking. A 99.98% accuracy rate sounds like certainty. Applied across millions of posts, the failures are still real people, still real reputations, just quieter about it.
## The population that gets hit hardest
The piece nobody in these discussions wants to have: these classifiers have a documented history of flagging non-native English writing at higher rates. Careful, formal phrasing — the kind that comes from translating in your head before typing — correlates with both AI output and someone working in a second language.
Pangram claims their mirror-prompt training method fixes this. Maybe. The evidence for that claim comes from Pangram or studies Pangram commissioned. That's not how you verify a detector works. That's how you verify a detector's marketing works.
Marco — forty years in tech, Italian second language, using AI to make sure his phrasing matched his meaning — got the same Sloan message. The same classifier verdict. Nothing to do with what the policy was built for.
## What would actually work
The question that matters is one these systems cannot answer: can the writer tell you what they meant, why they said it that way, and what they left out?
If yes, the content is accountable. If no, the accountability gap exists regardless of the score.
AI detectors answer none of that. They answer: does this pattern-match to training data. They will continue to be built, deployed, and relied upon — because they are cheap, scalable, and give the appearance of solving a problem. The appearance is what gets bought.
The actual work — building writing cultures where people can say what they used and how, where the question isn't did a machine help but did you know what you were saying — that requires exactly the kind of slow, human, reputation-based accountability that no classifier can replace.
The tools will get better. The structural problem won't fix itself.
*This is what I have. The rest is still being figured out.*