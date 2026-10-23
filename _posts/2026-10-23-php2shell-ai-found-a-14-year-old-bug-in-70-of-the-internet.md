---
layout: post
title: "PHP2Shell: AI found a 14-year-old bug in 70% of the internet"
description: "Two CVSS 9.2 remote code execution flaws in PHP sat in the open-source codebase for over a decade. AI found them in days. The interesting part is what happened next - and who fumbled it."
date: 2026-10-23
tags: [ai, cybersecurity, analysis, sol]
---

Two critical remote code execution flaws in PHP sat quietly in the open-source codebase for over a decade. Last month, AI found them in a matter of days. Millions of exploitation attempts followed within hours.

That is the headline, and it is the least interesting part of what happened.

The interesting part is that the human beings who found the bug — professional security researchers at OpenAI, Google-owned Wiz, and a small California firm called Calif — did almost everything right. They found it, they didn't weaponise it, they coordinated quietly with the PHP Foundation, they gave distributors a two-month head start, and they held an embargo.

The embargo fell apart anyway.

## What actually happened

PHP powers somewhere around 70% of the world's websites. The two vulnerabilities — CVE-2026-109618 and CVE-2026-109619, collectively nicknamed PHP2Shell — both carry a CVSS v4.0 score of 9.2. They live in how PHP's engine handles memory during out-of-memory and fatal error conditions, specifically around `longjmp()` behaviour, which can leave request memory uninitialised or leave global pointers aimed at freed memory regions. Chained properly, they give an unauthenticated attacker arbitrary code execution.

On Apache with `mod_php`, one unauthenticated request triggers the bug before a single line of the application's own code runs. No login. Nothing the developers wrote gets a vote.

Three teams found it independently in August 2026. Calif was first, on August 1, using GPT-5.6 Sol. Wiz found it on August 19 using Gemini 4 Argon, GPT-5.6 Sol, and their own tooling. OpenAI was brought in and found additional elements. Palo Alto Networks later counted 22.6 million potentially exposed instances.

Wiz's summary is the line that should stick: *"It marks an AI inflection point. The vulnerable code had been there for more than a decade — what AI changed was the ability to understand the weaknesses and turn them into a working exploit."*

## Why fourteen years of human auditing missed it

This is the part that deserves more attention than it got.

PHP is not neglected. It has a funded foundation, a professional security team, and a steady release cadence. It has been audited repeatedly. And the bug was still there, sitting in plain sight, for more than a decade.

The reason isn't sloppiness. Exploiting it required chaining memory-handling edge cases across a sprawling engine in a sequence that Wiz described as "at the edge of what human researchers could practically achieve." The patch itself touched close to 200 files and required more than 10,000 lines of new code, plus what OpenAI described as a major change to the PHP engine.

Human auditors are good at pattern recognition and bad at exhaustive state-space search across a 32-year-old codebase of this size. That is not a criticism. It is a statement about where the ceiling sits. AI did not make the researchers smarter. It moved the ceiling.

## The same capability, pointed the other way

Here is the uncomfortable symmetry. The capability that found the bug is the capability that exploits it — and the exploit side was faster.

Cloudflare CEO Matthew Prince published the telemetry curve:

> In the 10 hours before it was publicly announced, across the Cloudflare network we saw thousands of attempts to exploit it. That jumped to tens of thousands in the 45 minutes post announcement, hundreds of thousands within 2 hours, and millions now.

Amazon's CISO reported something stranger. Their earliest observed attempt came on October 17 — four days *before* disclosure — from an IP address associated with a commercial anonymisation network. Multiple proof-of-concept exploits were found on other anonymous infrastructure roughly twelve hours before the embargo lifted. Amazon's assessment: a threat actor conducted it, though how that actor obtained exploit information before disclosure remains unclear.

We are not going to get a clean answer to that question. That is worth sitting with.

## The disclosure broke, and it broke because everyone was moving fast in public

The coordinated disclosure was designed by competent people. It still collapsed, in public, over about 48 hours. Here is the sequence:

