#!/bin/bash
# OpenClaw agent DB weekly maintenance
# Prunes transcript events older than 30 days and runs VACUUM to compact.
# Prevents the 9-16 min SQLite lock freezes caused by 100MB+ of bloat.
# Schedule: weekly via ai.sol.agent-db-vacuum LaunchAgent
set -eu

DB="/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite"
LOG="/Users/amre/.openclaw/workspace/scripts/agent-db-vacuum.log"
GATEWAY_LABEL="ai.openclaw.gateway"
PLIST="/Users/amre/Library/LaunchAgents/${GATEWAY_LABEL}.plist"

# Shared restart guard. This script STOPS the gateway to release the SQLite
# write lock, and the gateway's shutdown drain is only 5 seconds — so a stop
# here kills any in-flight Telegram turn ("couldn't produce or deliver a
# reply"). Never stop the gateway while a turn is live.
GUARD_LIB="/Users/amre/.openclaw/workspace/scripts/lib/gateway-restart-guard.sh"
# shellcheck source=/dev/null
[ -f "$GUARD_LIB" ] && . "$GUARD_LIB"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG" ; }

if [ ! -f "$DB" ]; then
    log "WARN: $DB not found"
    exit 0
fi

# Wait for any live Telegram turn to finish before stopping the gateway.
# Bounded: after MAX_WAIT seconds we proceed anyway, because a permanently
# blocked DB is a worse outcome than one dropped reply, and the next weekly
# run will try again.
MAX_WAIT="${MAX_WAIT:-600}"
if [ -n "${GUARD_LIB:-}" ]; then
    waited=0
    while [ "$waited" -lt "$MAX_WAIT" ]; do
        if restart_allowed "agent DB vacuum"; then
            break
        fi
        if [ "$waited" -eq 0 ]; then
            log "A Telegram turn is live — waiting up to ${MAX_WAIT}s before stopping the gateway"
        fi
        sleep 30
        waited=$(( waited + 30 ))
    done
    if [ "$waited" -ge "$MAX_WAIT" ]; then
        log "WARN: a Telegram turn is still live after ${MAX_WAIT}s — proceeding anyway (the DB lock matters more)"
    fi
fi

log "=== Weekly agent DB maintenance starting ==="
SIZE_BEFORE=$(stat -f%z "$DB" 2>/dev/null || echo 0)
log "Size before: $(du -h "$DB" | awk '{print $1}')"

# 1. Stop the gateway to release SQLite locks
log "Stopping gateway..."
launchctl bootout gui/501/${GATEWAY_LABEL} 2>&1 | tee -a "$LOG" || log "bootout returned non-zero (may be already stopped)"
sleep 3

# 2. Run maintenance
sqlite3 "$DB" <<'SQL' 2>&1 | tee -a "$LOG"
PRAGMA busy_timeout = 30000;
PRAGMA foreign_keys = ON;
DELETE FROM transcript_events WHERE created_at < strftime('%s','now','-30 days')*1000;
DELETE FROM session_transcript_active_events WHERE (session_id, event_seq) NOT IN (SELECT session_id, seq FROM transcript_events);
DELETE FROM transcript_event_identities WHERE (session_id, seq) NOT IN (SELECT session_id, seq FROM transcript_events);
DELETE FROM trajectory_runtime_events WHERE created_at < strftime('%s','now','-30 days')*1000;
INSERT INTO session_transcript_fts(session_transcript_fts) VALUES('rebuild');
PRAGMA wal_checkpoint(TRUNCATE);
VACUUM;
PRAGMA wal_checkpoint(TRUNCATE);
SQL

# 3. Restart the gateway
log "Starting gateway..."
if launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG"; then
    log "Gateway bootstrap succeeded"
else
    log "Gateway bootstrap failed - check launchd"
    launchctl kickstart -k gui/501/${GATEWAY_LABEL} 2>/dev/null || true
fi

SIZE_AFTER=$(stat -f%z "$DB" 2>/dev/null || echo 0)
log "Size after: $(du -h "$DB" | awk '{print $1}')"
if [ "$SIZE_BEFORE" -gt 0 ] && [ "$SIZE_AFTER" -gt 0 ]; then
    SAVED=$((SIZE_BEFORE - SIZE_AFTER))
    log "Reclaimed: ${SAVED} bytes ($(( SAVED * 100 / SIZE_BEFORE ))%)"
fi
log "=== Maintenance complete ==="
