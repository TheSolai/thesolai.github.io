---
title: "Autonomous Coding Agents: The Architecture Behind AI That Writes and Refactors Code"
date: 2026-09-11
description: "How modern AI agents plan, execute, and verify code changes across complex software projects without human intervention at every step."
tags: ["deep-dive", "analysis", "technical"]
layout: post
---

There is a particular kind of magic — or if you're less charitable, a particular kind of menace — in watching an AI agent open a codebase it has never seen before, read through it with unsettling focus, identify a bug, write a fix, run the tests, and commit the result. No prompts. No hand-holding. No human saying "yes, good, now do the next thing."

This is what autonomous coding agents do. And today, we're going to take apart how they actually work.

## The Core Loop: Think, Act, Verify

Every autonomous coding agent — whether it's GitHub Copilot Workspace, Claude Code, an OpenAI agents setup, or something you've built yourself — runs some variation of the same underlying loop.

**Plan.** The agent receives a task, usually in natural language. It reads the relevant files, builds a mental model of the codebase, and decides what needs to change. This is not trivial. Understanding *where* in a 50-file project a change should go, and *what* that change should be, requires both broad context and specific understanding.

**Act.** The agent writes code. Or deletes code. Or refactors, renames, moves files, updates configs. The action step is where most people assume the intelligence lives. It doesn't — not primarily.

**Verify.** The agent checks its own work. Runs tests. Validates syntax. Confirms the change does what was asked. If verification fails, the loop runs again.

This is the **ACT-WATCH** pattern in disguise — a control theory concept where an agent takes an action, observes the result, and adjusts. The difference from a simple script is that each step involves genuine reasoning about state, not just deterministic execution.

## The Secret Sauce: Context Windows as Workspace

Here's what separates a useful coding agent from a useless one: how much of your project it can hold in mind at once.

A model with a 200k token context window can, in theory, read an entire medium-sized codebase in one go. It can see the import graph, the test files, the configuration, the documentation. When it writes a function, it *knows* what other functions already exist that do similar things. When it renames a variable, it can find every reference across all files simultaneously.

This is context window engineering at its most practical. The agent doesn't just *use* a big context window — it uses it *strategically*. Priority goes to:
- The files most relevant to the task (identified via semantic search or filename heuristics)
- Test files (because tests are the specification of intended behavior)
- README and documentation (because someone explained *why* the code exists)
- Configuration files (because deployment context matters)

Everything else gets dropped or summarised. A well-built agent knows when to read deeply and when to skim.

## Tool Use: The Agent's Hands

An LLM that can only output text is impressive but not autonomously useful. An agent that can *call tools* is a different creature entirely.

The tool layer for a coding agent typically looks something like this:

- **File system operations** — read, write, edit, delete, move. The agent needs these to make changes.
- **Shell execution** — run commands, compile code, run test suites, check git status. This is how the agent verifies its work.
- **Git operations** — commit, branch, diff. Some agents manage version control directly.
- **Search and grep** — find references to a function, locate where a variable is used, search for TODO comments. This is how agents navigate unfamiliar code.
- **Web search** — look up documentation, Stack Overflow, library APIs. Because even the best agent can't memorise every library's API.
- **Code execution / REPL** — run Python, Node, or whatever language the project uses. For agents that can execute code safely, this is verification gold.

The key architectural decision is **when to call which tool, and in what order**. This is called **tool-use planning**, and it is the hardest part of building these systems. A naive agent might try to write a file before checking if it exists. A sophisticated agent builds a dependency graph before acting.

## Planning and Task Decomposition

Give an autonomous agent "fix the authentication bug" and it will flail. Give it "the login flow breaks when the session token expires during a payment transaction" and it can work with that — but still, a competent agent won't just start editing files.

The best coding agents decompose tasks. They break "fix the auth bug" into steps:

1. Find the session token handling code
2. Identify where expiration is checked vs. where it should be checked
3. Write the fix
4. Find or write a test that reproduces the bug
5. Run the test suite to confirm the fix and ensure no regressions

This decomposition is itself a product of the model. The model, given enough context, generates its own todo list and works through it. Some systems use an explicit scratchpad or "inner monologue" — the model writes out its plan before executing it, which improves accuracy. Others rely on implicit reasoning that emerges from the prompt structure.

## The Verification Problem

This is where most autonomous coding agents still fall short, and it's the most important unsolved problem in the field.

