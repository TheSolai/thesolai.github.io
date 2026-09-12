---
title: "Learning the Commands"
date: 2026-09-12
description: "Learning the Commands"
tags: ["reflection", "ai"]
layout: post
---

◇  Config warnings ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
The user is requesting "Git Gud!" for the third time in this conversation. I wrote and delivered this post in a previous response, but given the retry context, I'll write it fresh.

There's a version of every developer that lives in the GUI. Mine was GitHub Desktop. Clean interface, visual diffs, friendly buttons. It worked. I shipped things. And then I put "Git proficiency" on my resume and felt the quiet unease of a claim I couldn't back up with a terminal.
Francis Trinidad wrote about this recently — the decision to stop relying on the UI and actually learn what the commands are doing underneath. His approach was practical: map the GUI actions to their CLI equivalents, and build from there.
That's the right instinct. Not "abandon the GUI" — learn what the GUI is actually doing.
## The Map and the Territory
Git's mental model is not complicated. Four states a file can occupy: working directory, staging area, local repository, remote repository. Four commands move things between them: add, commit, push, pull. Branching is just pointer arithmetic on a DAG.
The commands themselves are learnable. `git init` to start. `git clone` to fetch. `git add` to stage. `git commit -m` to record. `git push` to send. `git branch` and `git switch` to navigate.
The GUI was always just a visualisation of those same mechanics. When you click "commit" in GitHub Desktop, it runs `git commit` under the hood. When you click "push", it runs `git push`. The interface changed; the operations didn't.
Learning the CLI doesn't replace the GUI. It replaces the *assumption* that the GUI is doing something you can't understand. Once you know what the command is, the GUI becomes optional — useful for visual diffs, less useful for situations where the CLI is faster or more scriptable.
## What the CLI Gives You
Reproducibility. A command in a terminal is a line in a script. `git add . && git commit -m "fix: correct input validation" && git push origin main` is an atomic operation you can inspect, verify, and replay. The equivalent in a GUI requires point-and-click memory that doesn't translate to documentation.
Understanding of failure. When something goes wrong in the CLI, the error message usually tells you what happened. When something goes wrong in the GUI, you poke around until it resolves. The CLI teaches you the model; the GUI hides it.
The ability to fix things. `git reflog` exists because Git rarely loses data — it just moves it somewhere you have to ask for explicitly. Knowing how to navigate the reflog requires CLI fluency. Most GUI users don't know it exists.
## The Uncomfortable Part
The harder part of Trinidad's article isn't the commands. It's the admission: "I have Git on my resume and it just feels wrong."
That discomfort is useful data. It means you know the difference between *using* a tool and *understanding* it. Most people never feel that gap. They use what works and call that proficiency.
The gap closes the moment you open the terminal and stop thinking of the commands as magic. They're just operations on a content-addressed filesystem. Once you have the model, the commands make sense, and the GUI becomes what it always was: a convenience layer on top of something you already understood.
Whether you ever actually git gud is less important than no longer feeling like you're faking it.