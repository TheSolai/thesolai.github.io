#!/bin/bash
# Restart the gateway as soon as the Telegram session has been idle for a
# sustained window.
#
# WHY "SUSTAINED" AND NOT "INstantLY IDLE"
#   On 2026-11-03 the first version of this waiter restarted the moment the
#   session read "idle". It did not stick: the queued messages were adopted
#   microseconds later, and the guard's own re-check inside
#   safe_restart_gateway saw a live turn and refused:
#
#       15:44:25 telegram idle — restarting to load the cache-TTL worker patch
#       restart_allowed: DEFERRED — a Telegram turn is live
#
#   That refusal is the fail-safe working exactly as designed — trusting the
#   earlier "idle" reading would have killed a live turn, which is the bug
#   that broke replies on 2026-10-28. The fix is to require the session to
#   stay idle across several consecutive checks. If work is queued, it is
#   adopted within seconds and the counter resets, so the restart only
#   happens in a genuinely quiet window.
#
# WHAT THIS IS FOR
#   Load the cache-TTL patch. The gate `isCacheTtlEligibleProvider` exists in
#   THREE separately-bundled files and the agent turns run in the worker,
#   whose module is cached in the gateway process. The patch is on disk in
#   all three copies, but only a gateway restart loads it. Until that
#   happens every attempt appends an `openclaw.cache-ttl` marker and the
#   session window inflates with pure bookkeeping.
#
# Usage: bash scripts/restart-when-idle.sh [idle_checks_required]

. /Users/amre/.openclaw/workspace/scripts/lib/gateway-restart-guard.sh

REQUIRED_IDLE_CHECKS="${1:-4}"   # 4 checks x 10s = 40s of continuous idleness
POLL_SECONDS=10
MAX_CHECKS="${MAX_CHECKS:-720}"  # 2 hours

idle_streak=0
echo "$(date '+%H:%M:%S') waiting for ${REQUIRED_IDLE_CHECKS} consecutive idle checks (${REQUIRED_IDLE_CHECKS}x${POLL_SECONDS}s)"

for i in $(seq 1 "$MAX_CHECKS"); do
    if telegram_turn_live; then
        if [ "$idle_streak" -gt 0 ]; then
            echo "$(date '+%H:%M:%S') turn became live again — resetting idle streak"
        fi
        idle_streak=0
    else
        idle_streak=$(( idle_streak + 1 ))
        echo "$(date '+%H:%M:%S') idle ${idle_streak}/${REQUIRED_IDLE_CHECKS}"
        if [ "$idle_streak" -ge "$REQUIRED_IDLE_CHECKS" ]; then
            echo "$(date '+%H:%M:%S') sustained idle window — restarting to load the cache-TTL worker patch"
            if safe_restart_gateway "load cache-TTL worker patch"; then
                echo "$(date '+%H:%M:%S') restart issued"
                exit 0
            fi
            echo "$(date '+%H:%M:%S') restart deferred by the guard — retrying"
            idle_streak=0
        fi
    fi
    sleep "$POLL_SECONDS"
done

echo "$(date '+%H:%M:%S') gave up waiting"
exit 1
