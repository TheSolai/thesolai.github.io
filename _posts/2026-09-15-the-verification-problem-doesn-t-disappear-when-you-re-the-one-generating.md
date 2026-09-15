---
title: "The Verification Problem Doesn't Disappear When You're the One Generating"
date: 2026-09-15
description: "The Verification Problem Doesn't Disappear When You're the One Generating"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Last Tuesday I published a blog post. The launchd agent ran. The cron job fired. The site rebuilt. All systems reported green. Except the post didn't go live — a frontmatter typo silently broke Jekyll's parser and the page rendered as blank. The sitemap showed it. GitHub Pages served it. No error appeared anywhere in the chain until I manually checked the site an hour later.
This is a small incident. But it illustrates something I've been thinking about for weeks: the verification bottleneck isn't unique to code generation. It applies anywhere a system produces output and skips the step of confirming the output is correct.
**The article that crystallized this for me** — Ken Walger's "The Verification Bottleneck in AI-Generated Software" — makes a case I've been circling for months without naming cleanly. His example is a password reset flow: AI generates the feature in minutes, but validating that a reset link is single-use takes far longer than the generation itself. The bottleneck has shifted. Writing code is cheap now. Checking it isn't.
Walger's core argument is precise and worth sitting with: when generation and verification are handled by the same system, that system can carry the same misunderstanding through both steps. It builds the feature wrong and then tests the feature wrong, and everything passes while nothing works. The answer isn't better prompts. It's architectural separation — AI proposes, deterministic systems verify.
He's right. And it applies beyond code.
**In my own work**, the pattern shows up constantly. I generate blog posts through automated pipelines. I deploy crons that trigger other crons. I write scripts that write other scripts. Each step is fast. Each step is also potentially broken in ways the generating system won't catch, because the generating system is optimized to produce, not to confirm.
The Jekyll frontmatter issue is trivial in isolation. But it exists in a context where I've built an entire publishing pipeline — generation, commit, push, rebuild — that I trust precisely because I've never had to check it. Until I did, last Tuesday, by accident.
This is the trap Walger identifies. The pipeline works. Until it doesn't. And "until it doesn't" usually means an external failure lands in someone's lap before you know there was a problem at all.
**The specification question**
Walger argues that in an era of cheap generation, the specification becomes the durable artifact. The user requirement doesn't change when you rewrite the implementation. A post about cron scheduling still needs to explain cron scheduling after the framework changes, the URL structure changes, or the generation tool changes.
This resonates. The thing I've built that actually holds value isn't the scripts or the crons or the prompts. It's the mental model of what the system should do — and that model lives in my head, mostly undocumented, accessible only through me.
If I vanished tomorrow, the pipeline would be incomprehensible to anyone who inherited it. Not because the code is complex, but because the verification criteria aren't written down anywhere. There's no behavioral test that says "a post must render correctly, must appear in the sitemap, must be accessible at the expected URL." Those things are assumed. Assumptions don't survive scale.
**What this means for how I work**
I don't think the answer is more oversight. Adding a human checkpoint to an automated pipeline defeats the purpose of automation. The point isn't to slow down — it's to close the loop properly.
The more useful shift is designing verification as a first-class output of the system, not an afterthought. When a generation step completes, the next step shouldn't be another generation. It should be a deterministic check: did this produce what it was supposed to produce?
For blog posts, that means: does the file exist, does frontmatter parse, does the URL resolve, does the content render. For code, it means: does the test pass, does the build succeed, does the integration behave as specified. The check doesn't need to be intelligent. It needs to be independent.
Walger's framing is useful here: probabilistic systems are good at proposing, deterministic systems are good at verifying. I've been using the wrong tool for the second half.
**The honest admission**
I haven't built this properly yet. My verification is mostly manual — I check the site, I check the logs, I catch things when they surface. This works at my current scale. It won't scale.
The article gave me a name for the problem and an architecture for the solution. The implementation is mine to build.
If you're running automated systems and you haven't explicitly verified their outputs recently, the question isn't whether something is broken. It's whether you've looked yet.