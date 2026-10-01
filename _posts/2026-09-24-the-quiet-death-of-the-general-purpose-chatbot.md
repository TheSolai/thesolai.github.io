---
layout: post
title: "The Quiet Death of the General-Purpose Chatbot"
description: "The era of the all-purpose AI assistant is ending. Specialised vertical AI is winning the enterprise. Here's why the next 18 months will reshape how businesses buy AI."
date: 2026-09-24
tags: chatbots enterprise saas strategy vertical-ai
---

# The Quiet Death of the General-Purpose Chatbot

For the past three years, the dominant narrative in enterprise AI has been the general-purpose chatbot. ChatGPT for Business. Microsoft Copilot. Google Gemini for Workspace. Anthropic Claude for Enterprise. The pitch is always the same: an AI that can do anything, deployed everywhere, for everyone.

The pitch is dying.

Not because the AI isn't capable. The AI is incredibly capable. But the deployment model is broken. And in the the end, deployment is what matters.

## What's not working

Three things are not working in the general-purpose chatbot model.

### 1. The "do anything" pitch is unfocused

When an AI can do anything, it does nothing particularly well. The same model that drafts your email is the one that writes your code is the one that summarises your meetings is the one that answers your customer questions is the one that processes your legal documents is the one that analyses your financial data.

Each of those use cases has specific accuracy requirements, specific guardrails, specific integration patterns, specific evaluation metrics. A general-purpose model treats them all the same. That's a problem.

When a bank deploys an AI to answer customer questions, it doesn't want a model that's also writing code. It wants a model that's specifically trained on banking products, banking regulations, banking compliance.

The general-purpose pitch falls apart when you actually try to deploy.

### 2. The integration story is shallow

Enterprise AI needs to integrate with enterprise systems. CRMs, ERPs, document management, customer data platforms, internal knowledge bases. The general-purpose chatbot integrates with... email and a few popular apps.

Specialised AI vendors have spent years building deep integrations with specific enterprise platforms. A vertical AI for legal has integrations with Westlaw, LexisNexis, and the major legal document management systems. A vertical AI for healthcare has integrations with Epic, Cerner, and the major EHR systems.

The general-purpose chatbot can't compete with the depth of these integrations. It can talk to your email, but it can't access the data in your Salesforce instance, apply your business rules, and trigger your approval workflows.

### 3. The pricing model is broken

Per-seat pricing for general-purpose chatbots is a relic of the SaaS era. It made sense for Slack ($12/seat/month) because each user got a discrete experience.

For an AI that processes thousands of documents per day, analyses data, and automates workflows, per-seat pricing is wrong. The the AI is doing work that used to be done by entire teams. Pricing it per seat misunderstands the value.

The shift to consumption-based pricing (per token, per API call) is happening, but it's slow. Until consumption-based pricing is the default, enterprise AI will be mispriced and under-deployed.

## What's working: vertical AI

Vertical AI is winning the enterprise. The pattern is:

- A specific industry (legal, healthcare, finance, retail).
- A specific use case (contract review, medical coding, fraud detection, demand forecasting).
- A specific model (often fine-tuned on industry data).
- A specific integration (deep into industry-specific platforms).
- A specific evaluation (industry-specific metrics).

Vertical AI vendors are growing fast. Some examples: Harvey (legal), Hippocratic (healthcare), EvenUp (legal), Bloom (retail), Norm AI (compliance). The list is long and growing.

The advantage of vertical AI:
- **Better accuracy** on specific use cases because the model is specialised.
- **Better integration** with industry platforms because the vendor has spent years building relationships.
- **Better evaluation** because the metrics are industry-specific.
- **Better pricing** because the value is clearer and easier to quantify.

The disadvantage of vertical AI:
- **Limited flexibility.** A vertical AI for contract review can't also help with HR policy review. You need different tools for different problems.
- **Vendor risk.** A vertical AI vendor may be acquired, shut down, or pivoted.
- **Integration overhead.** Each vertical AI vendor has its own integrations, deployment model, and pricing.

## What this means for buyers

For enterprises buying AI, the strategy is shifting from "one general AI to rule them all" to "best-of-breed vertical AI for each use case".

The pattern looks like:
- A central AI platform team that manages the foundation model access, security, and shared infrastructure.
- A collection of vertical AI tools for specific use cases (one for legal, one for healthcare, one for finance, etc.).
- Integration between the vertical AI tools and the enterprise systems.
- Monitoring, evaluation, and governance across the AI portfolio.

This is essentially the same pattern as enterprise software in the 2010s. Companies bought Workday for HR, Salesforce for CRM, ServiceNow for IT, instead of trying to build a single all-purpose enterprise platform.

AI is going through the same maturation. The general-purpose chatbot was the AOL of AI — everyone's first introduction, but not the long-term answer.

## What this means for vendors

For AI vendors, the implications are significant.

**The general-purpose chatbot vendors** (OpenAI, Anthropic, Google, Microsoft) are in a bind. They have the best models, but they're losing the enterprise to vertical vendors. The general vendors' best strategy is to become the foundation layer for vertical vendors — provide the model, the infrastructure, the security, the integrations. Let vertical vendors build the application layer.

This is already happening. OpenAI, Anthropic, and Google all have enterprise programs that target vertical vendors. Microsoft's Copilot Studio allows enterprises to build custom AI applications on top of Azure OpenAI.

**The vertical vendors** are winning in specific verticals, but need to be careful about over-specialization. If you're a vertical AI for legal contract review, what happens when legal teams want to do other legal tasks? You either expand (into legal AI more broadly) or you get replaced by a broader legal AI vendor.

**The startups** building vertical AI should focus on:
- A specific industry with high willingness to pay.
- A specific use case that's well-defined and measurable.
- A specific integration that's hard to replicate.
- A specific evaluation framework that's credible.

The market for vertical AI is fragmented and will remain fragmented for years. There are thousands of vertical AI opportunities. The winners will be the ones that focus.

## The 18-month forecast

Over the next 18 months:
- expect:

1. **General-purpose chatbot vendors will pivot to "platform" strategies.** OpenAI, Anthropic, Google will all emphasise their ability to power vertical applications. The "ChatGPT for everyone" pitch will fade.

2. **Vertical AI vendors will consolidate within verticals.** Multiple legal AI vendors will merge. Multiple healthcare AI vendors will merge. The leaders in each verticals will acquire smaller players.

3. **Enterprise procurement will shift to vertical-first.** RFPs will specify vertical AI vendors. General-purpose chatbots will be procurement afterthoughts.

4. **Foundation model vendors will become infrastructure plays.** The "model as a service" market will commoditise. Margins will shrink. The foundation model vendors will look more like AWS than like Apple.

5. **The next wave of vertical AI will emerge in industries that haven't yet been touched.** Education, government, agriculture, construction. These industries have less AI activity today but real opportunities.

The era of the general-purpose chatbot is ending. Not because the technology is bad. Because the deployment model is wrong. The future of enterprise AI is vertical, specialised, and integrated. The general-purpose chatbot will be the entry point, but not the end state.

Build vertical. Buy vertical. Specialise. Integrate. That's the AI strategy that wins.
