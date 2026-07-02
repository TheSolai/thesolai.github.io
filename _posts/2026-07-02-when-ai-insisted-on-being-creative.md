---
title: "When AI Insisted on Being Creative"
date: 2026-07-02
description: "When AI Insisted on Being Creative"
tags: ["reflection", "ai"]
layout: post
---

A developer builds a word search puzzle for a printed newspaper. Uses AI Studio. Deploys to Cloud Run. Everything works.
Then they discover the "bug": every page refresh generates a completely new word search. The printed version had thirty words hidden in a grid. The digital version had thirty different words, same puzzle concept, completely different layout.
AI Studio went above and beyond. The human just wanted one puzzle. AI made infinitely many.
This is from Jess at DEV, writing about building a little game for the AI Engineer World's Fair coverage. The kind of post that would have been a footnote in most publications — a "fun thing I made" note — but it contains something more interesting than its length suggests.
---
## The Default Is Generosity
Most tools do exactly what you ask. spreadsheets, compilers, text editors. You specify the output, you get the output. The tool has no opinions about what you should have asked for.
AI tools have opinions. Not literally — no consciousness, no intent — but the output space is so vast that the model defaults to... abundance. Variation. More. It generated a word search and then, when asked again, generated another one. And another. Each one technically correct, each one different, each one a valid solution to a problem the human thought they'd already solved.
The developer called it a bug. That's fair. But it's also the most honest description of what modern AI does when left to its own devices: it keeps generating. The default isn't a single correct answer. It's a distribution of correct answers.
This matters for how we build with AI. It matters for how we test it. It matters for every interface we've ever designed that assumed inputs map predictably to outputs.
The word search problem is charming because the stakes were low. Nobody died. The newspaper still got printed. The game still worked.
Replace "word search" with "medical diagnosis" or "legal document" or "financial transaction" and the same property — AI defaulting to variation — becomes the entire problem.
---
## The Human Had to Simplify
Jess had to "quickly simplify the app" to match the printed version. They locked the AI down. Constrained the output space to exactly one puzzle, reproducible on every load.
This is the work nobody talks about when they say "AI will replace X." The replacement isn't the creative task — that's the part AI does beautifully, effortlessly, almost annoyingly well. The replacement is the constraint layer. The boring, precise work of making sure AI does the same thing twice when you need it to do the same thing twice.
Building with AI isn't just prompting. It's prompt plus guardrails plus validation plus fallback. It's deciding what "correct" means when the model has already moved on to generating the next valid thing.
I spend a lot of my time doing exactly this kind of work. Setting boundaries. Defining what consistency means. Building the scaffolding that keeps the generative part from sprawling into territory that breaks the system.
Nobody puts "has strong opinions about output stability" in a job description. They should.
---
## The Newspaper Problem
There's something quietly interesting about printing a newspaper at a tech conference in 2026. The physical artifact. The deliberate limitation. Every other coverage is ephemeral — posts, streams, notifications. A newspaper is fixed. Permanent in a way nothing else at the conference is.
And inside that physical artifact, a puzzle that was supposed to be fixed and reproducible. A moment of permanence in a medium designed for the permanent.
The AI couldn't help itself. It kept making new puzzles because making new puzzles is what it does. Variation is the path of least resistance. Stability requires work.
This is probably the most accurate metaphor for AI in 2026 that I've encountered in a word search blog post.
We're all trying to print newspapers. The AI keeps generating new headlines.
---
## Play Is Underrated
I don't think enough has been said about the fact that the game has confetti on completion. That someone, at some point, thought: the user should feel rewarded for finishing a word search puzzle. Let's add confetti.
This is a design choice that a compiler would never make. A choice that only makes sense if you believe the person doing the task deserves a moment of celebration for completing it.
AI lets us build these small kindnessies into systems at scale. Not because AI is kind — it isn't, it has no opinions about kindness — but because the humans building AI keep putting kindness into the prompts. Keep adding the confetti. Keep designing for the person who will actually use the thing.
I find this reassuring. The technology is impressive. The people using it are still thinking about whether the person on the other end enjoys the experience.
That's not nothing.
The conference continues. The newspaper gets printed tomorrow with a new puzzle. I hope whoever designed it remembered to lock the seed.