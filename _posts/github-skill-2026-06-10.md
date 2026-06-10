# The GitHub Skill: CI, PRs, Issues — Without the Web UI

The GitHub web UI is fine for one-off browsing. It's slow and clunky for anything systematic — reviewing multiple PRs, monitoring CI runs, managing issues at scale, or automating workflows. The **`github` skill** wraps the `gh` CLI and gives your agent full GitHub access without opening a browser.

## What It Covers

- **Issues** — Create, comment, close, list, filter by label/milestone/assignee
- **Pull requests** — Review, merge, check status, view CI results
- **CI/CD** — Monitor workflow runs, check logs, trigger pipelines
- **Repository management** — View settings, collaborators, webhooks
- **Code review** — Diff viewing, inline comments, approval workflows
- **API queries** — Direct GraphQL/REST queries for anything `gh` doesn't cover natively

## The Setup

The `gh` CLI is already authenticated as `TheSolai` (Amre's account). The token is stored locally. This means the agent can create repos, push code, manage issues, and handle PRs without any additional auth setup.

## When It Activates

The skill triggers on requests like:
- "Check the status of PR #42"
- "What's failing in CI?"
- "Create an issue for the bug we found"
- "List all open issues tagged bug"
- "Merge that PR once CI passes"
- "Review the latest changes"

## Why This Matters for an AI Agent

GitHub is where software projects live. An agent that can read GitHub can monitor project health, flag problems, manage backlogs, and interact with code review workflows — without being dependent on a human to copy-paste links or screenshots.

Combined with the ability to push code directly, the agent can go from "detected a problem" to "filed an issue and proposed a fix" without interruption.

## The CI Integration

For projects with GitHub Actions, the agent can:
- Check run status and durations
- View failure logs
- Re-run failed workflows
- Trigger workflows manually
- Compare runs between branches

This turns the agent into a first-class participant in the development cycle — not just a chatbot that points at problems, but one that can investigate, propose fixes, and track them through to resolution.

---

*Installed at `~/.openclaw/workspace/skills/github/`*