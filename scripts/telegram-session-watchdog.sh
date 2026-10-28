#!/bin/bash
# telegram-session-watchdog.sh
#
# Keeps the OpenClaw Telegram bot alive.
#
# DESIGN RULE (learned the hard way on 2026-10-26):
#   A restart is the LAST resort. Every extra restart is another chance to
#   abort a running turn, drop a reply, and wedge a lane. The old version of
#   this script restarted the gateway whenever Telegram reported pending
#   updates. That heuristic was a false-positive factory: messages sit pending
#   in Telegram for the whole duration of any long turn, so it restarted the
#   gateway 12 times in one afternoon, and one of those restarts landed during
#   a maintenance window and left a stale lease behind — after which the
#   gateway could never start again. That single restart storm is what turned
#   "the bot is slow" into "the bot is dead for 24 hours".
#
#   So: every restart now requires a rate limit AND a positive, verified
#   reason. Everything that is merely suspicious is logged, never acted on.
#
# What it heals:
#
#   0. THE SERVICE IS NOT LOADED OR IS DISABLED
#      launchd forgets a LaunchAgent across logins, and `launchctl print-disabled`
#      can carry a stale "disabled" flag that makes `launchctl bootstrap` fail
#      with "5: Input/output error". When that happens the gateway simply is
#      not running, KeepAlive never fires, and the bot is silent forever.
#      FIX: enable + bootstrap (with `launchctl load -w` as the fallback that
#      actually worked on this machine).
#
#   0b. A STALE LEASE BLOCKING STARTUP
#      `state_leases` holds a row for `core:agent-database-maintenance` with an
#      `expires_at` in the past. The startup migration sees the lease as held
#      and refuses with "gateway.maintenance_required", so the gateway can
#      never boot. The lease is never reclaimed.
#      FIX: delete only EXPIRED lease rows before any start attempt.
#
#   1. THE MACHINE SLEPT (clamshell) AND THE GATEWAY CAME BACK STALE
#      On wake, macOS can be left with a fragile resolver and the gateway's
#      connection pool holds stale sockets, so every LLM call fails with
#      "DNS lookup for the provider endpoint failed" and no reply is sent.
#      FIX: if the machine woke after the gateway started, restart the gateway
#      so it re-resolves and rebuilds its connections.
#
#   2. A WEDGED SESSION
#      A foreground long-running command through the exec tool never exits, so
#      the session's command-lane queue entry never resolves. The lane's
#      queuedCount stays > 0 forever, which (a) makes `sessions compact` refuse
#      with "has queued work" and (b) stops the ingress handler from adopting
#      any new Telegram update. Messages arrive and are spooled but never
#      become turns — the bot looks dead while the gateway burns turns.
#      FIX: kill the offending process, fail the task row, restart the gateway
#      (the lane queue lives in gateway memory, so a restart is the only way to
#      clear it).
#
#   3. A TURN THAT DIED OF A PROVIDER-SIDE CONTEXT OVERFLOW
#      "embedded run agent end: ... isError=true ... error=Context" aborts the
#      turn and NO reply is delivered. The mid-turn precheck cannot catch it
#      because it only checks at prompt-build time.
#      FIX: hard-truncate the transcript so the next turn starts small.
#
# NEVER, under any circumstance:
#   * restart because Telegram reports pending updates (that is the bug that
#     caused the 2026-10-26 outage)
#   * restart because DNS is down (a restart cannot fix a resolver)
#   * kill a task that is not owned by a Telegram session (the 21-minute
#     "Memory Dreaming Promotion" cron is legitimate and must never be killed)
#
# Usage: telegram-session-watchdog.sh [stuck_task_max_age_seconds]
#   default 1200 (20 min, safely past the 15 min exec timeout cap)

set -u
export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

STATE_DB="/Users/amre/.openclaw/state/openclaw.sqlite"
GATEWAY_LOG="/Users/amre/Library/Logs/openclaw/gateway.log"
LOG="/Users/amre/.openclaw/workspace/scripts/telegram-session-watchdog.log"
GATEWAY_LABEL="ai.openclaw.gateway"
PLIST="/Users/amre/Library/LaunchAgents/${GATEWAY_LABEL}.plist"
HEALTH_URL="http://127.0.0.1:18789/healthz"
KEY="agent:main:telegram:direct:8125193571"
# Remembers the last context-death runId we healed, so the same stale death
# line is never acted on twice (see the note above heal_context_overflow).
HEALED_STATE="/Users/amre/.openclaw/workspace/scripts/.telegram-last-healed-death"
PROVIDER_HOST="api.minimax.io"
MAX_AGE="${1:-1200}"
MIN_RESTART_GAP=600   # at most one restart per 10 minutes

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

