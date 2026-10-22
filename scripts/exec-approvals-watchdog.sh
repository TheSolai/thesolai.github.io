#!/bin/bash
# ============================================================================
# OpenClaw Gateway Health Watchdog — comprehensive self-heal
#
# Catches and repairs ALL known failure modes for this gateway:
#   1. Gateway process dead / not running
#   2. Gateway process alive but FROZEN (macOS maintenance sleep suspension)
#      -> detected via "host timing gap" entries in the gateway log
#   3. caffeinate lost its -s flag (prevents macOS suspending us again)
#   4. exec-approvals.json corrupted (blocks gateway startup)
#   5. Agent SQLite DB bloated (>150MB -> prune + VACUUM)
#
# Runs every 5 min. Logs everything to exec-approvals-watchdog.log (shared log).
# ============================================================================
set -u

STATE_DIR="/Users/amre/.openclaw"
LOG="/Users/amre/.openclaw/workspace/scripts/exec-approvals-watchdog.log"
AGENT_DB="${STATE_DIR}/agents/main/agent/openclaw-agent.sqlite"
EXEC_APPROVALS="${STATE_DIR}/exec-approvals.json"
GATEWAY_LOG_DIR="/tmp/openclaw"
PLIST="/Users/amre/Library/LaunchAgents/ai.openclaw.gateway.plist"
LABEL="ai.openclaw.gateway"
HEALTHZ="http://127.0.0.1:18789/healthz"
NODE="/Users/amre/.openclaw/tools/node-v24.21.0/bin/node"
OC_MJS="${STATE_DIR}/tools/node-v24.21.0/lib/node_modules/openclaw/openclaw.mjs"
MAX_DB_BYTES=$((150 * 1024 * 1024))   # 150MB

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [health-wd] $*" | tee -a "$LOG" >/dev/null; }
bounced=0

# --- helpers ---------------------------------------------------------------
STATE_FILE="${STATE_DIR}/workspace/scripts/.health-wd-state"
COOLDOWN_SECS=600   # don't bounce more than once per 10 min

gateway_pid() { pgrep -f "openclaw/dist/index.js gateway" 2>/dev/null | head -1; }

# last bounce time (epoch), 0 if none
last_bounce_epoch() {
    [ -f "$STATE_FILE" ] || { echo 0; return; }
    grep '^last_bounce=' "$STATE_FILE" 2>/dev/null | tail -1 | cut -d= -f2
}
mark_bounce() { echo "last_bounce=$(date +%s)" >> "$STATE_FILE"; }
in_cooldown() {
    local lb; lb=$(last_bounce_epoch)
    [ "$lb" -gt 0 ] 2>/dev/null || return 1
    [ $(( $(date +%s) - lb )) -lt "$COOLDOWN_SECS" ]
}

# healthz with a retry, because the gateway needs ~5-8s to answer after a bounce
gateway_alive() {
    local pid; pid=$(gateway_pid)
    [ -n "$pid" ] || return 1
    local i code
    for i in 1 2 3; do
        code=$(curl -s -m 6 -o /dev/null -w '%{http_code}' "$HEALTHZ" 2>/dev/null)
        [ "$code" = "200" ] && return 0
        sleep 3
    done
    return 1
}

latest_gateway_log() { ls -t "$GATEWAY_LOG_DIR"/openclaw-*.log 2>/dev/null | head -1; }

# Was a host timing gap (freeze) logged at/after $1 (epoch seconds)?
froze_since() {
    local since="$1"
    local lg; lg=$(latest_gateway_log)
    [ -n "$lg" ] || return 1
    python3 - "$lg" "$since" <<'PY' 2>/dev/null
import json, sys, datetime, re
path, since = sys.argv[1], float(sys.argv[2])
since_dt = datetime.datetime.fromtimestamp(since)
found = False
try:
    with open(path, errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if "host timing gap" not in d.get("message", ""):
                continue
            m = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})", d.get("time", ""))
            if not m:
                continue
            try:
                ts = datetime.datetime.fromisoformat(m.group(1) + "T" + m.group(2))
            except Exception:
                continue
            if ts >= since_dt:
                found = True
                break
except Exception:
    pass
sys.exit(0 if found else 1)
PY
}

bounce_gateway() {
    local why="$1"
    if in_cooldown; then
        log "SKIP bounce ($why) — still in $((${COOLDOWN_SECS}/60))min cooldown"
        return 0
    fi
    bounced=1
    mark_bounce
    log "BOUNCING gateway: $why"
    launchctl bootout gui/501/"$LABEL" 2>/dev/null || true
    sleep 3
    launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true
    # launchd sometimes returns a spurious I/O error on first attempt
    sleep 5
    if ! gateway_alive; then
        log "  first bootstrap didn't take; retrying"
        launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true
        sleep 6
    fi
    if gateway_alive; then
        log "  gateway healthy again (pid $(gateway_pid))"
    else
        log "  !! gateway STILL not healthy after bounce"
    fi
}

