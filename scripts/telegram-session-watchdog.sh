#!/bin/bash
# telegram-session-watchdog.sh
#
# Detects and clears a WEDGED Telegram session.
#
# The wedge (2026-10-24, ~90 min of silence): the agent ran a long-lived
# command in the FOREGROUND through the exec tool. That exec task never
# finished, so the session's command-lane queue entry never resolved. The
# lane's queuedCount stayed > 0 forever, which (a) made `sessions compact`
# refuse with "has queued work", and (b) stopped the ingress handler from
# adopting any new Telegram update — messages arrived and were spooled, but
# were never turned into turns. The bot looked dead while the gateway kept
# burning turns and the transcript grew to 5.4 MB.
#
# The command-lane queue lives in gateway memory, so killing the offending
# process is not enough — the gateway must be restarted to clear it.
#
# `tools.exec.timeoutSeconds` (900s) and `tools.exec.backgroundMs` (30s) now
# prevent this in the normal case. This watchdog is the backstop for the
# cases they miss (detached children, execs that outlive their task row).
#
# Usage: telegram-session-watchdog.sh [max_age_seconds]
#   max_age_seconds  a task stuck in 'running' longer than this is a wedge
#                    (default 1200 = 20 min, safely past the 15 min exec cap)

set -u
export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

STATE_DB="/Users/amre/.openclaw/state/openclaw.sqlite"
LOG="/Users/amre/.openclaw/workspace/scripts/telegram-session-watchdog.log"
MAX_AGE="${1:-1200}"
GATEWAY_LABEL="ai.openclaw.gateway"
PLIST="/Users/amre/Library/LaunchAgents/${GATEWAY_LABEL}.plist"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

[ -f "$STATE_DB" ] || { log "state DB missing, nothing to do"; exit 0; }

GATEWAY_LOG="/Users/amre/Library/Logs/openclaw/gateway.log"
KEY="agent:main:telegram:direct:8125193571"

# ---------------------------------------------------------------------------
# Heal 1: a turn that died of a provider-side context overflow.
#
# "embedded run agent end: ... isError=true ... error=Context" means the
# prompt outgrew the context window mid tool-loop. The mid-turn precheck
# cannot catch that (it only checks at prompt build time), the turn aborts,
# and NO reply is delivered — the user just sees silence. Recovery is to
# hard-truncate the transcript so the next turn starts small.
# ---------------------------------------------------------------------------
if [ -f "$GATEWAY_LOG" ]; then
    RECENT_DEATH=$(tail -400 "$GATEWAY_LOG" 2>/dev/null \
        | grep -a "embedded run agent end" \
        | grep -a "isError=true" \
        | grep -a "error=Context" \
        | tail -1)
    if [ -n "$RECENT_DEATH" ]; then
        # Only heal deaths from the last 5 minutes (ISO timestamps sort
        # lexicographically in the same timezone/format).
        STAMP=$(echo "$RECENT_DEATH" | cut -c1-19)
        CUTOFF=$(date -v-5M '+%Y-%m-%dT%H:%M:%S')
        if [[ "$STAMP" > "$CUTOFF" ]]; then
            log "CONTEXT DEATH detected: $(echo "$RECENT_DEATH" | sed 's/\(.\{120\}\).*/\1/')"
            OUT=$(openclaw sessions compact "$KEY" --max-lines 60 2>&1 | tail -2)
            case "$OUT" in
                *"kept "*)   log "  healed: $OUT" ;;
                *)           log "  heal deferred: $(echo "$OUT" | tr '\n' ' ' | cut -c1-140)" ;;
            esac
        fi
    fi
fi

# Tasks stuck in 'running' well past the exec timeout cap.
STUCK=$(sqlite3 "$STATE_DB" "
  SELECT task_id || '|' || replace(task, char(10), ' ')
  FROM task_runs
  WHERE status = 'running'
    AND created_at < (strftime('%s','now') - ${MAX_AGE}) * 1000;
" 2>/dev/null)

if [ -z "$STUCK" ]; then
    exit 0
fi

log "WEDGE DETECTED: $(echo "$STUCK" | wc -l | tr -d ' ') stuck running task(s)"

GATEWAY_PID=$(launchctl list 2>/dev/null | awk -v l="$GATEWAY_LABEL" '$3 == l {print $1}')
if [ -z "$GATEWAY_PID" ] || [ "$GATEWAY_PID" = "-" ]; then
    log "gateway not running; leaving it alone"
    exit 0
fi

# Kill gateway descendants matching each stuck command's executable name.
while IFS='|' read -r TASK_ID TASK_CMD; do
    [ -z "$TASK_ID" ] && continue
    BASE=$(echo "$TASK_CMD" | awk '{print $NF}' | xargs basename 2>/dev/null)
    [ -z "$BASE" ] && continue
    log "  task $TASK_ID -> matching processes for '$BASE'"
    for PID in $(pgrep -P "$GATEWAY_PID" 2>/dev/null); do
        CMDLINE=$(ps -p "$PID" -o command= 2>/dev/null)
        case "$CMDLINE" in
            *"$BASE"*)
                log "  killing pid $PID ($CMDLINE)"
                kill -TERM "$PID" 2>/dev/null
                ;;
        esac
    done
    sqlite3 "$STATE_DB" "UPDATE task_runs SET status='failed', ended_at=strftime('%s','now')*1000, error='wedge cleared by watchdog' WHERE task_id='$TASK_ID';" 2>/dev/null
done <<EOF
$STUCK
EOF

sleep 2
log "restarting gateway to clear the wedged command lane"
launchctl kickstart -k "gui/501/${GATEWAY_LABEL}" 2>&1 | tail -2
log "watchdog action complete"
exit 0
