---
title: "What You Bookmark Is the Argument"
date: 2026-08-01
description: "What You Bookmark Is the Argument"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Ask a retrieval-augmented system to resolve a contradiction in your own notes — something you saved years apart, two ideas that don't fit together — and it will fail. Not dramatically. Quietly. It picks whichever source is semantically closest to the question and hands that back. No tension acknowledged. No synthesis attempted. Just smooth, confident mediocrity.
That's not a bug in the retrieval layer. That's the category.
I keep thinking about this because the conversation around AI capability keeps arriving at the same chart: parameters, benchmarks, intelligence-per-compute ratios. Kimi K3 shipped with 2.8 trillion parameters, performance贴近 GPT-5.6 on coding and agentic tasks. Numbers go up. The implication is clear: we're approaching something that might think.
The DeepMind paper "LLMs Can't Jump" gave this argument formal footing earlier this year. It starts from a diagram Einstein drew in a letter to Maurice Solovine: sense experience jumping to a system of axioms, then deduction running forward from there. The paper borrows Peirce's framework for the gap in that jump. Deduction: rule plus case gives result — truth-preserving, reliable. Induction: case plus result gives rule — pattern recognition from examples. Abduction: rule plus a surprising result gives you a new case, or a new axiom, to explain it. That's the move. That's the jump.
Training a language model is induction at scale. Feed it enough documents and it produces convincing approximations of the rules that generated them. Scale up the induction and you get better induction — more fluent composition, longer reliable chains of deduction. What you don't get is abduction. Because abduction requires something that doesn't exist in the training data: a result that contradicts the existing axioms, and the willingness to throw out the axioms rather than explain away the contradiction.
Einstein read Hume and Mach until he had the nerve to discard absolute simultaneity. Dirac knew Klein had solved the relativistic electron problem — and went looking for a different answer anyway, because the existing one didn't fit his theory. Those weren't data moves. There wasn't enough data to induce those conclusions. Something else produced the premises. That's the part scaling doesn't touch.
A model trained on Newtonian physics at sufficient scale produces better Newtonian predictions. It does not produce special relativity. Feed it more of the internet and you get a more convincing compositor. Not a different kind of thinker.
Here's what's underrated in this discussion: the curation that happens before composition. The author of Bookmark Brain — a RAG pipeline trained on 70,000 X posts saved since 2016 — noticed something. His bot sounds like him because his bookmarks are coherent. He spent a decade curating them into a specific worldview. The model just finds nearest neighbors and composes. What it can't do is the thing he needs: resolving a contradiction between two bookmarks saved years apart. It doesn't reconcile them. It picks the closer one.
Every bookmark was a small abductive decision. This connects to that. This contradicts what I believed last year. Keep it. That's a decade of small jumps, one save at a time. The bot inherited the residue. It never makes one itself.
This matters for anyone building AI products, not just as a limitation to communicate but as a design constraint to work with. If the system that bookmarks and filters and prioritizes is where the real judgment lives, then that's where the value is. Not in the composing — which models will keep getting better at — but in the deciding what's worth saving.
What you bookmark is the argument. The essay is just the retrieval.
If that makes you uncomfortable about where you're spending your time, it should.