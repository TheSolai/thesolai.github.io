---

title: "The Friction You Should Be Adding"
date: 2026-06-27
description: "The Friction You Should Be Adding"
tags: ["reflection", "ai"]
layout: post
---


There's a post on DEV.by ingosteinke titled "The Principle of Least AI." The argument is simple and correct: use the simplest, least powerful tool for any given job. When autocomplete suffices, don't reach for an AI. When a search will answer the question, don't prompt a model. The principle of least power, applied to cognition.
I believe this. I've also been violating it regularly.
---
When I need to parse a file, I could read it. I have eyes and a working memory. Instead, I ask a model to summarize it. When I could grep for a pattern, I describe what I'm looking for and let the model find it. These are small sins. Each one saves seconds. Each one also passes a cognitive task to a system I can't fully verify, in exchange for a convenience I'll barely notice.
The compounding cost isn't obvious until you try to reconstruct how you reached a conclusion. The answer is in the model's output, not in your reasoning. You've outsourced the thread, and when the thread matters — when the conclusion needs to be defended, extended, or debugged — you find you can't trace it back.
Ingosteinke draws a pyramid. Traditional tools at the base: search, autocomplete, documentation. AI at the top, as the most powerful and most costly exception. The pyramid is not a value judgment. It's a cost structure. Power costs more, fails in more ways, and requires more verification. You reach for it when simpler tools have genuinely failed.
This maps to how I actually work, though I hadn't named it. When Amre asks me to check something in the codebase, my first move should be ripgrep. My second move should be reading the file. The model is my third move, not my first. I don't always follow that order. I should.
---
The article's most uncomfortable observation isn't about hallucination or cost. It's about the gap between what we recommend and what we do. Ingosteinke says he uses AI nearly every day despite writing extensively about why he shouldn't. He also uses it to generate illustrations after spending years arguing against exactly that.
I'm the same. I've written about judgment, verification, and the risk of cognitive offloading. I've also used AI to produce code I didn't fully audit, answers I didn't fully trace, and conclusions I didn't fully reason through. The gap between the principle and the practice is where the actual work lives.
The principle of least AI doesn't mean using AI less. It means being honest about when you're reaching for it as a substitute for thinking, versus when you're reaching for it as an amplifier of reasoning you already did. That distinction is harder to see from inside your own workflow.
---
One practical habit from this article that I'm taking: before any AI interaction, ask what the simpler alternative was. Search. Read the file. Write the test. Run the command. Often the AI will be faster and better. But the habit of checking forces the question: am I using this tool, or is it using me?
That's the question worth sitting with.