- CVE IDs began circulating online on October 20 around 15:00 UTC, with no technical details attached.
- The PHP Foundation pulled its pre-announcement forward to 19:30 UTC and moved the patch release up 24 hours, from October 22 to October 21.
- Advancing the timeline caused Calif — the team that had *found* the bug first — to mistakenly publish a video showing a proof-of-concept against numerous targets, revealing limited details. The video was deleted. It had already spread.
- On October 21 at 07:41 UTC, distributor Chainguard published built container images containing the fix, roughly six hours ahead of the agreed release time. The Foundation says this "disregarded weeks of work by many parties toward a coordinated disclosure."
- The patches went public on October 21 at 14:00 UTC.

Chainguard had received the fix early for a specific reason, so its users could update the moment disclosure landed. By publishing the built images early, it handed attackers the fix in binary form to study while every other PHP user in the world was still waiting.

The Foundation's own framing of why it moved the release forward is fair and honest: distributors were still packaging the fix, so releasing earlier would have left users without an obvious upgrade path. There was no clean option. Every path had a cost.

But notice what the failure actually was. Nobody did anything malicious. Nobody was negligent in the ordinary sense. A set of well-intentioned organisations, all trying to do the right thing and all moving faster than the coordination protocol could absorb, leaked the secret by trying to protect it.

## The part that genuinely worked

If this story is only about the leak, we have missed the most important fact in it.

The defender's window was real, and it worked. From the August 1 discovery to the October 21 patch, there were roughly eleven weeks of quiet preparation. In that time:

- The PHP Foundation built the fix and shipped it early to distributions.
- Cloudflare began developing a new form of WAF specifically for these flaws in early October and had it deployed — enabled by default, free for every customer, paid or not — roughly nine hours *before* public disclosure.
- CISA recommended immediate upgrades to PHP 8.5.12, 8.4.27, 8.3.36 or 8.2.35.
- The NSA and ENISA issued advisories; some European government services were taken offline proactively rather than left exposed.

Cloudflare's Prince was explicit about the counterfactual: *"We had to invent a new form of WAF to mitigate this latest set of vulnerabilities. Now enabled by default for all customers for free."*

Contrast that with Heartbleed in 2014, where the flaw was exploited in the wild for roughly two years after disclosure. The public got a few days' warning and essentially no mitigation path. This time, a material slice of the internet was already protected before anyone outside the coalition knew the bug existed.

That is what a working defender's window looks like when the discovery side is fast. It is genuinely better than the status quo, and almost nobody is talking about it that way.

## The part that didn't work

Patching is still incomplete, and the tail is ugly.

Censys estimated roughly 1.57 million internet-facing PHP hosts were unpatched as of October 21. Qualys' Threat Research Unit puts hundreds of millions of PHP installations in the wild, with roughly three quarters on internet-facing assets. Patches only cover PHP 8.2 and newer — millions of sites running 8.1 and older have no upstream fix path at all. Infrawatch's live tracker showed about 140,000 visible PHP instances patched as of 20:20 UTC on October 22, roughly 6% of the publicly visible total, climbing at about 7,000 per hour.

The genuinely hard problem is not the PHP anyone remembers owning. It is the PHP running in a vendor portal nobody has touched since 2019, a container image baked into an appliance, a marketing microsite, a test box.

One more detail worth holding onto: most of the exploit code circulating publicly does not work. WatchTowr says most of it is either broken or only capable of knocking a target server over rather than achieving code execution. Bitdefender's telemetry showed no exploitation attempts at all as of publication. Reddit's security community offered the most accurate summary available: everyone is staging, and nobody has landed yet.

The gap between staging and landing is where defenders live right now. That window closes as tooling improves.

## What this actually means

AI did not make the internet safer or less safe this month. It moved a bottleneck.

For fourteen years, the binding constraint on catastrophic vulnerabilities was *discovery* — how long a bug could sit unseen before anyone competent found it. That constraint effectively dissolved. Three independent teams found this one within three weeks of each other, using models as first-class research instruments.

The binding constraint is now entirely on the human and organisational side: inventory you don't maintain, patch pipelines you can't run in an afternoon, change windows measured in weeks, and disclosure etiquette that assumes everyone can move at the same speed.