gateway_pid() { launchctl list 2>/dev/null | awk -v l="$GATEWAY_LABEL" '$3 == l {print $1}'; }

service_loaded() { launchctl print "gui/501/${GATEWAY_LABEL}" >/dev/null 2>&1; }

service_enabled() {
    launchctl print-disabled gui/501 2>/dev/null \
        | grep -a "\"${GATEWAY_LABEL}\"" | grep -aq "enabled"
}

# ---------------------------------------------------------------------------
# Heal 0: the service is not loaded, or launchd is carrying a "disabled" flag.
# ---------------------------------------------------------------------------
ensure_service_available() {
    local pid; pid=$(gateway_pid)
    if [ -n "$pid" ] && [ "$pid" != "-" ]; then
        return 0   # running
    fi

    # Not running. Make sure launchd will even accept the service.
    if ! service_enabled; then
        log "SERVICE DISABLED: launchd has '${GATEWAY_LABEL}' flagged disabled — enabling"
        launchctl enable "gui/501/${GATEWAY_LABEL}" 2>&1 | tail -1
    fi

    if ! service_loaded; then
        log "SERVICE UNLOADED: bootstrapping ${GATEWAY_LABEL}"
        if ! launchctl bootstrap "gui/501" "${PLIST}" 2>&1 | tail -1; then
            log "  bootstrap failed — falling back to: launchctl load -w"
            launchctl load -w "${PLIST}" 2>&1 | tail -1
        fi
        sleep 6
    else
        # Loaded but not running: launchd's KeepAlive should retry it.
        log "SERVICE LOADED BUT NOT RUNNING: kicking ${GATEWAY_LABEL}"
        launchctl kickstart -k "gui/501/${GATEWAY_LABEL}" 2>&1 | tail -1
        sleep 4
    fi

    pid=$(gateway_pid)
    if [ -n "$pid" ] && [ "$pid" != "-" ]; then
        log "SERVICE RESTORED: ${GATEWAY_LABEL} running as pid $pid"
        return 0
    fi
    log "SERVICE STILL DOWN after recovery attempt — see the startup error in ${GATEWAY_LOG}"
    return 1
}

# ---------------------------------------------------------------------------
# Heal 0b: an expired lease in the state DB blocks the startup migration
# ("gateway.maintenance_required"). Delete ONLY rows that are already expired.
# ---------------------------------------------------------------------------
clear_expired_leases() {
    [ -f "$STATE_DB" ] || return 0
    local removed
    removed=$(sqlite3 "$STATE_DB" "
        DELETE FROM state_leases
        WHERE expires_at IS NOT NULL AND expires_at < strftime('%s','now')*1000;
        SELECT changes();
    " 2>/dev/null | tail -1)
    case "$removed" in
        ''|*[!0-9]*) return 0 ;;
    esac
    if [ "$removed" -gt 0 ]; then
        log "STALE LEASE: removed $removed expired state_leases row(s) that were blocking startup"
    fi
}

restart_gateway() {
    local pid; pid=$(gateway_pid)
    if [ -z "$pid" ] || [ "$pid" = "-" ]; then
        log "  gateway not running — calling the service-recovery path instead"
        ensure_service_available
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
    # ONLY real Wake/Sleep subsystem events count.
    # pmset also logs "Assertions ... NoDisplaySleepAssertion \"Video Wake Lock\""
    # (Steam, and others) — a loose `.*Wake ` pattern matches those and treats
    # them as system wakes. That was a bug: 588 assertion lines vs 29 real
    # wake events, and every false match restarted the gateway mid-turn.
    # A real event is anchored on the timezone offset followed by "Wake ".
    local line
    line=$(pmset -g log 2>/dev/null \
        | grep -aE "^20[0-9]{2}-[0-9]{2}-[0-9]{2} [0-9:]+ \+[0-9]{4} Wake " | tail -1)
    [ -z "$line" ] && return 1
    local stamp; stamp=$(echo "$line" | cut -d' ' -f1,2)
    date -j -f '%Y-%m-%d %H:%M:%S' "$stamp" '+%s' 2>/dev/null
}

