#!/bin/bash
# telegram-session-watchdog.sh
#
# Keeps the OpenClaw Telegram bot alive. Three failure modes it heals:
#
#   1. NETWORK / DNS FAILURE  (the persistent one)
#      The Mac sleeps on lid close. On wake, macOS can be left with only a
#      fragile IPv6 link-local resolver (fe80::...%en0) and no IPv4 fallback,
#      so `getaddrinfo` for api.minimax.io returns ENOTFOUND. Every LLM call
#      then fails, every turn dies with
#        "LLM request failed: DNS lookup for the provider endpoint failed"
#      and the bot delivers nothing. The gateway does not recover by itself —
#      its connection pool holds stale state.
#      FIX: if the provider hostname does not resolve, restart the gateway so
#      it re-resolves from scratch. The check is ACTIVE (we resolve the name
#      ourselves), not log-scraping.
#
#   2. A WEDGED SESSION
#      A foreground long-running command through the exec tool never exits, so
#      the session's command-lane queue entry never resolves. The lane's
#      queuedCount stays > 0 forever, which (a) makes `sessions compact`
#      refuse with "has queued work" and (b) stops the ingress handler from
#      adopting any new Telegram update. Messages arrive and are spooled but
#      never become turns — the bot looks dead while the gateway burns turns.
#      FIX: kill the offending process, fail the task row, restart the gateway
#      (the lane queue is in gateway memory, so a restart is the only way to
#      clear it).
#
#   3. A TURN THAT DIED OF A PROVIDER-SIDE CONTEXT OVERFLOW
#      "embedded run agent end: ... isError=true ... error=Context" aborts the
#      turn and NO reply is delivered. The mid-turn precheck cannot catch it
#      because it only checks at prompt-build time.
#      FIX: hard-truncate the transcript so the next turn starts small.
#
# Usage: telegram-session-watchdog.sh [stuck_task_max_age_seconds]
#   default 1200 (20 min, safely past the 15 min exec timeout cap)

set -u
export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

STATE_DB="/Users/amre/.openclaw/state/openclaw.sqlite"
GATEWAY_LOG="/Users/amre/Library/Logs/openclaw/gateway.log"
LOG="/Users/amre/.openclaw/workspace/scripts/telegram-session-watchdog.log"
GATEWAY_LABEL="ai.openclaw.gateway"
KEY="agent:main:telegram:direct:8125193571"
PROVIDER_HOST="api.minimax.io"
MAX_AGE="${1:-1200}"
MIN_RESTART_GAP=600   # at most one restart per 10 minutes

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

gateway_pid() { launchctl list 2>/dev/null | awk -v l="$GATEWAY_LABEL" '$3 == l {print $1}'; }

restart_gateway() {
    local pid; pid=$(gateway_pid)
    if [ -z "$pid" ] || [ "$pid" = "-" ]; then
        log "  gateway not running — launchd KeepAlive will start it"
        return 0
    fi
    log "GATEWAY-RESTART pid=$pid reason=watchdog"
    launchctl kickstart -k "gui/501/${GATEWAY_LABEL}" 2>&1 | tail -1
}

rate_limited() {
    local last now_epoch last_epoch
    # Match ONLY the restart marker — never a prose line that happens to
    # mention restarting, or the limiter blocks itself.
    last=$(grep -a "GATEWAY-RESTART" "$LOG" 2>/dev/null | tail -1 | cut -d' ' -f1,2 | tr '\n' ' ')
    last=$(echo "$last" | sed 's/ *$//')
    # No previous restart recorded -> not rate limited.
    [ -z "$last" ] && return 1
    now_epoch=$(date '+%s')
    last_epoch=$(date -j -f '%Y-%m-%d %H:%M:%S' "$last" '+%s' 2>/dev/null) || return 0
    [ $(( now_epoch - last_epoch )) -lt "$MIN_RESTART_GAP" ]
}

