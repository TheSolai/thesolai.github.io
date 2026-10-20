#!/bin/bash
# OpenClaw exec-approvals.json self-healing watchdog
# Detects when the file is corrupted to non-object JSON (e.g. []) and:
#   1. Archives the corrupt file
#   2. Runs openclaw doctor --fix to clean up
#   3. Bounces the gateway so it picks up the new state
# Runs every 5 minutes via ai.sol.exec-approvals-watchdog launchd agent.
set -eu

STATE_DIR="/Users/amre/.openclaw"
FILE="${STATE_DIR}/exec-approvals.json"
BACKUP_DIR="${STATE_DIR}/state/exec-approvals-bak"
LOG="/Users/amre/.openclaw/workspace/scripts/exec-approvals-watchdog.log"
GATEWAY_NODE="/Users/amre/.openclaw/tools/node-v24.21.0/bin/node"
GATEWAY_OPENCLAW="${STATE_DIR}/tools/node-v24.21.0/lib/node_modules/openclaw/openclaw.mjs"
PLIST="/Users/amre/Library/LaunchAgents/ai.openclaw.gateway.plist"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG" ; }

# 1. If file does not exist, that's the desired steady state. Cache the absence.
if [ ! -f "$FILE" ]; then
    exit 0
fi

# 2. File exists. Validate it: must be a JSON object with a "version" field.
CONTENT=""
if ! CONTENT=$(cat "$FILE" 2>/dev/null); then
    log "WARN: cannot read $FILE (permissions?)"
    exit 0
fi

FIRST_CHAR="${CONTENT:0:1}"
if [ "$FIRST_CHAR" = "{" ] && echo "$CONTENT" | grep -q '"version"'; then
    # valid: object with version field. Nothing to do.
    exit 0
fi

# 3. File is corrupt. Repair.
log "CORRUPTED: $FILE contains $(echo -n "$CONTENT" | head -c 80 | tr '\n' ' ')..."
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d-%H%M%S)
mv "$FILE" "${BACKUP_DIR}/corrupted-${TS}.json"
log "Moved corrupt file to ${BACKUP_DIR}/corrupted-${TS}.json"

# 4. Run doctor --fix to clear migration state (with 3-min timeout to prevent hangs)
log "Running: openclaw doctor --fix (timeout 180s)"
if /usr/bin/timeout 180 "$GATEWAY_NODE" "$GATEWAY_OPENCLAW" doctor --fix >> "$LOG" 2>&1; then
    log "doctor --fix completed"
elif [ $? -eq 124 ]; then
    log "doctor --fix timed out after 180s; continuing"
else
    log "doctor --fix returned non-zero (may be expected if no migrations pending)"
fi

# 5. Bounce the gateway so it picks up the absence
log "Bouncing gateway..."
launchctl bootout gui/501/ai.openclaw.gateway 2>/dev/null || true
sleep 2
if launchctl bootstrap gui/501 "$PLIST" >> "$LOG" 2>&1; then
    log "Gateway bootstrap succeeded"
else
    log "Gateway bootstrap failed - check launchd"
    # Try a kickstart as fallback
    launchctl kickstart -k gui/501/ai.openclaw.gateway 2>/dev/null || true
fi

log "Watchdog run complete"