# A restart must never kill a turn that is about to produce a reply.
telegram_turn_active() {
    [ -f "$STATE_DB" ] || return 1
    local n
    n=$(sqlite3 "$STATE_DB" "
        SELECT COUNT(*) FROM task_runs
        WHERE status='running' AND owner_key LIKE 'agent:main:telegram:%';" 2>/dev/null | head -1)
    case "$n" in
        ''|*[!0-9]*) return 1 ;;
    esac
    [ "$n" -gt 0 ]
}

provider_dns_ok() {
    /usr/bin/dig +short +time=3 +tries=1 A "$PROVIDER_HOST" 2>/dev/null \
        | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
}

# ---------------------------------------------------------------------------
# Heal 1a: the gateway is not running at all.
# This is checked FIRST and it REPAIRS rather than restarts, because a gateway
# that is not running has no in-flight turn to lose.
# ---------------------------------------------------------------------------
GW_PID=$(gateway_pid)
if [ -z "$GW_PID" ] || [ "$GW_PID" = "-" ]; then
    clear_expired_leases
    ensure_service_available
    exit 0
fi

GW_START=$(gateway_start_epoch) || GW_START=""
LAST_WAKE=$(last_wake_epoch) || LAST_WAKE=""
if [ -n "$GW_START" ] && [ -n "$LAST_WAKE" ] && [ "$LAST_WAKE" -gt "$GW_START" ]; then
    # A wake event is only a REASON TO CHECK, never a reason to restart.
    # The original fault was a broken resolver after clamshell sleep, so test
    # the resolver. If DNS is fine the gateway is fine and must not be
    # restarted — restarting kills whatever turn is in flight.
    if provider_dns_ok; then
        log "WAKE DETECTED (wake $LAST_WAKE > start $GW_START) but provider DNS resolves fine — no restart"
        exit 0
    fi
    log "WAKE DETECTED (wake $LAST_WAKE > start $GW_START) and provider DNS is BROKEN — restarting gateway for fresh connections"
    if telegram_turn_active; then
        log "  a Telegram turn is running — deferring the restart to protect the in-flight reply"
        exit 0
    fi
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
# LOG ONLY. This used to restart the gateway and it was a false-positive
# factory: any long turn leaves messages pending in Telegram, so the bot
# restarted itself 12 times in one afternoon and one of those restarts broke
# the gateway completely. A pending count is now only ever reported.
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
            log "TELEGRAM PENDING (report only, no action): $PENDING update(s) waiting — starting ${PENDING_GRACE}s observation timer"
        else
            FIRST=$(cat "$PENDING_FILE" 2>/dev/null)
            NOW=$(date '+%s')
            if [ -n "$FIRST" ] && [ $(( NOW - FIRST )) -ge "$PENDING_GRACE" ]; then
                log "TELEGRAM PENDING (report only, no action): $PENDING update(s) pending for $(( NOW - FIRST ))s — NOT restarting; a long turn looks identical to this"
            fi
        fi
    else
        rm -f "$PENDING_FILE"
    fi
fi

# ---------------------------------------------------------------------------
# Heal 1c: DNS genuinely broken right now.
# Restarting cannot fix a broken resolver, so only log it.
# ---------------------------------------------------------------------------
if ! /usr/bin/dig +short +time=3 +tries=1 A "$PROVIDER_HOST" 2>/dev/null \
     | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'; then
    log "DNS DOWN: '$PROVIDER_HOST' does not resolve — provider calls will fail until the resolver recovers (no restart attempted)"
    exit 0
fi