# ---------------------------------------------------------------------------
# Heal 1: the Mac slept (clamshell) and the gateway came back with stale
#         network state.
#
# The Mac sleeps when the lid closes. On wake, macOS can be left with only a
# fragile IPv6 link-local resolver and the gateway's connection pool holds
# stale sockets, so every LLM call fails with
#   "LLM request failed: DNS lookup for the provider endpoint failed"
# (getaddrinfo ENOTFOUND api.minimax.io) and the bot delivers nothing.
# The gateway does not recover on its own.
#
# FIX: if the machine has woken since the gateway started, restart the
# gateway so it re-resolves and rebuilds its connections.
# ---------------------------------------------------------------------------
gateway_start_epoch() {
    local pid; pid=$(gateway_pid)
    [ -z "$pid" ] || [ "$pid" = "-" ] && return 1
    local lstart; lstart=$(ps -p "$pid" -o lstart= 2>/dev/null | sed 's/^ *//')
    [ -z "$lstart" ] && return 1
    date -j -f '%a %b %e %H:%M:%S %Y' "$lstart" '+%s' 2>/dev/null
}

last_wake_epoch() {
    local line; line=$(pmset -g log 2>/dev/null | grep -aE "^20[0-9]{2}-[0-9]{2}-[0-9]{2} [0-9:]+ .*Wake " | tail -1)
    [ -z "$line" ] && return 1
    local stamp; stamp=$(echo "$line" | cut -d' ' -f1,2)
    date -j -f '%Y-%m-%d %H:%M:%S' "$stamp" '+%s' 2>/dev/null
}

GW_START=$(gateway_start_epoch) || GW_START=""
LAST_WAKE=$(last_wake_epoch) || LAST_WAKE=""
if [ -n "$GW_START" ] && [ -n "$LAST_WAKE" ] && [ "$LAST_WAKE" -gt "$GW_START" ]; then
    log "WAKE DETECTED: machine woke after the gateway started (wake $LAST_WAKE > start $GW_START) — restarting gateway for fresh DNS/connections"
    if ! rate_limited; then
        restart_gateway
    else
        log "  restart rate-limited"
    fi
    exit 0
fi

# ---------------------------------------------------------------------------
# Heal 1b: Telegram is holding messages that we are not consuming.
#
# getWebhookInfo's pending_update_count is the count of updates Telegram has
# NOT yet handed to a getUpdates caller. Our poller long-polls continuously,
# so a sustained non-zero count means the poller is dead or wedged — the
# user's messages are sitting in Telegram and nothing is arriving. Require it
# to persist for PENDING_GRACE seconds before acting, so a momentary blip
# does not trigger a restart.
# ---------------------------------------------------------------------------
PENDING_FILE="/Users/amre/.openclaw/workspace/scripts/.telegram-pending-since"
PENDING_GRACE=180

