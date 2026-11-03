#!/bin/bash
# Restart the gateway as soon as the Telegram session has been idle for a
# sustained window, then verify that the restart actually fixed things.
#
# WHY THIS WRAPPER EXISTS
#   verify-after-restart.sh has to know the pid the gateway had BEFORE the
#   restart so it can tell "a marker was written after the restart" from
#   "a marker was written before the restart". Chaining the two scripts
#   with `restart-when-idle.sh && verify-after-restart.sh` would start the
#   verifier AFTER the restart, so it would capture the new pid and then
#   wait forever for a second restart. The old pid is captured here,
#   before anything runs.
#
# WHAT THE RESTART IS FOR (2026-11-03)
#   1. Load the widened cache-TTL guard. The gate lives in three
#      separately-bundled files and the running gateway holds the old
#      function in memory. The patch is on disk and behaviourally verified;
#      only a restart loads it.
#   2. Start from a clean process with the compacted tool catalogue
#      (tools.toolSearch) already applied.
#
# Usage: bash scripts/restart-and-verify.sh [idle_checks_required]

set -u
WS="/Users/amre/.openclaw/workspace"

OLD_PID=$(launchctl list | awk '$3=="ai.openclaw.gateway"{print $1}')
echo "$(date '+%H:%M:%S') pre-restart gateway pid=$OLD_PID"

if bash "$WS/scripts/restart-when-idle.sh" "${1:-4}"; then
    echo "$(date '+%H:%M:%S') restart issued — verifying"
    bash "$WS/scripts/verify-after-restart.sh" "$OLD_PID"
else
    echo "$(date '+%H:%M:%S') no idle window was found; nothing was restarted"
    exit 1
fi