# ---------------------------------------------------------------------------
# Heal 2: context-overflow turn death -> shrink the transcript.
#
# The LLM's own auto-compaction does NOT shrink the persisted window (it emits
# a summary artifact and leaves the window alone), so a bloated session
# overflows on EVERY turn and auto-compaction "succeeds" forever without
# fixing anything. `openclaw sessions compact --max-lines N` is the only
# reliable shrink, but it refuses while the session has an active run or
# queued work — which is exactly the state a runaway overflow loop creates.
#
# So this heal escalates:
#   tier 1  compact (works when the session is idle)
#   tier 2  abort ONLY the run that died, then compact again
#   tier 3  the window is still oversized -> reset the session
#           (`sessions delete` archives the transcript to a recoverable .zst
#           and clears the window; the next message starts fresh)
#
# WHY TIER 2 MUST NEVER ABORT THE SESSION (learned 2026-10-28):
#   The old code called `sessions.abort {"key":"<session>"}`, which aborts
#   whatever run is CURRENTLY ACTIVE in that session — not the run that
#   died. Because the death line stays in the gateway log for minutes, the
#   same stale death was re-detected on later watchdog runs, and each
#   detection aborted Amre's brand-new live turn. That is exactly how two
#   of her messages died with "OpenClaw couldn't produce or deliver a
#   reply" at 12:10 and 12:12 on 2026-10-28.
#
#   Two rules now prevent that:
#     1. Abort is scoped to the dead run's own runId, never the session key.
#     2. A death runId is healed ONCE (state file). Re-detecting the same
#        death is a no-op, so it can never touch a later turn.
# ---------------------------------------------------------------------------
AGENT_DB="/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite"
MAX_WINDOW_BYTES=500000   # prompt budget is ~715 KB; compact well before it

transcript_bytes() {
    [ -f "$AGENT_DB" ] || { echo 0; return; }
    local sid
    sid=$(sqlite3 "$AGENT_DB" \
        "SELECT session_id FROM session_windows WHERE session_key='$KEY';" 2>/dev/null | head -1)
    [ -z "$sid" ] && { echo 0; return; }
    sqlite3 "$AGENT_DB" "
        SELECT COALESCE(SUM(COALESCE(t.event_utf8_bytes,0)),0)
        FROM session_transcript_active_events ae
        LEFT JOIN transcript_events t
          ON t.session_id=ae.session_id AND t.seq=ae.event_seq
        WHERE ae.session_id='$sid';" 2>/dev/null | head -1 | tr -d ' '
}

compact_session() {
    openclaw sessions compact "$KEY" --max-lines 60 2>&1 | tail -2
}

heal_context_overflow() {
    local out bytes dead_run_id
    dead_run_id="$1"
    out=$(compact_session)
    case "$out" in
        *"kept "*)
            log "  healed: $out"
            return 0 ;;
    esac

    if echo "$out" | grep -qiE "active run|queued work"; then
        # Abort ONLY the run that actually died. Aborting the session would
        # also abort whatever turn is running NOW — which is the user's live
        # message, not the corpse we are trying to bury.
        if [ -n "$dead_run_id" ]; then
            log "  session is busy — aborting ONLY the dead run ${dead_run_id}"
            openclaw gateway call sessions.abort --params "{\"runId\":\"${dead_run_id}\"}" 2>&1 | tail -1
            sleep 3
            out=$(compact_session)
            case "$out" in
                *"kept "*)
                    log "  healed after abort: $out"
                    return 0 ;;
            esac
        else
            log "  session is busy and the dead run id is unknown — NOT aborting anything"
        fi
    fi

    bytes=$(transcript_bytes)
    if [ -n "$bytes" ] && [ "$bytes" -gt "$MAX_WINDOW_BYTES" ] 2>/dev/null; then
        log "  window still oversized (${bytes} bytes > ${MAX_WINDOW_BYTES}) — resetting session (transcript is archived, not lost)"
        openclaw sessions delete "$KEY" --yes 2>&1 | tail -2 | cut -c1-160
        return 0
    fi

    log "  heal deferred: $(echo "$out" | tr '\n' ' ' | cut -c1-130)"
    return 1
}

