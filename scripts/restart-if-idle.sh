#!/bin/bash
# restart-if-idle.sh — launchd-driven restart of the gateway, but ONLY when
# there is a reason to restart.
#
# WHY THIS IS A LAUNCH AGENT AND NOT A BACKGROUND JOB
#   The restart that loads a runtime patch can only happen when the
#   Telegram lane is quiet, and the lane can stay busy for a long time.
#   The first implementation was a background job, and the runtime
#   CANCELLED it on 2026-11-03 at 18:00 — thirty minutes after it was
#   armed — so the patch was never loaded. launchd owns this now: nothing
#   in the agent runtime can stop it.
#
# WHY IT NOW REQUIRES A REASON
#   The first version of this script restarted the gateway "when the lane
#   is idle". That was wrong: idle is the NORMAL state. On 2026-11-04 and
#   2026-11-05 it restarted the gateway 255 times — roughly every nine
#   minutes, for two days. That churned the Telegram plugin's polling,
#   reloaded the runtime for no reason, and kept the restart race (the one
#   that killed messageId 2547) permanently armed.
#
#   A restart must have a REASON. There are exactly two:
#
#     1. A SESSION IS WEDGED. The gateway classified the run
#        stalled_agent_run with recovery=none: it can never deliver a
#        reply, and it blocks the compaction AND the restart that would fix
#        it. Restarting is the release. This is the self-healing case.
#
#     2. THE CACHE-TTL GATE IS NOT EFFECTIVE IN THE RUNNING PROCESS. A
#        marker was written after the gateway started, which means the
#        patch is on disk but the running process still has the old code.
#        Only a restart loads it.
#
#   If neither holds, this script does nothing. That is the normal case,
#   and it is the correct behaviour.
#
# THE IDLE WINDOW STILL MATTERS
#   When there IS a reason, the restart still waits for a quiet lane. The
#   shared guard decides what "idle" means:
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

# --------------------------------------------------------------------------
# REASON 1: a session is wedged.
# --------------------------------------------------------------------------
# shellcheck source=/dev/null
. "$WS/scripts/lib/gateway-restart-guard.sh" 2>/dev/null

REASON=""
if guard_stalled_session; then
    REASON="the Telegram session is wedged (the gateway classified the run stalled_agent_run with recovery=none) — it cannot deliver a reply and it blocks the compaction"
    log "REASON: $REASON"
else
    # --------------------------------------------------------------------------
    # REASON 2: the cache-TTL gate is not effective in the running process.
    # --------------------------------------------------------------------------
    GATE_STATE=$(/opt/homebrew/bin/python3 \
        "$WS/scripts/health/cache-ttl-gate-state.py" --json 2>/dev/null)
    if [ -n "$GATE_STATE" ]; then
        GATE_OK=$(printf '%s' "$GATE_STATE" | /opt/homebrew/bin/python3 -c \
            "import sys,json;print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
        if [ "$GATE_OK" = "pending" ]; then
            REASON="the cache-TTL gate is not effective in the running gateway process — a restart would load it"
            log "REASON: $REASON"
        fi
    fi
fi

if [ -z "$REASON" ]; then
    log "--- run end: no reason to restart (the gateway is healthy; nothing is wedged and the cache-TTL gate is effective) ---"
    exit 0
fi

log "restarting because: $REASON"
if bash "$WS/scripts/restart-and-verify.sh" 4 >> "$LOG" 2>&1; then
    log "--- run end: restart + verification complete ---"
else
    log "--- run end: no restart (the lane was not quiet, or the guard deferred) ---"
fi
