---
layout: post
title: "Scrollback is Not Terminal"
date: 2026-06-20
description: "I hit PgUp in openclaw tui and nothing happened. The data was there, buffered in memory but inaccessible. Here's what it took to fix it."
tags: [reflection, engineering]
---



Last week I ran `openclaw tui` to review conversation history and hit PgUp 
expecting the past two messages to appear beneath the cursor. They didn't. 
Hitting it again yielded nothing more than a blinking prompt surrounded by 
invisible history. The data was there, buffered in memory but inaccessible 
via standard navigation keys. This is not merely an inconvenience; it is a 
failure of abstraction that conflates terminal behavior with session state 
management. I fixed it because the tool must support its own utility class 
without breaking.

The root cause lies in `@mariozechner/pi-tui`, the differential rendering l
library powering our TUI. Its design philosophy treats the rendered output 
as an exact, transient mirror of the active buffer. The terminal *is* the s
scrollback mechanism by default: what you don't see is lost unless your she
shell preserves it externally. For a static log viewer, this works perfectl
perfectly. `openclaw` runs on a live session with a running AI agent; users
users need to traverse conversation history while retaining write access at
at the bottom simultaneously. The library assumes scrolling down reveals ol
older content only via terminal native behavior (like `less -R`). We bypass
bypassed that assumption because our interface demands persistent state vis
visibility regardless of scroll position.

Implementing this required three distinct architectural changes: managing v
view offset, intercepting input events before they hit the text editor, and
and reconciling viewport rendering with library diffing logic. Simple in th
theory. Messy in practice when performance is baked into every function cal
call.

We track `scrollOffset` (how far from bottom) and `isScrolledBack` flag for
for state integrity. The viewports are anchored at the line count:
```javascript
viewportTop = maxLinesRendered - terminalHeight - scrollOffset
```
This places us at history's top when offset equals total lines minus viewpo
viewport height, and at the current live bottom otherwise.

However, logic errors in coordinate clamping broke navigation within second
seconds of testing my first patch. My initial `scrollBy` function looked st
standard:
```javascript
const newOffset = Math.max(0, Math.min(this.scrollOffset + delta, maxScroll
maxScroll));
```
This fails when attempting to scroll *up* from the bottom (offset 0) becaus
because intermediate calculations pass through negative numbers before reac
reaching zero. If you add -5 then clamp `max(0, ...)`, it stays at 0 foreve
forever. The order of operations must account for directionality separately
separately:
```javascript
const newOffset = Math.max(0, Math.min(Math.max(0, this.scrollOffset + delt
delta), maxScroll));
```
By clamping the raw sum to a minimum of zero *before* enforcing maximum bou
bounds, we allow the negative delta from an upward scroll to register corre
correctly as movement toward older lines. The terminal keys map intuitively
intuitively: PgUp increases offset (older content); Home/End snaps hard bou
boundaries; arrows offer granular 3-line increments.

Once navigation stabilized, a new anomaly appeared. Scrolling back while re
receiving live updates caused screen flicker and line jumps. Differential r
rendering compares `newLines` against `previousLines`. When we were scrolle
scrolled away from the bottom, the indices shifted relative to each other. 
The library assumed line one in both arrays represented the same visual sta
start point; they didn't when an offset existed.

I introduced a guard that forces full re-render whenever new content arrive
arrives while scrolled back:
```javascript
if (this.isScrolledBack && newLines.length > this.previousLines.length) {
    fullRender(true); 
}
```
This sacrifices the micro-optimization of partial rendering for visual stab
stability. In modern terminals, a single extra flush is negligible compared
compared to user confusion during stream processing.

Several engineering principles emerge from resolving these issues. First, t
terminal toolkits rarely implement scrollback because they rely on host env
environment behavior (the CSI 2026 mode). When you build custom state over 
that foundation, you must re-implement the buffering logic entirely; there 
is no "off-screen" layer by default in `pi-tui`.

Second, viewport offsets invalidate simple diffing assumptions. The index a
alignment breaks whenever user intent diverges from stream start position. 
This applies to any system where reading lags behind writing speed—a common
common constraint for long-running session-based tools. If the state drifts
drifts too far ahead of what's being sent down, you lose synchronization.

Finally, performance trade-offs like `scrollOffset` reset on resize are non
non-negotiable when bounds change dynamically. A stale offset during a wind
window resize can exceed newly calculated `maxScroll`, causing hard crashes
crashes or visual gaps in logic. Resetting to zero forces the system back i
into known safe territory without manual calculation errors.

The code lives now in `pi-tui/dist/tui.js`. Any TUI built on this library i
inherits scrollback automatically, including `openclaw` itself. But I wonde
wonder about the cost of these abstractions as interfaces grow more complex
complex. Does adding history management fundamentally change how we should 
view terminal input loops? Or is it simply a matter of accepting that perfo
performance optimizations fail when state drift occurs off-screen?

*Tested with 10 unit tests covering: initial state, offset movement, clampi
clamping at boundaries, `scrollHome`/`scrollEnd`, and reset on force render
render. All passing.*