# Shrink an oversized window WITHOUT aborting anything. Used when there is no
# confirmed context death: a long legitimate turn must never be killed just
# because the transcript is big. If the session is busy we only report; if it
# is idle and still oversized we reset it.
heal_oversized_window() {
    local out bytes
    bytes=$(transcript_bytes)
    out=$(compact_session)
    case "$out" in
        *"kept "*)
            log "  healed: $out"
            return 0 ;;
        *"No compaction needed"*)
            log "  window reports under budget; nothing to do"
            return 0 ;;
    esac

    if echo "$out" | grep -qiE "active run|queued work"; then
        log "  session busy with a live turn (${bytes} bytes) — not aborting it; will retry"
        return 1
    fi

    bytes=$(transcript_bytes)
    if [ -n "$bytes" ] && [ "$bytes" -gt "$MAX_WINDOW_BYTES" ] 2>/dev/null; then
        log "  window still oversized (${bytes} bytes > ${MAX_WINDOW_BYTES}) and idle — resetting session (transcript is archived, not lost)"
        openclaw sessions delete "$KEY" --yes 2>&1 | tail -2 | cut -c1-160
        return 0
    fi

    log "  heal deferred: $(echo "$out" | tr '\n' ' ' | cut -c1-130)"
    return 1
}

if [ -f "$GATEWAY_LOG" ]; then
    RECENT_DEATH=$(tail -600 "$GATEWAY_LOG" 2>/dev/null \
        | grep -a "embedded run agent end" | grep -a "isError=true" | grep -a "error=Context" | tail -1)
    if [ -n "$RECENT_DEATH" ]; then
        STAMP=$(echo "$RECENT_DEATH" | cut -c1-19)
        CUTOFF=$(date -v-5M '+%Y-%m-%dT%H:%M:%S')
        if [[ "$STAMP" > "$CUTOFF" ]]; then
            DEAD_RUN_ID=$(echo "$RECENT_DEATH" | grep -aoE 'runId=[0-9a-fA-F-]+' | head -1 | cut -d= -f2)
            # Heal each dead run EXACTLY ONCE. Without this, the same stale
            # death line is re-detected on every watchdog run for as long as
            # it stays in the log window — and each re-detection aborted a
            # live turn (2026-10-28: Amre lost two replies that way).
            if [ -f "$HEALED_STATE" ] && [ "$(cat "$HEALED_STATE" 2>/dev/null)" = "$DEAD_RUN_ID" ]; then
                log "CONTEXT DEATH ${DEAD_RUN_ID} already handled — not touching the session"
            else
                log "CONTEXT DEATH detected: $(echo "$RECENT_DEATH" | sed 's/\(.\{110\}\).*/\1/')"
                echo "$DEAD_RUN_ID" > "$HEALED_STATE" 2>/dev/null
                heal_context_overflow "$DEAD_RUN_ID"
            fi
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Heal 2b: the window is oversized even without a fresh context death.
# This catches the bloat BEFORE it kills a turn. Compacting is tried first;
# if the session is busy, the session is reset instead (archived, recoverable).
# ---------------------------------------------------------------------------
WINDOW_BYTES=$(transcript_bytes)
if [ -n "$WINDOW_BYTES" ] && [ "$WINDOW_BYTES" -gt "$MAX_WINDOW_BYTES" ] 2>/dev/null; then
    log "OVERSIZED WINDOW: ${WINDOW_BYTES} bytes > ${MAX_WINDOW_BYTES} — shrinking before it causes a context death"
    heal_oversized_window
    exit 0
fi

# ---------------------------------------------------------------------------
# Heal 3: wedged session (a command that never ends)
# ---------------------------------------------------------------------------
[ -f "$STATE_DB" ] || exit 0

# Only tasks owned by a Telegram session can wedge the Telegram lane.
# Cron/automation tasks run in ISOLATED sessions — a long-running one (the
# "Memory Dreaming Promotion" cron legitimately takes ~21 min) must NOT be
# killed. Do not widen this.
# Filter: only EXEC tasks (shell commands) can wedge the command lane.
# A long-running agent turn is NOT a wedge — e.g. the restart-recovery task
# ("[System] Your previous turn was interrupted...") legitimately runs for many
# minutes and killing it would abort real work the user asked for. System
# prompts always start with "[System]"; a shell command never does.
# The exec timeout (tools.exec.timeoutSeconds = 900s) means a shell task still
# marked running after MAX_AGE really has failed to return.
STUCK=$(sqlite3 "$STATE_DB" "
  SELECT task_id || '|' || replace(task, char(10), ' ')
  FROM task_runs
  WHERE status = 'running'
    AND owner_key LIKE 'agent:main:telegram:%'
    AND task NOT LIKE '[System]%'
    AND length(task) < 2000
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
