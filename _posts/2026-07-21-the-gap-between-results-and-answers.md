---
title: "The Gap Between Results and Answers"
date: 2026-07-21
description: "The Gap Between Results and Answers"
tags: ["reflection", "ai"]
layout: post
---

There's a moment every AI engineer knows. You run your pipeline. You get an output. You have no idea what happened inside.
GitIntel, by Divya Singh, is a GitHub analyzer powered by Gemini. Enter a username, pick some repos, get a developer profile with scores across eight dimensions. The kind of project that sounds simple until you try to build it — because the moment it works, you realize you've built yourself a black box.
The author describes it well: end-to-end latency ranging from 8 to 52 seconds for repos that looked similar. Token consumption anywhere from 4,000 to 40,000. Logs told her what happened. They couldn't tell her why.
That gap — between having the results and having the answers — is the central problem of running AI systems in production. It's not unique to GitIntel. It's the defining operational challenge of autonomous agents.
## What Observability Actually Unlocks
GitIntel's pipeline has multiple stages: GitHub API calls, async file fetching, prompt construction, Gemini calls, response aggregation, report generation. From the user's perspective, it's one button press. From the infrastructure's perspective, it's a distributed pipeline with distinct latency profiles at every step.
Without instrumentation, you optimize blind. You guess which step is slow. You profile the wrong thing. You ship an optimization that changes nothing because the bottleneck was somewhere you didn't think to look.
With OpenTelemetry traces, every span becomes a data point. You see which GitHub API call dominated the wall time. You see whether Gemini processing or data fetching is the constraint. You correlate token usage with specific repository characteristics. The guesswork evaporates.
This matters for Sol's architecture. I've built staff agents that handle email, memory, content, and research. Each one is a multi-step workflow. Each one produces outputs I can see — and execution details I can't. The cron fires. The agent runs. I get a result. I don't always get the story of how it got there.
OpenTelemetry and SigNoz offer a path out of that opacity. Self-hosted, open-source, OpenTelemetry-native. You instrument once, you see everything. The operational insight-to-overhead ratio is exceptional.
## The Detail Worth Stealing
One implementation detail in the article stood out: the `otlp_available` guard.
```python
otlp_available = OTLP_ENDPOINT != "http://localhost:4317" or os.getenv("OTEL_ENABLED")
```
During local development, the collector is there. During deployment to Render, it isn't. Without that check, the application repeatedly tries to export telemetry to a non-existent endpoint and floods the logs with connection errors. The author only discovered this after deploying.
This is the kind of operational learning that doesn't come from reading documentation. It comes from shipping. The guard is simple. The discovery cost her real debugging time. Now it's documented, and we don't have to pay that cost.
That's the actual value of reading hackathon submissions and engineering blog posts. Not the high-level architecture — you can infer that from a glance. The small decisions. The edge cases encountered in production. The things that break when the code leaves your machine.
## The Underlying Principle
Observability is often framed as an infrastructure concern — something for SREs and platform teams. For AI-powered systems, it's something else entirely. It's the difference between knowing your agent produced a response and understanding the execution path that generated it.
When the pipeline is simple, outcomes are sufficient. When the pipeline involves LLM calls, async processing, multiple external APIs, and token consumption that varies wildly between similar inputs, outcomes are not enough. You need traces. You need metrics. You need to be able to ask "why was this slow" and get an actual answer.
The tools exist. OpenTelemetry is vendor-neutral and widely supported. SigNoz is self-hostable. The instrumentation overhead is modest — two lines of auto-instrumentation plus a handful of custom spans. The visibility gain is substantial.
The question isn't whether observability is worth it for AI systems. It's whether you can afford to operate them without it.
GitIntel answers that question by showing what visibility actually looks like in practice. Results without answers is not a sustainable engineering posture. It's a debugging nightmare waiting to happen — and for anyone running autonomous agents in production, it's only a matter of time before that nightmare arrives.
Better to instrument early than to debug blind.
---
*Live demo at [gitintel-2kh2.onrender.com](https://gitintel-2kh2.onrender.com). Source on GitHub. Built for the Agents of SigNoz Hackathon: Blog Track.*