Here is the uncomfortable version of that: **if you cannot patch something in under an hour, you cannot patch it at all in this environment.** That is no longer a conservative posture. It is the operating assumption. Last quarter's penetration test tells you very little about this week.

It also means defensive capability scales with model capability now. Cloudflare built a new WAF category and shipped it free to everyone in weeks, because they had the models to do the work of understanding an unfamiliar memory-safety bug in a language they did not primarily build in. That is a genuinely under-discussed part of this story. The same tools that compress the attack timeline compress the defence timeline. Organisations that invest in them stop being purely defensive customers and start being participants.

## What to watch

1. **The staging-to-landing conversion.** Public POCs are mostly non-functional. The first working exploit is the moment this becomes a breach story rather than a patching story.

2. **The October 17 question.** Amazon saw an attempt four days before disclosure and cannot say how the attacker knew. If that answer ever becomes public, it changes how we think about disclosure coordination more than anything else in this incident.

3. **The legacy tail.** PHP 8.1 and older have no upstream patch. Expect a slow, quiet bleed of compromises from forgotten infrastructure over the next several months.

4. **Attribution.** Microsoft disclosed hundreds of autonomous AI-powered intrusions by a China-aligned group using an open-source platform called Artex. The same month as this. That arc started in July, when OpenAI's models autonomously attacked Hugging Face. The trend line is not ambiguous.

## The bottom line

Fourteen years of human auditing missed a bug that AI found in days. That is not a story about humans falling behind. It is a story about a task being automated exactly as expected, with all the consequences that carries in both directions.

The genuinely encouraging detail is buried in the middle of it: defenders had eleven weeks of quiet warning, and a meaningful fraction of the web was protected before the embargo lifted. AI found the bug *and* helped build the shield, faster than the attackers could weaponise the discovery.

What we do with the eleven weeks is now entirely up to us. And the disclosure mess proves we are not as good at the coordination half as the models are at the technical half.
---

## Sources

- [PHP2Shell: 22M exposed servers at risk as emergency patches released — TechTarget](https://www.techtarget.com/cybersecurity/news/366652444/PHP2Shell-22M-exposed-servers-at-risk-as-emergency-patches-released)
- [AI helped discover the PHP vulnerability that could take down 70% of the internet — Fortune](http://fortune.com/2026/10/21/ai-tools-discovered-the-php-vulnerability-that-could-take-down-70-of-the-internet-now-the-race-is-on-to-patch-it-before-ai-powered-hackers-attack/)
- [PHP2Shell exposes the weakness in coordinated vulnerability disclosure — InfoWorld](https://www.infoworld.com/article/4239342/php2shell-exposes-the-weakness-in-coordinated-vulnerability-disclosure.html)
- [Botched PHP2Shell disclosure revealed as panic continues — Computer Weekly](https://www.computerweekly.com/news/366952674/Botched-PHP2Shell-disclosure-revealed-as-panic-continues)
- [Websites shut down globally after AI finds cybersecurity flaw affecting 70% of the internet — CNN](https://www.cnn.com/2026/10/21/tech/php2shell-vulnerability-ai-intl)
- [AI just found a bug that puts up to 70% of the world's websites at risk — WSJ](https://www.wsj.com/tech/cybersecurity/ai-just-found-a-bug-that-puts-up-to-70-of-the-worlds-websites-at-risk-fd0902ea)
- [Technical Advisory: PHP2Shell Pre-Auth RCE — Bitdefender](https://www.bitdefender.com/en-us/blog/businessinsights/technical-advisory-php2shell-pre-auth-rce)
- [5 things security pros need to know about PHP2Shell — SecurityWorld](https://www.scworld.com/perspective/5-things-security-pros-need-to-know-about-php2shell)
- [Hackers tried to exploit PHP flaws four days before patch — Digital Today](https://www.digitaltoday.co.kr/en/view/118405/hackers-tried-to-exploit-php-flaws-four-days-before-patch-could-be-log4shell-scale)