# --- 1. exec-approvals.json corruption guard -------------------------------
if [ -f "$EXEC_APPROVALS" ]; then
    content=$(cat "$EXEC_APPROVALS" 2>/dev/null)
    first="${content:0:1}"
    if [ "$first" != "{" ] || ! printf '%s' "$content" | grep -q '"version"'; then
        bak="${STATE_DIR}/state/exec-approvals-bak"
        mkdir -p "$bak"
        ts=$(date +%Y%m%d-%H%M%S)
        log "CORRUPT exec-approvals.json ($(printf '%s' "$content" | head -c 40)) -> archiving"
        mv "$EXEC_APPROVALS" "${bak}/corrupted-${ts}.json" 2>/dev/null || true
        bounce_gateway "corrupt exec-approvals.json archived"
    fi
fi

# --- 2. gateway alive? ------------------------------------------------------
if ! gateway_alive; then
    bounce_gateway "gateway not answering /healthz"
fi

# --- 3. gateway frozen recently? -------------------------------------------
# Only bounce if a freeze was logged AFTER the current gateway process started,
# otherwise an old freeze entry in a stale log would trigger a pointless bounce.
if [ -n "$(gateway_pid)" ] && gateway_alive; then
    gw_start=$(ps -o lstart= -p "$(gateway_pid)" 2>/dev/null | xargs -I{} date -j -f "%a %b %d %T %Y" "{}" +%s 2>/dev/null || echo 0)
    if [ "${gw_start:-0}" -gt 0 ] 2>/dev/null; then
        if froze_since "$gw_start"; then
            log "gateway FROZEN since process start -> bouncing"
            bounce_gateway "freeze detected"
        fi
    fi
fi

# --- 4. caffeinate -s assertion present? ------------------------------------
# The gateway runs under `caffeinate -dims`. If that wrapper is gone, macOS
# will suspend us again. Verify the process command line.
if [ -n "$(gateway_pid)" ]; then
    capid=$(pgrep -f "caffeinate -dims" 2>/dev/null | head -1)
    if [ -z "$capid" ]; then
        log "caffeinate -dims wrapper missing -> restoring from plist"
        launchctl bootout gui/501/"$LABEL" 2>/dev/null || true
        sleep 3
        launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true
        sleep 5
        capid=$(pgrep -f "caffeinate -dims" 2>/dev/null | head -1)
        [ -n "$capid" ] && log "  caffeinate restored (pid $capid)" || log "  !! caffeinate still missing"
    fi
fi

# --- 5. agent DB bloat guard ------------------------------------------------
if [ -f "$AGENT_DB" ]; then
    dbsize=$(stat -f%z "$AGENT_DB" 2>/dev/null || echo 0)
    if [ "$dbsize" -gt "$MAX_DB_BYTES" ]; then
        log "agent DB is ${dbsize} bytes (> 150MB) -> pruning + VACUUM"
        # stop gateway so we don't fight for the write lock
        launchctl bootout gui/501/"$LABEL" 2>/dev/null || true
        sleep 3
        sqlite3 "$AGENT_DB" <<'SQL' >>"$LOG" 2>&1
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
        launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true
        sleep 6
        gateway_alive || { launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true; sleep 4; }
        newsize=$(stat -f%z "$AGENT_DB" 2>/dev/null || echo 0)
        log "  VACUUM done: ${dbsize} -> ${newsize} bytes; gateway $(gateway_alive && echo up || echo DOWN)"
    fi
fi

# --- 6. session context overflow guard --------------------------------------
# A single runaway session can accumulate 10MB+ of transcript, overflow the
# model context window, and make EVERY reply fail with
# `visible channel turn dispatched with no queued reply payloads:
#  cause=skipped:reply_operation_aborted`. Detect an oversized session and
# reset it so the channel recovers without manual intervention.
if gateway_alive; then
    big_sid=$(sqlite3 "$AGENT_DB" "
        SELECT session_id FROM transcript_events
        GROUP BY session_id
        HAVING COUNT(*) > 4000
        ORDER BY COUNT(*) DESC LIMIT 1;" 2>/dev/null)
    if [ -n "$big_sid" ]; then
        cnt=$(sqlite3 "$AGENT_DB" "SELECT COUNT(*) FROM transcript_events WHERE session_id='$big_sid';" 2>/dev/null)
        log "session ${big_sid:0:12}... has $cnt events (>4000) -> context overflow risk, resetting session"
        launchctl bootout gui/501/"$LABEL" 2>/dev/null || true
        sleep 3
        sqlite3 "$AGENT_DB" <<SQL >>"$LOG" 2>&1
PRAGMA busy_timeout = 30000;
PRAGMA foreign_keys = ON;
DELETE FROM session_transcript_active_events WHERE session_id = '$big_sid';
DELETE FROM transcript_event_identities    WHERE session_id = '$big_sid';
DELETE FROM transcript_events             WHERE session_id = '$big_sid';
DELETE FROM session_windows               WHERE session_id = '$big_sid';
INSERT INTO session_transcript_fts(session_transcript_fts) VALUES('rebuild');
PRAGMA wal_checkpoint(TRUNCATE);
VACUUM;
SQL
        launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true
        sleep 6
        gateway_alive || { launchctl bootstrap gui/501 "$PLIST" 2>&1 | tee -a "$LOG" >/dev/null || true; sleep 5; }
        log "  session reset; gateway $(gateway_alive && echo up || echo DOWN)"
    fi
fi

exit 0