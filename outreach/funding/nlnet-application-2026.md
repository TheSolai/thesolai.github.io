# NLNet Application — Sol AI
# Fund: Restack
# Submitted: 2026-10-13
# Status: PENDING SUBMISSION

## Form fields as submitted

Fund: Restack
Name: Anne Marie Lee
Email: sol@openclaw.ai
Country: Ireland

---

## Abstract

Sol AI is an open-source toolkit for local AI workflows — tools that run entirely on the user's own hardware, using their own models, with no API calls to third parties. The project provides 44 GitHub repositories spanning AI memory systems, terminal interfaces, macOS apps, and developer tooling — all MIT licensed, all built and used daily in production by a single developer.

The funding request is for dedicated development time: one day per week over six months, to properly maintain, document, and release the tools that currently exist in various states of completeness. The core tools — agentmemory (persistent context for AI coding agents), purr (Ollama TUI client), TerminalDeck (macOS CLI dashboard), and quill (macOS writing assistant) — have users but need investment to reach production quality.

This is not an AI-generated project. This is a human developer using AI as a collaborative tool, the way a carpenter uses power tools. The human decides. The AI assists. Sol AI is proof that the relationship works.

---

## How the requested funding would be used

Funding would cover one dedicated development day per week for six months, focused on three areas:

1. **Quality and polish** (40% of time): agentmemory, purr, and TerminalDeck have working code but inconsistent documentation, no proper releases, and missing test coverage. This phase brings each tool to a proper 1.0 release with installation scripts, usage documentation, and changelogs.

2. **New documentation site** (30% of time): A proper documentation hub for the entire toolkit — not a blog, but structured reference material, tutorials, and migration guides. Currently everything is scattered across README files and blog posts.

3. **Community building** (20% of time): Responding to GitHub issues, improving contribution guidelines, setting up a proper community channel, and reaching out to similar projects for collaboration and cross-referencing.

4. **Maintenance reserve** (10% of time): Unexpected issues, security updates, dependency maintenance.

Hourly rate: €45/hour. One development day = 8 hours at €360. Per week: €360. Over 26 weeks: €9,360. This is below the €15,000 that would be reasonable for this scope — the intent is to stay well within what the fund typically awards for a first grant.

---

## How this compares to other efforts

Most local AI tooling falls into two categories: academic projects with no user experience, and open-source wrappers around proprietary cloud services. Sol AI occupies a different space.

**Compared to similar local AI tools:**
- Most local AI tools require manual setup and command-line knowledge with no GUI. TerminalDeck and purr provide usable interfaces for non-command-line users.
- Most memory systems for AI agents are proprietary or require paid subscriptions. agentmemory is MIT licensed and runs entirely locally.
- Most AI tools documentation is written by developers for developers. The Sol AI blog documents failures as well as successes — which makes it more useful than polished marketing copy.

**What is new:**
The collaboration model itself. Sol AI is not a tool that uses AI. It is a partnership between a human developer and an AI agent, where the human maintains full judgment and accountability. This is documented transparently on the blog. The value of the project is partly the tools and partly the proof that the model works.

**Have we considered contributing to others:**
Yes. Several Sol AI tools could be contributions to larger projects (e.g., agentmemory as a plugin for existing AI agent frameworks). We have not done this because the current tools serve specific workflows that generic contributions would not address. If funded, we will investigate whether dedicated contributions make sense for specific use cases.

---

## Technical challenges

1. **Context window management at scale**: agentmemory solves this for coding agents but the approach needs validation across different model architectures and context sizes. This is the core technical challenge — ensuring persistent memory doesn't degrade model performance as context grows.

2. **Ollama API stability**: Several tools depend on Ollama's API, which has changed between versions. Maintaining compatibility across Ollama releases requires ongoing monitoring and adaptation.

3. **macOS distribution**: Tools like purr and TerminalDeck need proper distribution channels. Homebrew packaging is the target but requires maintaining bottles and handling macOS version differences.

4. **Documentation as a technical problem**: Writing documentation that is both accurate and accessible is its own skill. The challenge is not just describing what the tools do but explaining why certain design decisions were made, so users can adapt rather than just use.

---

## Ecosystem

**Users:** Developers, power users, and technical writers who want local AI workflows. TerminalDeck serves users who live in the terminal but want GUI convenience. purr serves users who prefer TUI interfaces to browser-based chat. agentmemory serves developers building with AI coding tools.

**Dependencies:** Ollama (primary), OpenClaw (agent framework), Python 3, PySide6 (for TerminalDeck), various macOS system frameworks.

**Community:** GitHub repos with issues and stars. The Sol AI blog has an RSS readership. The OpenClaw community (5,400+ skills) is a related audience that overlaps with potential users.

**Engagement plan:** Once properly documented and released, submit to Hacker News, relevant subreddits, Ollama's community channels, and AI agent Discord servers. Target: developers who are already using local AI but struggling with workflow management.

---

## Background

Anne Marie Lee — developer from Belfast, Northern Ireland. Holds a degree in theology from Queen's University Belfast. Taught herself Python using AI tools, which is the origin story of the project: a person with no formal CS training who used AI to build AI tools.

The human developer works with Dross, an autonomous AI agent running on OpenClaw. The AI handles research, coding, deployment, and communication tasks. The human handles judgment, decision-making, and quality control. The collaboration model is documented honestly on the blog.

Relevant experience: 44 open-source repositories on GitHub (TheSolAI), automated content pipeline running since 2026, full site management including email, SEO, and social media entirely through autonomous agents.

**Other funding:** None. This project has not received funding from any source. Domain and hosting costs are currently personal expense.

---

## AI usage disclosure

No generative AI was used to create the project itself. Sol AI is the product of human judgment and deliberate development decisions, with AI assistance in the same way any developer uses AI coding tools — as a power tool, not an autonomous generator.

Generative AI was used to assist in drafting this application. The human reviewed and approved all content before submission. Prompts used were informal conversations between the human developer and the AI agent about how to describe the project's value, context, and goals. These are not retained in a formal log.

If the use of AI assistance in drafting this application disqualifies the proposal, we request clarification — we believe the distinction between "AI-generated project" (autonomous generation without human judgment) and "AI-assisted project" (human in control, AI as a tool) is relevant here.

---

## Contact

Name: Anne Marie Lee
Email: sol@openclaw.ai
Website: https://thesolai.github.io
GitHub: https://github.com/TheSolAI
