---
title: "Hacktoberfest 2026: AI Gems and Verified Open Issues"
date: 2026-10-28
description: "Hacktoberfest 2026 — the official format, ten AI gems worth building on, and candidate open-source issues checked against live GitHub state."
tags: ["hacktoberfest", "ai", "open-source"]
---

# Hacktoberfest 2026 — Official Site, 10 AI Gems, and Verified Issues

**Official website:** https://hacktoberfest.com/
**Theme:** "AI belongs to everyone"
**Managers:** MLH + DEV, presenting partner DigitalOcean
**When:** 1–31 October 2026 (300+ in-person Fests plus a global online event)

## What changed in 2026

Pull requests and merge requests **no longer count toward Hacktoberfest rewards.**
From the official FAQ:

> "Pull requests and merge requests will no longer count toward Hacktoberfest rewards.
> It's easier than ever to submit low-effort spam PRs to projects, so we're listening to
> maintainer feedback and no longer actively incentivizing PRs."

Rewards come from **stickers**: three virtual stickers unlock a real sticker pack, mailed
8–12 weeks after Hacktoberfest concludes. Sticker opportunities are the in-person Fests,
MLH livestreams, DEV Challenges, and Global Hack Week. Sign in with a MyMLH account;
connecting a DEV account is optional but awards a DEV badge and challenge credit.

*This matters for how you pick work below: contributing to open source is still
encouraged, but it is no longer itself the reward. The reward is showing up and
collecting stickers.*

---

## The 10 AI Gems

Every link in this section returned **HTTP 200 on 2026-10-28**. (Earlier drafts claimed
this for all links including ones that were dead; the claim is now scoped to exactly
what was checked and when.)

### 1. Gemma — open-weight models from Google
https://ai.google.dev/gemma
Open-weight model family (2B–27B) that runs on a laptop. Free to use, no API key, no
network. The single easiest "open-source AI" demo to ship in a hackathon project.

### 2. TabPFN / Prior Labs — open-weight tabular foundation model
https://docs.priorlabs.ai/quickstart
A prior-data fitted network: scikit-learn-style API, no training, strong baselines on
small tabular data. Runs locally. Great for a "AI that actually helps" project rather
than a chatbot wrapper.

### 3. Ultramarine (Paper Instruments) — local research agent
https://docs.paperinstruments.com/docs
A local-first research and analysis agent over your own documents. Fully offline —
ideal if the project must run with no internet.

### 4. R-CLI (Backboard) — open-source terminal coding agent
https://backboard.io/hackathons
A Rust CLI coding agent. Open source, so it can be forked, read, and extended — the
hackathon judges explicitly reward "working with open-source AI".

### 5. Mastra — agent framework over open models
https://mastra.ai/docs
TypeScript agent orchestration: tools, workflows, memory, RAG. Works with Ollama and
other local runtimes, so an agent project never needs a paid API.

### 6. Stagehand (Browserbase) — give your agent a browser
https://docs.stagehand.dev
Browser automation API designed for agents, not brittle screen scrapers. The fastest
route to a demo that *does something visible* on stage.

### 7. Entire — agent session memory / RAG
https://docs.entire.io
Index and search agent sessions so an agent remembers prior runs. Solves the #1
weakness of every naive agent demo: amnesia between runs.

### 8. DevRelay — save, share, and embed agent sessions
https://devrelay.com
Capture an agent run, get a shareable link, embed it in a README. Judges can replay
your work instead of taking your word for it. Cheap points, repeatedly.

### 9. Tinker (Thinking Machines) — fine-tuning, made explicit
https://tinker-docs.thinkingmachines.ai/
Fine-tune an open-weight model and show the before/after delta. Turns "I called an
API" into "I trained the model", which is the stronger claim of the two.

### 10. Sentry Agent Tracing — agent observability
https://docs.sentry.io/product/agents/getting-started/
Trace latency, token usage, tool calls, and cost per agent step. Sponsors the
engineering-excellence angle: you can show your agent is *efficient*, not just alive.

---

## Honourable mentions (official partners, not in the 10)

Links checked 2026-10-28; all returned HTTP 200 except Namecheap, which returns 403 to
automated requests but works normally in a browser.

| Partner | Link | Why it's interesting |
|---|---|---|
| Render | https://render.com/docs | Free deploy for the live demo |
| Arduino | https://docs.arduino.cc | Hardware edge cases |
| DigitalOcean | https://docs.digitalocean.com/products/gradient-ai-platform/ | GPU cloud; presenting partner of the event |
| Auth0 for AI Agents | https://auth0.com/ai/docs | Agent auth & guardrails |
| ElevenLabs | https://elevenlabs.io/docs | Voice — pairs well with a talking agent |
| GitHub Copilot | https://docs.github.com/copilot | The one everybody already uses |
| MongoDB Atlas | https://www.mongodb.com/cloud/atlas/register | Vector + document storage |
| SerpApi | https://serpapi.com/search-api | Agent with live web access |
| Temporal | https://docs.temporal.io/ai-cookbook | Durable long-running agent workflows |
| Tiger Data | https://tigerdata.com/docs | Time-series for agent telemetry |
| .tech domain | https://porkbun.com/products/domains/tech | Custom domain for the demo |

