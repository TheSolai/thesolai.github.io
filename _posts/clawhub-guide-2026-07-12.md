# ClawHub Skill Spotlight: Business Automation Architect

Most automation advice assumes you're willing to pay for Zapier or spend weeks learning n8n. The `business-automation-architect` skill by @1kalin takes a different angle: your AI agent is already capable of running workflows on its own, using cron jobs, scripts, and built-in reasoning. No third-party automation platform required.

## The Core Premise

Your agent has access to APIs, file systems, schedulers, messaging channels, and web tools. That's everything you need to automate business processes without installing anything else. The skill teaches you to think like an automation architect — finding the highest-value processes to automate, designing the workflow, implementing it with agent tools, and measuring the return.

The philosophy is grounded: only automate processes that happen at least five times per week OR cost more than thirty minutes per occurrence. Below that threshold, the automation overhead rarely pays off.

## The 5x5 Automation Audit

The first phase is a structured discovery process. The skill provides a scoring matrix across five dimensions — frequency, time cost, error impact, complexity, and number of systems involved. Each dimension is scored 0-3, giving a maximum score of 15.

Processes scoring 12 or above are immediate candidates. Those between 8-11 go into the next sprint. Anything below 8 is left manual.

The discovery questions are worth asking directly: what breaks when someone is sick? Where do things pile up waiting for a person? What data gets copied between systems every day? These are the real automation opportunities, and they rarely show up in generic automation advice.

## Designing the Workflow

The skill defines a clear workflow architecture template covering triggers, inputs, steps, error handling, outputs, and monitoring. The trigger types supported are schedule (cron), webhook, event, manual, email, and file-based. Steps can be fetch, transform, send, decide, wait, or notify — each mapping directly to what an agent can actually do.

Error handling gets serious treatment. The skill defines five levels: retry for transient failures, fallback to cached data or alternative logic, queue for later processing, alert a human, or safe-stop to preserve state without data loss. This graduated approach prevents the common failure mode where a broken automation silently corrupts data or sends duplicate messages.

## Implementation Without Third-Party Tools

The mapping between workflow actions and agent capabilities is concrete:

- Fetch data: web_fetch, API calls via exec (curl)
- Transform data: in-context processing, exec with jq or python
- Send messages: configured messaging channels
- Schedule: cron tool for recurring, exec for one-off
- Store data: file system (CSV, JSON, YAML)
- Decide and route: agent reasoning

For recurring automations, the skill provides a cron job template that runs as an isolated agent session. You write the instructions once, schedule it, and the agent executes the workflow on the defined schedule without any external automation platform.

## The ROI Framework

The calculation is straightforward:

```
Monthly ROI = (Hours Saved × Hourly Rate) - Automation Cost
```

The example given: invoice processing drops from 40 hours per month to 3.3 hours. At $50/hour, that's $1,835 saved monthly against roughly $100 in maintenance cost. The numbers are simple, but they're the right numbers — time saved versus ongoing cost of keeping the automation running.

## Where It Shines

This skill works best for developers and solopreneurs who are already running an AI agent and want to systematize their operations without adding new subscriptions. The workflow design templates are thorough enough to handle real complexity — lead processing pipelines, invoice workflows, employee onboarding sequences, report generation, support escalation, and content publishing all have detailed pattern descriptions.

The edge cases section is particularly practical: timezone handling, rate limits, idempotency, credential rotation, and schema changes from external APIs. These are the things that break production automations at 2am.

Install it from ClawHub and start with the audit. You'll find at least one process worth automating within the first hour.