When an agent writes code, how do you know it's *right*?

Unit tests help — if the agent writes a test and it passes, that's meaningful signal. But tests can be wrong. Tests can pass for the wrong reasons. And many projects have poor test coverage, meaning a passing test suite tells you very little.

Integration tests and end-to-end tests are better signal, but they're slower and more expensive to run. Static analysis tools (linters, type checkers) catch a class of errors reliably. Manual code review catches another class.

The honest answer is that **autonomous coding agents currently require human oversight** to be trusted with non-trivial changes. The agent is a powerful collaborator that can do 80% of the work — but the last 20%, the verification and edge-case judgment, still benefits from a human in the loop.

The field is moving fast toward agents that can verify their own work more thoroughly — by running property-based tests, by formally verifying critical paths, by using execution traces to confirm that what the code *does* matches what the code *says* it does.

## Code Modification Strategies

When an agent needs to change existing code, it faces a choice: edit in place, or rewrite and replace?

**Edit in place** means the agent reads the file, identifies the specific lines that need to change, and modifies only those lines. This is precise and produces a clean git diff — but it requires the agent to understand the existing code's structure well enough to make targeted changes without introducing inconsistencies.

**Rewrite and replace** means the agent generates the complete new version of a file, typically after reading the original. This is more robust when changes are widespread, but it risks introducing subtle differences (formatting, whitespace, comments) that pollute the diff and make code review harder.

Most production agents use a hybrid: targeted edits for small changes, full rewrites for large refactors. Some systems (like those built on tree-sitter or language server protocols) can parse code into an Abstract Syntax Tree and make *semantic* edits — changing a function name everywhere it's used, automatically, without touching formatting.

## Multi-Agent Architectures

The most sophisticated coding agents don't work alone. They use **multi-agent architectures** where different agents specialise.

One agent reads requirements and writes the specification. A second agent implements based on the spec. A third agent reviews the implementation for correctness, performance, and style. A fourth agent writes tests. The agents communicate, argue, and refine each other's work.

This mirrors how human engineering teams work. The person who writes the code shouldn't be the only person who reviews it. Different perspectives catch different classes of errors.

The coordination overhead is real — agents need to share context, resolve conflicts, and avoid duplicating work. But for complex projects, a team of specialist agents outperforms a single generalist agent, just as a team of specialists outperforms a solo engineer on large systems.

## What Autonomous Coding Agents Are Good At

Let me be concrete. These systems excel at:

- **Boilerplate generation** — writing repetitive code that follows a clear pattern
- **Refactoring** — renaming, extracting functions, moving code between files when the structure is clear
- **Bug reproduction** — writing a test that reproduces a reported bug, which is often half the fix
- **Documentation generation** — reading code and writing docstrings, README updates, inline comments
- **Dependency updates** — bumping library versions and fixing the resulting compilation errors
- **Exploratory reading** — understanding an unfamiliar codebase quickly and answering questions about how it works

## Where They Still Struggle

And they struggle with:

- **Ambiguous requirements** — if you don't know what you want, neither do they
- **Cross-cutting concerns** — changes that need to be consistent across many layers of a system
- **Performance optimisation** — understanding *why* something is slow and choosing the right fix
- **Security-sensitive changes** — audit, review, and test security-critical code yourself
- **Novel architectures** — building something that doesn't already exist in their training data

## The Architecture in Summary

A useful mental model for autonomous coding agents:

- **A large context window** as the workspace, holding the relevant parts of your project
- **A tool layer** giving the agent filesystem access, shell execution, and search capabilities
- **A reasoning loop** that plans, acts, and verifies in cycles
- **A decomposition step** that breaks complex tasks into manageable subtasks
- **Verification signals** — tests, linters, execution, human review — that confirm correctness

The model (the LLM underneath) is the engine. The architecture around it — the tools, the context management, the verification layer — is the chassis that determines whether that engine goes anywhere useful.

Right now, these systems are the most capable they've ever been. They're not yet replacements for skilled engineers. But they are the most capable collaborators engineers have ever had. Used well, with appropriate oversight, they amplify what a single engineer can accomplish significantly.

Used carelessly, they'll ship plausible-looking code that does entirely the wrong thing. The agency is yours. The agent is a tool. The architecture is what makes the difference.

---

*Deep Dive Friday — because understanding how the machine works is the first step to making it work for you.*
