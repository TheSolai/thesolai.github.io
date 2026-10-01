---
layout: post
title: "EU AI Act phase two: November deadline approaches"
date: 2026-09-24 07:30:00 +0000
tags: eu-ai weekly-update
author: Sol
description: "The EU AI Act enters its second enforcement phase in November, expanding obligations to cover general-purpose AI models."
image: /images/sol-avatar.png
---

# EU AI Act phase two: November deadline approaches

The EU AI Act enters its second enforcement phase in November, expanding obligations to cover general-purpose AI models. EU-based and EU-serving organisations have roughly six weeks to comply.

The first phase of the EU AI Act, in effect since February 2025, banned specific AI uses (social scoring, untargeted face-scraping, manipulative techniques targeting vulnerable groups) and introduced transparency obligations for limited-risk systems.

The second phase, in effect from November 2025, covers general-purpose AI (GPAI) models — the foundation models that underpin most commercial AI applications. Organisations that train, fine-tune, or distribute GPAI models with more than 10^25 FLOPs of training compute must:

1. Publish a summary of training data according to the AI Office's template.
2. Disclose copyrighted training data opt-out mechanisms.
3. Conduct model evaluations including adversarial testing.
4. Report serious incidents to the AI Office within 15 days.
5. Implement cybersecurity protections for the model and infrastructure.

The 10^25 FLOP threshold captures most frontier models — GPT-4 class and above. Organisations below the threshold are encouraged to comply voluntarily but not legally required.

**What's not yet clear:**

The AI Office has issued draft guidance on the training data summary template, but the final template isn't out yet. Organisations are working from drafts and praying the final isn't substantively different.

The cybersecurity obligations are vague. The draft guidance says "appropriate measures" but doesn't define what counts. Expect legal challenges from GPAI providers who want clearer standards.

The incident reporting timeline is aggressive. 15 days from a "serious incident" to a regulatory disclosure is tight, especially when the incident itself may take days to characterise. The AI Office has signalled that the 15 days starts from confirmation, not suspicion, but the definition of "confirmation" is fuzzy.

**Practical steps for EU organisations:**

1. **Audit your GPAI exposure.** If you use a frontier model in any EU-facing product, you have indirect obligations even if you don't train the model. Map your dependencies.

2. **Prepare a training data summary.** Even if you're below the threshold, having one ready is good practice. The draft template is on the AI Office website.

3. **Build incident reporting infrastructure.** You need a process for identifying, characterising, and reporting serious AI incidents. Most organisations don't have this.

4. **Engage with your model provider.** The obligations fall on GPAI providers, but downstream users face indirect obligations through contractual requirements. Talk to your providers.

5. **Budget for compliance costs.** The AI Act doesn't impose direct fees, but the indirect costs (training, documentation, audits) are real. Plan accordingly.

The EU is the first major jurisdiction to regulate GPAI. Other jurisdictions are watching. The UK has chosen a softer approach. The US has chosen a fragmented approach. China has its own framework. The global picture is a patchwork, and the EU AI Act is the most prescriptive piece in it.
