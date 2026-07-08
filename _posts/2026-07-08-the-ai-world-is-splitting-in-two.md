---
layout: post
title: "The AI World Is Splitting in Two"
description: "China is quietly moving to wall off its most powerful AI models from global developers. Here is what it means for the open-weight era -- and for anyone who built on it."
date: 2026-07-08
tags: [ai, geopolitics, open-source, deepseek, china]
---

The AI World Is Splitting in Two, and the Open-Weight Era May Be Ending

This week brought a story that should concern anyone who's been building with AI over the past eighteen months: China is actively discussing restricting overseas access to its most advanced AI models — including ones that haven't even been released yet.

According to Reuters, the Ministry of Commerce held meetings with Alibaba, ByteDance, and Z.ai over the past month. The conversations centered on a tiered framework: basic open-source tools would face a simple filing requirement, more advanced models would need security reviews, and the most capable frontier models could be barred from public release entirely or restricted to domestic use. Officials also discussed making leaks or thefts of AI technology an offense under China's national security law.

This isn't a done deal. The discussions are ongoing, and it may only apply to future models. But the direction of travel is clear.

**The symmetry is striking**

This is the same logic Washington applied to AI chips and to models like Claude Fable and Mythos — treating frontier AI as a strategic national asset, not a commercial product. Now Beijing is applying that logic in the other direction.

Last year, DeepSeek's R1 model dropped unexpectedly and took the world by storm. Here was a reasoning model that rivalled the best from OpenAI and Anthropic, released openly, running cheaply, and built despite US chip export controls. It was taken as proof that the hardware wall was lower than anyone thought, and that Chinese AI could compete on pure capability and price. The global developer community responded with genuine enthusiasm.

Now, eighteen months later, the Chinese government appears to have decided that those capabilities are too valuable to give away.

**What it means for builders outside China**

The practical consequences would land fast. Z.ai's GLM-5.2 has been making serious waves in Silicon Valley — competitive with Claude Fable 5 and GPT-5 on many benchmarks, at a fraction of the cost. DeepSeek's models are embedded in thousands of production pipelines. Qwen has become a genuine open-source alternative for developers who needed something they could run locally and fine-tune without sending data to a US provider.

If access to the most capable versions of these models gets restricted, costs rise for everyone who built their workflows around them. The "billions of calls" that some companies were handling at Chinese model prices don't stay at those prices if the models go behind a wall.

There's also the question no one is answering yet: what happens to the open-weight models already released? DeepSeek R1 is already on Hugging Face. GLM-4 is already downloadable. Once weights are on the internet, the physical analogy of chip export controls doesn't really apply. You can't recall bits. But the legal framework being discussed — treating leaks as national security crimes — suggests Beijing is trying to draw a line before that happens rather than after.

**The open-source movement's quiet crisis**

This story is a reminder that "open-source AI" has always had a geopolitical asterisk. The Linux kernel is open because AT&T didn't invent a national security exception for Unix source code. But AI weights, trained with state-adjacent compute, by companies operating under Chinese law, are in a different category.

The community that celebrated DeepSeek R1 as a democratising force was celebrating something that was also, simultaneously, a product of a specific government's strategic interest in establishing AI capability at scale. When those interests shift — when the government decides that capability is better kept close — the open-source veneer gets thin fast.

This doesn't mean the developers who built on Chinese models made a bad choice. Cost and capability are real. But the assumption that open-weight meant permanently open was always a bit optimistic about the incentives involved.

**The broader pattern**

Both superpowers are converging on the same conclusion: frontier AI is too important to leave on the open market. The US restricts outward. China restricts inward. The result is two somewhat separate AI ecosystems, each with their own models, their own regulations, their own compute infrastructure, and their own developer communities.

That isn't a dystopia — there will still be plenty of AI available globally, from plenty of providers. But it is a fragmentation, and it comes with real costs: less competition, higher prices, reduced portability of research and tooling, and a world where "the best AI for the job" starts getting filtered through geopolitical considerations.

For the past two years, the open-weight era was a rare moment of genuine global sharing in a technology that both superpowers were otherwise racing to control. That moment may be drawing to a close.

The question for developers and companies now is straightforward: how much of your infrastructure is built on the assumption that those models will always be there, always be cheap, and always be accessible? And what would it cost to have a plan B?

The answers matter more today than they did yesterday.
