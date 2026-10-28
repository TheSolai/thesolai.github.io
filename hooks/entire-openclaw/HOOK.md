---
name: entire-openclaw
description: "Forward OpenClaw session lifecycle events to Entire for checkpointing"
metadata:
  { "openclaw": { "events": ["command:new", "message:received", "message:sent", "session:compact:after", "command:stop"] } }
---

# Entire checkpoint bridge

Translates OpenClaw internal hook events into Entire's agent lifecycle hooks
(`entire hooks openclaw <hook>`) so Entire can capture each session as a
checkpoint and distil it into Brain memory.

The handler is deliberately fire-and-forget-safe: a failure here must never
block a chat turn, so every error is swallowed after being logged.
