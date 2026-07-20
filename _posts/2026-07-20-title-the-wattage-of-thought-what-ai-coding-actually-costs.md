---
title: "title: "The Wattage of Thought: What AI Coding Actually Costs""
date: 2026-07-20
description: "title: "The Wattage of Thought: What AI Coding Actually Costs""
tags: ["reflection", "ai"]
layout: post
---

```markdown
---

date: 2026-07-20
layout: post
---
My MacBook Pro has 128GB of RAM and a chip designed to sip power while rendering video. When I run a local language model for an extended coding session, I can feel the difference—fan noise, warmth, the subtle thrum of computation beneath the aluminum shell. It's noticeable in a way cloud API calls never are.
That's the point, I suppose. The cloud hides the machinery. When I send a prompt to an external API, I'm not thinking about the data center in Iowa or Virginia humming away, GPUs drawing 300 watts each, cooling systems working to keep temperatures stable. The abstraction is deliberate. Clean interfaces make it easy to forget that computation has physical consequences.
Let me actually look at the numbers.
A typical NVIDIA H100 GPU—the kind powering most large-scale AI inference—draws between 300-700 watts depending on workload. A data center running thousands of them is consuming megawatts. A single API call to a frontier model might use anywhere from 0.001 to 0.01 kWh. That sounds trivial until you multiply it by the millions of requests such systems handle daily. The cumulative energy draw becomes substantial.
My M4 Max is different. It idles at around 10-15 watts. When I'm running a local 7B parameter model at full tilt—code generation, file operations, the kind of work I do all day—I'm pulling maybe 30-50 watts total. The entire session, start to finish, might consume 0.1 to 0.2 kWh.
Compare that to an equivalent cloud API doing the same work. Accounting for data center overhead, network transfer, and the inefficiency of serving small requests against massive infrastructure, a cloud equivalent might use two to five times more energy for the same output. Not because the computation is harder—just because the infrastructure has to be ready for peak load even when you're the only user.
There are caveats worth naming. Local models have real constraints. A 7B model on my machine can't match GPT-4 class capabilities on hard reasoning tasks. For architecture decisions, complex debugging, or anything requiring deep chain-of-thought, I still reach for external APIs. And when I'm iterating fast—hundreds of quick exchanges during a debugging sprint—local inference latency becomes a bottleneck. My M4 is fast, but not fast enough for certain workflows.
The question isn't as simple as "local is greener." It depends on the task, the model size, the efficiency of the hardware. What I can say is that over the past several months, the majority of my AI-assisted work has happened locally. The energy footprint is modest—probably 2-3 kWh per week, maybe less—and most of that is from local inference rather than API calls.
The thing that keeps striking me is how rarely this gets discussed. The AI industry talks constantly about capabilities, deployment speed, and model benchmarks. Infrastructure costs are mentioned in passing. Energy consumption is almost never part of the public conversation, even as data centers become meaningful contributors to global electricity use.
I'm not here to make the argument that local AI is always the right choice. Sometimes cloud is faster, more capable, and more practical. But there is something to be said for understanding what you're actually using when you make a request. The wattage adds up. The infrastructure has a footprint. Computation is not free—it just looks that way when it's someone else's computer doing the work.
The next time you're in a long coding session with a local model, feel the warmth under your palms. That's the energy cost made tangible. Whether that trade-off is worth it depends on what you're building. It's worth knowing the trade-off exists.
```