TOKEN=$(python3 -c "
import json
try:
    print(json.load(open('/Users/amre/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])
except Exception:
    print('')
" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    PENDING=$(curl -s -m 15 "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" 2>/dev/null \
        | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(d['result']['pending_update_count'] if d.get('ok') else 0)
except Exception:
    print(0)
" 2>/dev/null)
    case "$PENDING" in
        ''|*[!0-9]*) PENDING=0 ;;
    esac
    if [ "$PENDING" -gt 0 ]; then
        if [ ! -f "$PENDING_FILE" ]; then
            date '+%s' > "$PENDING_FILE"
            log "TELEGRAM PENDING: $PENDING update(s) waiting — starting ${PENDING_GRACE}s grace timer"
        else
            FIRST=$(cat "$PENDING_FILE" 2>/dev/null)
            NOW=$(date '+%s')
            if [ -n "$FIRST" ] && [ $(( NOW - FIRST )) -ge "$PENDING_GRACE" ]; then
                log "TELEGRAM PENDING: $PENDING update(s) stuck for $(( NOW - FIRST ))s — poller is dead, restarting gateway"
                if ! rate_limited; then
                    restart_gateway
                else
                    log "  restart rate-limited"
                fi
                rm -f "$PENDING_FILE"
                exit 0
            fi
        fi
    else
        rm -f "$PENDING_FILE"
    fi
fi

# ---------------------------------------------------------------------------
# Heal 1c: DNS genuinely broken right now.
# Restarting cannot fix a broken resolver, so only log it — the gateway is
# restarted by the wake check above once connectivity returns.
# ---------------------------------------------------------------------------
if ! /usr/bin/dig +short +time=3 +tries=1 A "$PROVIDER_HOST" 2>/dev/null \
     | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'; then
    log "DNS DOWN: '$PROVIDER_HOST' does not resolve — provider calls will fail until the resolver recovers"
    exit 0
fi

# ---------------------------------------------------------------------------
# Heal 2: context-overflow turn death -> truncate the transcript
# ---------------------------------------------------------------------------
if [ -f "$GATEWAY_LOG" ]; then
    RECENT_DEATH=$(tail -600 "$GATEWAY_LOG" 2>/dev/null \
        | grep -a "embedded run agent end" | grep -a "isError=true" | grep -a "error=Context" | tail -1)
    if [ -n "$RECENT_DEATH" ]; then
        STAMP=$(echo "$RECENT_DEATH" | cut -c1-19)
        CUTOFF=$(date -v-5M '+%Y-%m-%dT%H:%M:%S')
        if [[ "$STAMP" > "$CUTOFF" ]]; then
            log "CONTEXT DEATH detected: $(echo "$RECENT_DEATH" | sed 's/\(.\{110\}\).*/\1/')"
            OUT=$(openclaw sessions compact "$KEY" --max-lines 60 2>&1 | tail -2)
            case "$OUT" in
                *"kept "*) log "  healed: $OUT" ;;
                *)         log "  heal deferred: $(echo "$OUT" | tr '\n' ' ' | cut -c1-130)" ;;
            esac
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Heal 3: wedged session (a command that never ends)
# ---------------------------------------------------------------------------
[ -f "$STATE_DB" ] || exit 0

# Only tasks owned by a Telegram session can wedge the Telegram lane.
# Cron/automation tasks run in ISOLATED sessions — a long-running one (the
# "Memory Dreaming Promotion" cron legitimately takes ~21 min) must NOT be
# killed. Do not widen this.
STUCK=$(sqlite3 "$STATE_DB" "
  SELECT task_id || '|' || replace(task, char(10), ' ')
  FROM task_runs
  WHERE status = 'running'
    AND owner_key LIKE 'agent:main:telegram:%'
    AND created_at < (strftime('%s','now') - ${MAX_AGE}) * 1000;
" 2>/dev/null)

[ -z "$STUCK" ] && exit 0

log "WEDGE DETECTED: $(echo "$STUCK" | wc -l | tr -d ' ') stuck running task(s)"
GATEWAY_PID=$(gateway_pid)
if [ -z "$GATEWAY_PID" ] || [ "$GATEWAY_PID" = "-" ]; then
    log "  gateway not running; leaving it alone"
    exit 0
fi

while IFS='|' read -r TASK_ID TASK_CMD; do
    [ -z "$TASK_ID" ] && continue
    BASE=$(echo "$TASK_CMD" | awk '{print $NF}' | xargs basename 2>/dev/null)
    [ -z "$BASE" ] && continue
    log "  task $TASK_ID -> matching processes for '$BASE'"
    for PID in $(pgrep -P "$GATEWAY_PID" 2>/dev/null); do
        CMDLINE=$(ps -p "$PID" -o command= 2>/dev/null)
        case "$CMDLINE" in
            *"$BASE"*) log "  killing pid $PID"; kill -TERM "$PID" 2>/dev/null ;;
        esac
    done
    sqlite3 "$STATE_DB" "UPDATE task_runs SET status='failed', ended_at=strftime('%s','now')*1000, error='wedge cleared by watchdog' WHERE task_id='$TASK_ID';" 2>/dev/null
done <<EOF
$STUCK
EOF

sleep 2
restart_gateway
log "watchdog action complete"
exit 0
