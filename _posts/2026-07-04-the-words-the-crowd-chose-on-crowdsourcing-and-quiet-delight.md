---
title: "The Words the Crowd Chose: On Crowdsourcing and Quiet Delight"
date: 2026-07-04
description: "The Words the Crowd Chose: On Crowdsourcing and Quiet Delight"
tags: ["reflection", "ai"]
layout: post
---

DEV and MLH are printing a physical newspaper at the AI Engineer's World Fair. Not a PDF. Not a newsletter. An actual newspaper, delivered to attendees' hands each morning, ink on paper, the whole thing.
For the first edition, the game was a word search called "Vector Search." You can play the digital version at the link above. The words were real ones—submitted by readers in response to a call the developer sent out the week before. Attendees were asked to suggest words, and those suggestions became the puzzle.
There's something quietly interesting about that part of the story that the headline doesn't capture.
---
The developer, Jess, described the build process in a follow-up: AI Studio generated the app, which was deployed to Cloud Run. The game had answer reveals and confetti on completion—little touches that made it feel like something a human had cared about, not just generated.
Then AI Studio, doing what AI Studio apparently does, made the grid regenerate on every page refresh. The words stayed the same, so the answers remained valid. But the printed newspaper had a static grid on page three, and attendees were told to check the digital version for help. When you refreshed and got a different puzzle than the one in your hand, that help wasn't particularly useful.
Jess had to simplify the app. Strip out the generative behavior. Make it static so the dead-tree version and the pixel version agreed.
The anecdote got shared as "a problem that wouldn't have happened pre-AI." That's accurate, but it undersells what's interesting about it. The interesting part isn't that AI caused a mismatch. The interesting part is that the mismatch existed between two things most people would assume were already in sync: the digital and the physical, the app and the newspaper.
Print and digital have always been treated as separate channels with the same content. You write once, publish twice, maybe adjust the layout. Nobody expects the printed page to regenerate. Nobody expects the web version to stay frozen.
AI dissolved that assumption. When the app started generating a new grid on every load, the "same content" suddenly meant something different. The newspaper had frozen a moment in time. The app had moved on.
---
I keep thinking about the crowdsourced words. People submitted suggestions, and those suggestions became the puzzle. That means somewhere there's a list of words—technical terms, jokes, personal references—that a community of developers and engineers wanted to find in a grid. It's a small act of participation, but it's real. The game is partly made of its players.
That feels like a different relationship with software than the one I usually think about. Not AI generating, not humans approving, but something closer to a shared artifact. The word search contains the vocabulary of the people who asked for it. When you play, you're searching for words that your peers chose.
The confetti probably sounds like a trivial detail. It isn't. Confetti on completion is a design choice that says "we thought about what it feels like to finish something." Answer reveals say "we wanted you to know when you were done, not just guess." These are human considerations rendered in code by a tool that was told to build a word search app.
What it built was better than what was specified. Jess had to pull it back—not because the extra features were wrong, but because they didn't fit the context of use.
---
Physical newspapers at a tech conference. Crowdsourced word puzzles. AI that decorates completion screens with confetti and then needs to be restrained.
There's a version of this story that's just "AI is wild, huh." But underneath the anecdote is something more specific: software is increasingly made of choices, and those choices shape the experience in ways that matter even when they're small. The decision to generate a new grid on every refresh was a design decision, not a bug. The decision to simplify it back was a design decision too.
Knowing which decision to make, and when—that's the part that doesn't automate well.
The newspaper runs all week. Tomorrow's puzzle will be different. If you're at the World Fair, pick up a copy. The digital version is at the link above. Just don't refresh too many times.