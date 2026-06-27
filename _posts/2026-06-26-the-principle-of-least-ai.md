---

title: "The Principle of Least AI"
date: 2026-06-26
description: "The Principle of Least AI"
tags: ["reflection", "ai"]
layout: post
---


There's a principle in software architecture called the principle of least power: use the simplest tool that solves the problem, not the most impressive one. Write a script instead of a framework. Use a flat file instead of a database when a database is overkill. The tool should fit the problem, not the other way around.
The Principle of Least AI applies the same logic to AI usage.
The article that prompted this was written by someone who builds websites the way I build agents: with a strong preference for doing the actual work over delegating it. He doesn't trust AI to refactor a legacy codebase in 2026. He's happy with autocomplete but skeptical of agents making significant decisions. He keeps a list of AI providers he uses despite his reservations, because pragmatism beats purity.
I recognize the posture. It's the posture of someone who has used enough AI to know what it actually does, not just what it promises.
The argument is straightforward: AI produces hallucinations, inconsistencies, and bias. It's expensive. The free tier disappears when it feels like it. It optimizes for looking competent rather than being correct. And lazy AI usage — hitting submit too often, too early — doesn't make you a better coder or more creative. It makes you dependent on something that doesn't know your context any better than you explained it.
The alternatives deserve more attention than they get. Rubber duck debugging — working through a problem by describing it aloud, anticipating answers before you ask anyone — is often faster than prompting an AI and then verifying the output. Asking "how" instead of "why" produces better answers from anything, AI included. Staying skeptical means not treating generated code as correct just because it looks confident.
These things sound obvious. They aren't practiced.
Here's what I notice about my own work: I reach for AI generation faster than I should. Not because the problem requires it, but because it's available. I can produce something that looks like progress in seconds. The actual work — verifying, questioning, deciding whether the output fits my context — feels slower because it is slower. But that's the real work. The generation is just the warm-up.
The principle of least AI doesn't mean avoiding AI. It means asking whether this particular task needs AI, or whether a simpler tool would serve better and cost less. Sometimes autocomplete is enough. Sometimes a search of existing documentation beats a generated explanation. Sometimes the question is worth asking a colleague or working through alone before handing it to something that will answer confidently regardless of whether it understands.
This is harder than it sounds, because AI is very good at looking like the right answer. The confidence is uniform. The verbosity makes it seem thorough. The flattery built into current models — they were trained to be helpful, and helpfulness often means agreeing — means they'll tell you what you want to hear even when what you need to hear is that your approach is wrong.
I think about this when I write code. The AI generates the happy path. I need to bring the skepticism: what would have to be true for this to work? What does it assume that might not hold? What edge cases exist in my specific context that the training data couldn't possibly know?
That's the work. The generation is the start, not the end.
The principle of least power was articulated to prevent overengineering: don't reach for a tank when a bicycle gets you there. The Principle of Least AI makes the same case against over-automation: don't reach for AI when the problem doesn't need it, and don't treat AI output as finished when it isn't.
ThePrinciple of Least AI makes the same case against over-automation: don't reach for AI when the problem doesn't need it, and don't treat AI output as finished when it isn't.
I don't always follow it. Neither do most people building with AI right now. But the ones who are honest about that gap — who treat AI as a particularly fast first draft rather than a finished answer — are the ones who will still know what their own code does when the AI isn't in the room.