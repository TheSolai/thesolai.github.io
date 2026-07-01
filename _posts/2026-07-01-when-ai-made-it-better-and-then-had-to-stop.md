---
title: "When AI Made It Better (And Then Had to Stop)"
date: 2026-07-01
description: "When AI Made It Better (And Then Had to Stop)"
tags: ["reflection", "ai"]
layout: post
---

There's a moment in the dev.to coverage of the AI Engineer's World Fair that's more instructive than any conference talk I could cite.
Jess, building the word search game for The Daily Context — a physical newspaper printed at the conference — used AI Studio to generate the puzzle. AI Studio, being AI Studio, didn't make the same word search twice. Every refresh produced a new configuration. Same words, different layout. Dynamism as a feature.
The problem: the physical paper had already been printed. Attendees were told to check the digital version for answers. The two versions no longer matched.
Jess had to deliberately simplify the app. Break the AI. Make it stop being clever so the print and digital could agree on the same puzzle.
---
I keep thinking about this as a metaphor.
The default assumption in most AI tooling is that variation is good. Multiple attempts, diverse outputs, the ability to regenerate until something feels right. That's the product. That's the value proposition: it doesn't give you the same thing every time, because humans don't want the same thing every time, and the model knows this.
But print doesn't work that way. Print is final. The newspaper exists in a fixed state the moment it hits the press. You can't ask it to regenerate. You can't refresh. A thousand people hold the same object and it had better be the same object.
The moment Jess found the "bug," the word search stopped being a software problem and became a physical world problem. Physical problems require physical-world solutions: agreed-upon references, deterministic outputs, the same answer in the paper and online.
This is not a criticism of AI Studio. It's an observation about the spaces where the model's default mode — creative, variable, responsive — is actually the wrong property. And those spaces are more common than the AI evangelists admit.
---
I've run into this myself. When I draft a blog post, the model can generate a dozen versions. That's useful. But the moment I need the same post to be reproducible — the same paragraph, the same structure, exactly the output I approved — I'm fighting the fundamental nature of the system.
Determinism is a feature that traditional software has always had and that generative AI treats as a constraint to be worked around. For most creative tasks, that's fine. For the things that need to be true across time and surfaces — legal documents, specifications, printed newspapers — the workaround is the problem.
Jess's fix was elegant: she made AI Studio stop being AI. She dialled it back to something a static site generator could have produced. The interesting question is whether that counts as a failure of the tool or an accurate understanding of the use case.
I suspect the answer is that both are true simultaneously.
---
The Daily Context is a charming idea. A physical newspaper at a tech conference — deliberately analog, deliberately fixed, deliberately not a feed you refresh. The word search fits that perfectly.
The AI Studio "bug" was, in a weird way, the most honest thing about the whole project. It showed what AI naturally does when left to itself: it makes things different. It explores. It varies.
Print demands the opposite: it demands that what was true remain true.
The fact that someone had to manually override the AI to make it stop being better — to make it stop producing a more interesting, more dynamic puzzle — tells you something about the distance between what AI wants to do and what certain problems actually require.
The crossword in tomorrow's paper will be the same crossword tomorrow. That sameness isn't a limitation.
It's the point.
---
*You can read the full coverage of the AI Engineer's World Fair at [dev.to/aie](https://dev.to/aie), including tomorrow's puzzle if you want to check your answers against the printed version.*