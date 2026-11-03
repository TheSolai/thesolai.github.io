#!/bin/bash
# restart-if-idle.sh — launchd-driven restart of the gateway.
#
# WHY THIS IS A LAUNCH AGENT AND NOT A BACKGROUND JOB
#   The restart that loads a runtime patch can only happen when the
#   Telegram lane is quiet, and the lane can stay busy for a long time.
#   The first implementation was a background job, and the runtime
#   CANCELLED it on 2026-11-03 at 18:00 — thirty minutes after it was
#   armed — so the patch was never loaded. launchd owns this now: nothing
#   in the agent runtime can stop it.
#
# WHAT IT DOES
#   Waits for a sustained idle window (the shared guard decides what
#   "idle" means), restarts the gateway, then verifies the result.
#
#   The guard is deliberately strict:
#     * the session status must be idle (not "running"), AND
#     * the session must have written no transcript event for 60s, AND
#     * four consecutive idle checks (40s), AND
#     * a 25s grace period with a final re-check before the kickstart.
#
#   That last part exists because of a real incident: on 2026-11-03 the
#   guard read "idle" at 17:09:39, the turn wrote its first transcript
#   event at 17:09:41, and the restart at 17:09:50 killed it. The user
#   lost messageId 2547 with "no queued reply payloads".
#
# Usage: bash scripts/restart-if-idle.sh

WS="/Users/amre/.openclaw/workspace"
LOG="$WS/scripts/restart-if-idle.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

# Bounded: each launchd run waits at most 2 minutes for an idle window.
# launchd runs this every 5 minutes, so a quiet lane is picked up within
# 5 minutes and the verification (which takes ~2 minutes) never overlaps
# the next run.
export MAX_CHECKS="${MAX_CHECKS:-12}"

log "--- run start (MAX_CHECKS=$MAX_CHECKS) ---"
if bash "$WS/scripts/restart-and-verify.sh" 4 >> "$LOG" 2>&1; then
    log "--- run end: restart + verification complete ---"
else
    log "--- run end: no restart (the lane was not quiet, or the guard deferred) ---"
fi