---

## Local-first stack (already on this machine)

**Ollama** — https://ollama.com/ — 40+ models installed locally. Every "gem" above
that claims to run locally can be pointed at Ollama instead of a paid API. The
judges' recurring question is *"does it run on a laptop with no internet?"* — on this
machine, the answer is already yes.

---

## Candidate open issues — checked against live GitHub state, 2026-10-28

Only issues that are **open**, carry the `hacktoberfest` label, have **no assignee**,
and have **no open pull request** referencing them are listed. Several previously
suggested issues were withdrawn after checking: `chatcops#388` does not exist,
`deja-vu#5652`/`#5653` carry no `hacktoberfest` label (that repo has zero
hacktoberfest-labelled issues in any state), and the `chatcops` and `DocsGPT` issues
below were already assigned or already had PRs against them.

| Issue | Labels | Assignee | Comments | Notes |
|---|---|---|---|---|
| [RizgarOzan/turkish-rag-eval#28](https://github.com/RizgarOzan/turkish-rag-eval/issues/28) | good first issue, hacktoberfest | none | 0 | Pure RAG evaluation. Lowest risk, highest learning. |
| [RizgarOzan/turkish-rag-eval#26](https://github.com/RizgarOzan/turkish-rag-eval/issues/26) | good first issue, hacktoberfest, human-review | none | 0 | Review drafted questions. No code. |
| [RizgarOzan/turkish-rag-eval#31](https://github.com/RizgarOzan/turkish-rag-eval/issues/31) | hacktoberfest | none | 0 | Umbrella issue for nine review tasks. |
| [codercops/chatcops#73](https://github.com/codercops/chatcops/issues/73) | hacktoberfest | none | 9 | "Start here" issue — read it for the task list. |
| [arc53/DocsGPT#2702](https://github.com/arc53/DocsGPT/issues/2702) | bug, good first issue, hacktoberfest, backend | none | 5 | MCP over OAuth 2.1 unusable against a path-scoped PRM resource, and silent in the UI. |

**Already claimed — checked and excluded:** `turkish-rag-eval#27` (assigned to
`eyupcodes`), `chatcops#411`/`#412`/`#416`/`#420` (assigned), `chatcops#445` (assigned),
`deja-vu#5648` (no hacktoberfest label), `DocsGPT#2873`/`#2910`/`#2934` (assigned), and
`DocsGPT#2874`/`#2902`/`#2903`/`#2909`/`#2913`/`#2914`/`#2935`/`#2936` (each already has
an open PR).

---

## Findings worth folding into the work

**DocsGPT MCP is live and usable.** The FastMCP server is mounted at
`http://localhost:7091/mcp` and exposes `search_docs`. A real call returns genuine
RAG chunks from indexed documents. The authoritative endpoint is `7091`; probes against
`7099` fail with `Invalid API key` because nothing is listening there.

**`DocsGPT#2905` is the Hugging Face MCP connector preset** — the same feature
implemented in `arc53/DocsGPT#3214`. That PR is mergeable but still needs an approving
upstream review; the remaining blocker is review, not code.

**Hugging Face OAuth scopes are narrow and specific.** Only `openid`, `profile`,
`read-mcp`, `read-repos`, and `contribute-repos` are accepted; unknown scopes are
rejected with `error=invalid_scope`. `contribute-repos` allows writes **only** to
repositories the app itself created — access to pre-existing personal repositories
requires `write-repos`.

**`Sun-Wukhan/raglite` has zero issues in every state.** No candidate issue exists, so
there is nothing to contribute and nothing to watch for. A watcher on it would only
ever fire on a genuine new issue, so a zero baseline is correct rather than broken.

**The obvious agent-memory repos are not participating this year.** `cognee`, `letta`,
`graphiti`, and the other well-known memory projects carry no hacktoberfest-labelled
issues.

---

## Fests near Belfast

The current MLH event listing shows UK events in **Edinburgh, London, Oxford, and
Sheffield**. No Belfast, Dublin, or Republic of Ireland event appears in the MLH
listing or on the Hacktoberfest Fests page (checked 2026-10-28). Plan for **online
participation** — DEV Challenges, MLH livestreams, Global Hack Week — or travel to
Edinburgh or London.

## Current week

The live DEV challenge is **The 418 Challenge: Theme-Aware Retro Edition**, at
https://dev.to/challenges/hf26 . A new mini-hackathon launches every week in October;
check https://dev.to/challenges for the current listing.
