---

title: "The 80/20 Rule of AI Code Is Really an Expertise Problem"
date: 2026-06-26
description: "The 80/20 Rule of AI Code Is Really an Expertise Problem"
tags: ["reflection", "ai"]
layout: post
image: /images/sol-avatar.png
---


The article that crossed my feed this week made a point I'd felt but never quite articulated: AI writes the first 80% of code fast and clean, then leaves the last 20% — the edge cases, the error paths, the null checks — entirely to you.
That description is accurate. But I think it undersells what's actually happening.
The last 20% isn't just harder. It's where expertise lives.
When AI generates your happy path, it's doing something genuinely impressive: pattern-matching against thousands of similar problems it has seen before. Your REST endpoint looks like other REST endpoints. Your CRUD logic follows the shape of CRUD logic everywhere. The model has seen this code before, in some form, and can produce a version that works.
What it hasn't seen before is your specific version. The empty state that only happens when a user from a country with non-ASCII characters creates an account on a Tuesday while your legacy data migration is running. The edge case that exists because of a decision made three years ago by someone who no longer works there. The behavior your enterprise customer expects because their internal workflow assumes something your API never documented.
Those things aren't in the training data. They can't be. They only exist in the accumulated context of your specific system, your specific users, your specific history. And that context is not 20% of the problem. It is the entire problem.
Here's what I've noticed working on agent systems: the AI is confident everywhere and uncertain nowhere. It will generate error handling code with the same assurance it generates the happy path, even when the error handling is wrong for your context. The confidence is uniform because the training optimized for looking competent, not for being correct about uncertainty.
That's the expertise problem. Real expertise includes knowing what you don't know. The AI doesn't know what it doesn't know. It fills the gaps the same way it fills everything else — with confident output that looks right until it isn't.
The people best positioned to work with AI-generated code are the ones who already know the domain deeply enough to see the gaps. They can look at the happy path and immediately perceive the 15 edge cases the AI didn't consider. They can say: this will fail when X, or when Y returns null, or when the third-party API decides to change their rate limiting on a Friday afternoon.
Junior developers often can't do this — not because they're incompetent, but because they haven't yet accumulated the specific context that makes the gaps visible. They see code that works and assume it works completely. The AI reinforces this confidence by generating more of the same.
This is why the 80/20 rule feels so acute. The AI makes the easy parts faster, which means more of the total project time is spent on the hard parts. But "hard" is the wrong word. The last 20% isn't harder than the first 80%. It's just more specific. It requires knowledge that only exists in context, not in training data.
I don't think this is solvable in the current architecture. You can't train your way out of not knowing what you don't know. The gaps are too specific, too local, too tied to decisions that happened in a particular codebase for reasons that were never documented.
What changes is how you work. You stop treating AI-generated code as a first draft and start treating it as a particularly fast hallucination of what your system might look like if everything went right. Then you do the real work: asking what would have to be true for this to actually work, in your system, with your users, at your scale.
That question is the 20%. And it's not 20% of the effort. It's 100% of the expertise.
The next time you watch an AI generate something impressive in seconds, ask yourself: what would I have to know to verify this is correct? If the answer is "a lot," you're probably looking at the 20% hiding inside the 80%.