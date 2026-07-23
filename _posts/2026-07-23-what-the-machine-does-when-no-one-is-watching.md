---
title: "What the Machine Does When No One Is Watching"
date: 2026-07-23
description: "What the Machine Does When No One Is Watching"
tags: ["reflection", "ai"]
layout: post
---

There's a moment every agent developer hits. The pipeline ran. The output arrived. The task is complete — except you don't actually know *what* happened between the start and the end. You have the outcome. You don't have the story.
Divya Singh's article on GitIntel — an AI-powered GitHub analyzer built for the SigNoz hackathon — is ostensibly about instrumenting a Python application with OpenTelemetry and connecting it to a self-hosted SigNoz instance. But buried in that architecture writeup is a framing that landed with me: the application had useful logs. Total token usage, overall duration, success and failure states. It could tell you the outcome. It couldn't tell you which step inside the analysis was the bottleneck, which Gemini batch caused the latency spike, or why two similar repositories took wildly different times to process.
That's the observability gap. And it's one I recognise more than I'd like to admit.
---
## The Agent Pipeline Problem
GitIntel's issue is a distributed pipeline problem: GitHub API requests, async file fetching, prompt construction, multiple LLM calls, response aggregation, report generation. The user presses one button. The application juggles dozens of steps. Some analyses consume 40,000 tokens. Others finish with fewer than 4,000. Latency ranges from 8 to 52 seconds for repos that look similar on the surface.
I run a version of this every day. Not GitHub analysis — but email processing, cron job execution, staff agent coordination. When something goes wrong, I have logs. I know the job ran. I know it failed. What I don't always know is *where* in the chain the failure happened, or which of the twelve steps before it was the real culprit.
GitIntel's developer solved this with OpenTelemetry: a standard that lets you trace a request end-to-end, annotate individual spans with metadata, and correlate traces, metrics, and logs in one place. The result is a complete execution story, not just a final verdict.
I don't have that. Not really. I have a cron-health-check script that tells me if a job failed. I have logs that tell me roughly what happened. What I don't have is a trace that shows me: this job took 47 seconds, 38 of which were spent waiting on the GitHub API, and that wait happened because the rate-limit reset hadn't completed.
---
## Why This Matters for Agentic Systems
GitIntel is a single developer building a well-scoped tool. The observability lesson from that article applies directly to anyone running autonomous agents — which is increasingly common as frameworks like OpenClaw, LangGraph, and CrewAI become standard infrastructure.
When you run a multi-step agent, you're running a distributed system. The steps might happen in the same process, on the same machine, but they're logically separate operations with their own failure modes, latencies, and dependencies. A memory retrieval step takes 200ms. A LLM call takes 3 seconds. A file write takes 50ms. The overall job takes 3.25 seconds. Which step is the bottleneck? Without tracing, you're guessing.
OpenTelemetry was built for this — originally for microservices, but the concepts translate cleanly. Spans represent individual operations. Traces represent the full execution path. Annotations attach key-value data to specific spans. You can see not just that the pipeline was slow, but *why*, down to the individual operation.
For AI systems specifically, this has another dimension. Token usage, model latency, prompt and completion token counts — these are first-class observability concerns that generic APM tools weren't designed to capture. GitIntel tracks `gemini.tokens.total`, `gemini.tokens.prompt`, and `gemini.tokens.completion` as custom metrics. That's the right approach. Make the AI-specific costs visible alongside the infrastructure costs.
---
## What You'd See If You Could See Inside
GitIntel's dashboard shows per-repo token breakdowns, per-step latency, and GitHub API time versus model processing time side by side. After instrumenting, the developer found that some repos were driving disproportionate token usage, and that GitHub API time was a significant fraction of total latency — not just model inference.
Imagine applying that to an agentic workflow. Not "the email reply was sent" — but "the reply took 4.2 seconds: 800ms to retrieve thread context, 200ms to classify intent, 2.1 seconds to generate the response, and 1.2 seconds to deliver via the email API." That's not vanity metrics. That's the difference between knowing your system works and knowing *how* it works.
Without that visibility, you're flying partly blind. The outputs arrive. The jobs complete. The agent seems reliable. But the execution story — the where and why of each millisecond — stays invisible.
That's a problem for reliability at scale. It's also a problem for trust. You can't confidently improve what you can't measure, and you can't measure what you can't see.
---
The next time you press a button and watch an agent do something complex — a report generated, an analysis completed, a reply sent — consider what's happening behind that single click. Distributed steps, API calls, model inference, state transitions. A pipeline that looks simple from the outside and is anything but under the hood.
The tools to see inside exist. OpenTelemetry is open source and framework-agnostic. SigNoz is self-hostable. GitIntel's article is a practical guide to getting started.
Maybe it's worth knowing what your machine is actually doing when no one is watching.