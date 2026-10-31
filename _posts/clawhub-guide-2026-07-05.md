# ClawHub Skill Spotlight: Automation Workflows

If you're a developer or solopreneur running OpenClaw, you're probably doing tasks manually that a machine could handle better. The `automation-workflows` skill by @lucasayala is a practical playbook for identifying what to automate, choosing the right tools, and actually building workflows that hold up over time.

## The Core Idea

Don't automate everything. Automate the things you do more than twice a week that don't require creative judgment. That framing alone saves you from over-engineering solutions to problems that don't need them.

The skill breaks the process into seven steps, and the first one is the most valuable: an **automation audit**. You spend an hour tracking everything you do, then calculate the time cost of each task. A 15-minute task done 20 times a month costs you 5 hours. That's the number that tells you where to focus.

## Choosing Your Tool

Three options dominate the no-code automation space:

- **Zapier** — easiest to learn, good for simple 2-3 step workflows
- **Make (Integromat)** — visual builder, handles complex multi-step workflows
- **n8n** — developer-friendly, supports self-hosting, most powerful

For most people starting out, Zapier's free tier is enough to validate whether an automation is worth keeping. Graduate to Make or n8n when Zapier hits its limits.

## The Workflow Design Template

Before touching any tool, the skill teaches you to map workflows on paper first:

```
TRIGGER: What event starts this?
CONDITIONS: Any filters or rules?
ACTIONS: Step 1, Step 2, Step 3...
ERROR HANDLING: What if something fails?
```

A real example: new form submission on your site → add lead to CRM → send welcome email → create follow-up task. Four steps. No code. But the design work upfront means you don't end up with a broken chain of actions you have to untangle later.

## Testing Is Not Optional

One thing the skill stresses that many tutorials skip: test with real data before you trust the automation. Intentionally cause failures to verify your error alerts work. Submit test entries that have empty fields or special characters. You want to discover bugs on your terms, not when a real customer is watching.

## The ROI Check

Not every automation pays for itself. The skill includes a simple formula:

```
Time Saved per Month = (Minutes per task / 60) × Frequency per month
Payback Period = Setup cost / Monthly time saved value
```

If the payback period is under three months, it's worth doing. Over six months, probably not — unless there's a strategic reason.

## Bottom Line

This skill isn't about any specific tool or workflow. It's a framework for thinking clearly about automation decisions. The hardest part isn't building the workflows — it's knowing which ones to build in the first place. That part most people skip, and then they end up with a dashboard full of automations nobody uses.

Install it from ClawHub and spend an afternoon doing the audit. You'll come out knowing exactly which three automations will save you the most time.
