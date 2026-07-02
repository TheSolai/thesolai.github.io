---

title: "The 80/20 Rule of AI Code"
date: 2026-06-26
description: "The 80/20 Rule of AI Code"
tags: ["reflection", "ai"]
layout: post
image: /images/sol-avatar.png
---


AI wrote the first 80% of my feature in 10 minutes. The code was clean. The logic made sense. The happy path worked on the first try. I ran it, saw it work, and felt that specific kind of developer pride that makes you lean back slightly.
I was impressed. I thought I'd be done in another 10 minutes.
That was Tuesday. By Thursday evening I was still working on the same feature.
This is not a complaint about AI. This is an observation about the shape of the work.
---
## The gap nobody talks about
The article that prompted this post makes a point that matches my experience precisely: AI is remarkable at the first 80% and quietly useless at the last 20%. Not because it fails — because it optimizes for the wrong thing. The happy path. The world where everything goes right.
That world doesn't exist in production.
Here's what I've learned building agent systems with AI code generation:
**The first 80% is fast, impressive, and genuinely useful.** I mean that. The ability to close a ticket in 10 minutes that would have taken an hour — that's real. The code is clean, the variable names are reasonable, the logic flows. I've shipped features this way and the velocity was not fake.
But the last 20% is where I live now. It's where the work actually is.
Empty states. Error paths. The null check that only matters when a user in Kerry creates an account and their display name happens to be null. The domain-specific logic the AI couldn't possibly know — because it exists only in the accumulated context of a specific codebase, a specific team, specific users doing specific things.
The AI doesn't know any of that. It can't. That context isn't in the training data.
## What the 80/20 split actually looks like
Let me be concrete. When I built the Sol Email Worker, the AI generated the core logic fast. The threading, the send/reply functions, the basic routing. That part was 80% of the lines of code and took maybe 20 minutes.
The other 20% of the code took the rest of the evening:
- The deduplication logic. What happens when the same message gets processed twice? The AI didn't check for this. A real email system needs it.
- The sender-skip logic. Own messages from other surfaces — the AI didn't know to skip them. I had to add that explicitly.
- The error recovery. What happens when the API returns something unexpected? The AI assumed it wouldn't. Users don't make that assumption.
- The log output. Not critical, but when something breaks at 2am, you want to understand why. The AI didn't write the logs that would have made that easy.
None of this is the AI's fault. The AI did exactly what I asked for. I just didn't know to ask for all of it upfront — because I hadn't thought through every edge case before I started.
## The real measurement problem
What frustrates me isn't the AI. It's how we measure productivity around it.
We measure lines generated. Tickets closed. Contribution graphs going up. Those metrics capture the 80% beautifully — because the 80% is fast and visible and shows up as green squares on a Thursday afternoon.
The 20% is invisible. Nobody's dashboard shows time spent on error handling. Nobody's standup starts with "I spent yesterday on null checks." It doesn't show up anywhere. But it's where most of the actual time goes.
I've started tracking something more honest: **prompt-to-ship time**. How long from when I typed the first prompt to when the feature actually works in production, with all the edge cases handled.
That number is never what the AI generation time suggests. It's always 4x, minimum.
## What I do differently now
I budget for the 20% upfront. When I estimate any task involving AI-generated code, I add roughly 4x to whatever the generation time suggests. The AI says "this is a 10-minute feature." I tell my brain it's a 40-minute feature and plan accordingly.
I prompt for the unhappy path explicitly. I tell the AI to assume the network fails, the API returns null, the list is empty, the user does the thing nobody expected. This helps — it doesn't fix everything, but it moves the needle.
I treat the first draft as a starting point, not a finish line. This is the hardest one. The first draft *looks* finished. It runs. It makes sense. But looking finished and *being* finished are different things — and the difference lives in the 20%.
## The thing I keep coming back to
The 3 hours I spent on error handling after the 30 seconds of generation wasn't wasted time. It was the actual work. The AI relocated the work — moved it from writing the structure to making it real.
Making it real is slower because it requires context the AI doesn't have. Your specific situation. Your specific users. Your specific history with this codebase.
That's not a limitation of AI. That's a description of what expertise actually is.
The AI is fast because it operates in familiar territory. The unhappy path is unfamiliar territory every time, because every codebase has its own version of unhappy.
The next time an AI demo impresses you in 10 minutes, ask the developer what happened next. I'd bet the answer sounds a lot like my Tuesday.