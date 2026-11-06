#!/bin/bash
# gateway-restart-guard.sh
#
# SHARED restart guard. Source this from ANY script that can stop, bootout or
# kickstart the OpenClaw gateway:
#
#     . /Users/amre/.openclaw/workspace/scripts/lib/gateway-restart-guard.sh
#     safe_restart_gateway "reason string"
#
# WHY THIS EXISTS
#   The gateway's shutdown drain is only 5 seconds:
#     "shutdown budget at shutdown: drain=5000ms shutdown=15000ms ..."
#   A Telegram turn takes minutes. So ANY restart that lands while a turn is
#   live kills that turn, and the user sees:
#     "⚠️ OpenClaw couldn't produce or deliver a reply"
#   That is not a hypothetical. On 2026-10-28 the gateway took 16 SIGTERMs,
#   and the 13:45:47 one landed mid-turn and killed messageId=2308:
#     "draining active work before stop with timeout 5000ms:
#      queueSize=2 pendingReplies=1 embeddedRuns=1"
#     -> "lane task error: ... error=\"agent run aborted for restart\""
#     -> "visible channel turn dispatched with no queued reply payloads"
#
# THE RULE
#   Before restarting, PROVE the Telegram session is idle.
#   If the state cannot be determined, treat it as LIVE and defer.
#   Deferring costs one cycle. Restarting blind costs the user her reply.
#
# THE ONE EXCEPTION
#   If the gateway is not answering /healthz at all, restart regardless. A
#   dead gateway has no live turn to protect, and "session status says
#   running" may just be a stale row from before the crash. Refusing to
#   restart a dead gateway would turn a blip into an outage.
#
# WHAT THIS DOES NOT COVER
#   A restart triggered from inside OpenClaw itself (not from a script) is not
#   observable here. Those are rare; the gateway's own maintenance path was
#   checked on 2026-10-28 and it only retries, it does not restart.

TELEGRAM_SESSION_KEY="agent:main:telegram:direct:8125193571"
GUARD_AGENT_DB="/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite"
GUARD_HEALTH_URL="http://127.0.0.1:18789/healthz"
GUARD_GATEWAY_LABEL="ai.openclaw.gateway"
GUARD_CLI_SESSION_TIMEOUT=12   # seconds; a watchdog that hangs is worse
GUARD_ACTIVITY_WINDOW=60       # seconds of transcript silence that means idle
GUARD_GRACE_SECONDS=25         # quiet period before the final restart check
GUARD_GATEWAY_LOG="$HOME/Library/Logs/openclaw/gateway.log"
GUARD_STALL_SECONDS=180        # a session stalled this long is a corpse
GUARD_STALL_FRESHNESS=90       # the stall report must be this recent to count

# --- Restart rate limiter ---------------------------------------------------
# On 2026-11-05 three separate watchdogs each decided "restart the gateway"
# and none of them knew about the other two. Result: 255 restarts in two
# days, roughly one every nine minutes, each one SIGTERM-ing the gateway and
# killing whatever Telegram turn was in flight. The liveness guard alone did
# not stop it, because each watchdog saw the gateway as "idle" on its own
# schedule and immediately after the previous restart.
#
# The rate limiter is shared (one state file, one clock) so the watchdogs
# can no longer storm the gateway between them. A restart that is genuinely
# needed still happens: the limiter only sets a MINIMUM GAP.
GUARD_RESTART_STATE="/Users/amre/.openclaw/workspace/scripts/.gateway-restart-state"
GUARD_MIN_RESTART_INTERVAL=300    # seconds between two normal restarts
GUARD_MIN_DEAD_RESTART_INTERVAL=45 # seconds between two restarts of a DEAD gateway
GUARD_MIN_FORCE_RESTART_INTERVAL=90 # seconds between two forced (wedged) restarts

# guard_stalled_session — 0 if the gateway itself reports the Telegram
# session as a stalled agent run.
#
# WHY THIS EXISTS
#   On 2026-11-03 at 18:02 the MiniMax API answered 429 and the agent
#   run never recovered. The gateway knew:
#
#     [diagnostic] stalled session: sessionKey=agent:main:telegram:direct:8125193571
#       state=processing age=704s queueDepth=0 reason=active_work_without_progress
#       classification=stalled_agent_run activeWorkKind=model_call
#       lastProgress=reply_operation:ended lastProgressAge=703s recovery=none
#
#   `classification=stalled_agent_run` with `recovery=none` is the gateway
#   saying the run is a corpse: it is holding the session in `processing`
#   forever, which blocks the compaction AND the restart that would fix
#   it. The Oct 28 rule protects a turn whose reply is seconds away; a
#   run the provider has abandoned is not that.
#
#   The report must also be CURRENT (within GUARD_STALL_FRESHNESS), so a
#   stall that resolved on its own stops counting, and the age must have
#   grown past GUARD_STALL_SECONDS, so a momentary hiccup never triggers
#   it.
guard_stalled_session() {
    local line ts age now_epoch ts_epoch
    [ -f "$GUARD_GATEWAY_LOG" ] || return 1
    line=$(grep -a "stalled session: .*sessionKey=$TELEGRAM_SESSION_KEY" \
           "$GUARD_GATEWAY_LOG" 2>/dev/null | tail -1)
    [ -n "$line" ] || return 1

    ts=$(printf '%s' "$line" | sed -n 's/^\([0-9][0-9-]*T[0-9:]*\).*/\1/p')
    [ -n "$ts" ] || return 1
    now_epoch=$(date -u +%s)
    ts_epoch=$(date -j -u -f "%Y-%m-%dT%H:%M:%S" "$ts" +%s 2>/dev/null) || return 1
    [ $(( now_epoch - ts_epoch )) -lt "$GUARD_STALL_FRESHNESS" ] || return 1

    age=$(printf '%s' "$line" | sed -n 's/.*[^a-zA-Z]age=\([0-9][0-9]*\)s.*/\1/p')
    [ -n "$age" ] || return 1
    [ "$age" -ge "$GUARD_STALL_SECONDS" ]
}

# guard_recent_activity — 0 if the Telegram session wrote a transcript event
# within the last GUARD_ACTIVITY_WINDOW seconds.
#
# WHY THIS EXISTS
#   On 2026-11-03 at 17:09:39 the guard read "idle" for the fourth
#   consecutive time and authorised a restart. At 17:09:46 the gateway
#   aborted a live turn and the user lost messageId 2547:
#
#     "visible channel turn dispatched with no queued reply payloads:
#      channel=telegram messageId=2547 cause=skipped:reply_operation_aborted"
#
#   The session status column was the only signal, and it LAGS: a turn that
#   starts writes its first transcript event before the status row catches
#   up. A transcript event is written within a second or two of a turn
#   starting, so "has the session written anything in the last N seconds"
#   is the far better liveness signal.
#
#   The session id is read from the same store, so this works even while
#   the CLI is slow.
guard_recent_activity() {
    local sid last now
    [ -f "$GUARD_AGENT_DB" ] || return 1
    sid=$(sqlite3 "$GUARD_AGENT_DB" "
        SELECT session_id FROM session_windows
        WHERE session_key='$TELEGRAM_SESSION_KEY'
        ORDER BY created_at DESC LIMIT 1;" 2>/dev/null | head -1 | tr -d ' ')
    [ -n "$sid" ] || return 1
    last=$(sqlite3 "$GUARD_AGENT_DB" "
        SELECT COALESCE(MAX(t.created_at), 0)
        FROM session_transcript_active_events ae
        LEFT JOIN transcript_events t
          ON t.session_id = ae.session_id AND t.seq = ae.event_seq
        WHERE ae.session_id = '$sid';" 2>/dev/null | head -1 | tr -d ' ')
    [ -n "$last" ] || return 1
    now=$(date +%s)
    # created_at is milliseconds.
    [ $(( (now - last / 1000) )) -lt "$GUARD_ACTIVITY_WINDOW" ]
}

# gateway_alive — 0 if the gateway answers /healthz
guard_gateway_alive() {
    local code
    code=$(curl -s -m 6 -o /dev/null -w '%{http_code}' "$GUARD_HEALTH_URL" 2>/dev/null)
    [ "$code" = "200" ]
}

# cli_session_status — the gateway's own view of the session, bounded.
# Prints the raw status, or nothing if it cannot be determined.
guard_cli_session_status() {
    local tmp pid i out
    tmp=$(mktemp 2>/dev/null) || return 1
    ( openclaw sessions list --json >"$tmp" 2>/dev/null ) &
    pid=$!
    for i in $(seq 1 "$GUARD_CLI_SESSION_TIMEOUT"); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
        wait "$pid" 2>/dev/null
        rm -f "$tmp"
        return 1
    fi
    wait "$pid" 2>/dev/null
    out=$(jq -r --arg k "$TELEGRAM_SESSION_KEY" '
        (.sessions // [])[]
        | select(.key == $k)
        | if .status == null then "idle" else .status end' "$tmp" 2>/dev/null | head -1 | tr -d ' \t')
    rm -f "$tmp"
    [ -n "$out" ] || return 1
    echo "$out"
}

# telegram_turn_state — prints exactly one of: live | idle | unknown
#
# Signal 1 (authoritative): the gateway's own session list.
# Signal 2 (fallback): session_windows.status in the agent DB.
# Neither readable -> "unknown" (treated as live by the caller).
telegram_turn_state() {
    local st=""

    st=$(guard_cli_session_status)

    if [ -z "$st" ] && [ -f "$GUARD_AGENT_DB" ]; then
        st=$(sqlite3 "$GUARD_AGENT_DB" "
            SELECT status FROM session_windows
            WHERE session_key='$TELEGRAM_SESSION_KEY'
            ORDER BY created_at DESC LIMIT 1;" 2>/dev/null | head -1 | tr -d ' ')
    fi

    # A run the gateway itself has classified as stalled is not a live
    # turn: it is holding the session in `processing` forever. It will
    # never deliver a reply, and it blocks the compaction and the restart
    # that would fix the session. Treat it as restartable.
    if guard_stalled_session; then
        echo "stalled"
        return
    fi

    # Recent transcript activity means a turn is live, whatever the status
    # column says. The status column LAGS a turn that has just started:
    # the turn writes its first event before the row catches up. This is
    # the signal that caught the messageId 2547 race.
    if guard_recent_activity; then
        echo "live"
        return
    fi

    case "$st" in
        running)                                  echo "live" ;;
        # A run that ended in "failed" is not a live run — the turn is over
        # and the next inbound starts a fresh one. Treating it as unknown
        # made the guard refuse to restart a session that was merely
        # sitting on a failed turn, which is the most common state right
        # after the watchdog resets an oversized window.
        done|killed|timeout|error|failed|idle)   echo "idle" ;;
        "")                                       echo "unknown" ;;
        *)                                        echo "unknown" ;;
    esac
}

# telegram_turn_live — 0 if a Telegram turn is live or its state is unknown
# (fail closed), 1 if it is provably idle.
#
# NOTE the polarity: exit 0 means "a turn IS live". Callers use it as
#     if telegram_turn_live; then ...defer...
telegram_turn_live() {
    local st
    st=$(telegram_turn_state)
    # Only a PROVABLY idle session counts as idle. "live" and "unknown"
    # both mean: do not touch it. "stalled" is the one exception: the
    # gateway has classified the run as a corpse, so it cannot deliver a
    # reply and it is blocking the very restart that would clear it.
    [ "$st" != "idle" ] && [ "$st" != "stalled" ]
}

# guard_restart_rate_ok — 0 if the shared rate limiter permits a restart
# right now, 1 if it must be deferred because one happened too recently.
#
# The limiter is a single state file shared by every script that can restart
# the gateway, so three watchdogs cannot each restart on their own schedule
# and collectively storm the gateway (255 restarts on 2026-11-03/05).
#
# The minimum gap is shorter when the gateway is actually dead, because
# there is nothing to protect and the bot is already down.
guard_restart_rate_ok() {
    local min_secs="${1:-300}"
    local last now
    [ -f "$GUARD_RESTART_STATE" ] || return 0
    last=$(head -1 "$GUARD_RESTART_STATE" 2>/dev/null | tr -d '[:space:]')
    case "$last" in ''|*[!0-9]*) return 0 ;; esac
    now=$(date +%s)
    local gap=$(( now - last ))
    if [ "$gap" -lt "$min_secs" ]; then
        echo "restart_allowed: DEFERRED — a gateway restart happened ${gap}s ago (min gap ${min_secs}s) (${2:-unspecified})" >&2
        return 1
    fi
    return 0
}

# guard_mark_restart — record that a restart just happened.
guard_mark_restart() {
    mkdir -p "$(dirname "$GUARD_RESTART_STATE")" 2>/dev/null
    date +%s > "$GUARD_RESTART_STATE" 2>/dev/null
}

# restart_allowed — 0 if it is safe to restart right now, 1 if it must be
# deferred. Logs the reason to stderr so the caller can surface it.
#
# This is a LIVENESS question only ("is a Telegram turn in flight?"). The
# RATE question ("has the gateway been restarted too recently?") lives in
# safe_restart_gateway / safe_force_restart_gateway, so that callers which
# merely need to know whether it is safe to STOP the gateway — such as
# agent-db-vacuum.sh, which waits for an idle lane before a VACUUM — are not
# penalised by a recent restart.
restart_allowed() {
    local reason="${1:-unspecified}"

    # Exception first: a dead gateway is already broken, restart it.
    if ! guard_gateway_alive; then
        echo "restart_allowed: gateway is NOT answering healthz — restarting regardless (${reason})" >&2
        return 0
    fi

    case "$(telegram_turn_state)" in
        idle)
            echo "restart_allowed: Telegram session is idle — restarting (${reason})" >&2
            return 0 ;;
        stalled)
            echo "restart_allowed: Telegram session is a STALLED run (the gateway classified it stalled_agent_run) — it cannot deliver a reply, so restarting (${reason})" >&2
            return 0 ;;
        live)
            echo "restart_allowed: DEFERRED — a Telegram turn is live; restarting would drop the reply (${reason})" >&2
            return 1 ;;
        *)
            echo "restart_allowed: DEFERRED — Telegram session state UNKNOWN; assuming a turn is live (${reason})" >&2
            return 1 ;;
    esac
}

# safe_restart_gateway <reason> — restart the gateway, but only when it is
# safe. Returns 0 if it restarted, 1 if it deferred.
#
# Uses `launchctl kickstart -k`, NOT `openclaw gateway install --force`
# (which overwrites the `caffeinate -dims` wrapper in the plist and drops the
# machine into sleep), and NOT `launchctl bootout` (which needs a bootstrap
# afterwards and historically failed with "5: Input/output error").
#
# THE GRACE PERIOD
#   A session that reads "idle" can still be about to adopt a queued
#   message. On 2026-11-03 the guard read idle at 17:09:39, the turn
#   wrote its first transcript event at 17:09:41, and the restart at
#   17:09:50 killed it — the user lost messageId 2547:
#
#     "visible channel turn dispatched with no queued reply payloads:
#      channel=telegram messageId=2547 cause=skipped:reply_operation_aborted"
#
#   A turn writes its first event within a second or two of starting, so
#   waiting GUARD_GRACE_SECONDS and re-checking afterwards catches the
#   turn before it is killed. The check is done twice: once after the
#   grace period, and once more immediately before the kickstart.
safe_restart_gateway() {
    local reason="${1:-unspecified}"

    # Shared rate limiter. Even a legitimately idle gateway may not be
    # restarted more often than the minimum gap, no matter which script is
    # asking. This is what ended the 255-restart storm of 2026-11-05, where
    # three independent watchdogs each restarted on their own schedule.
    local min_gap="$GUARD_MIN_RESTART_INTERVAL"
    if ! guard_gateway_alive; then
        min_gap="$GUARD_MIN_DEAD_RESTART_INTERVAL"
    fi
    if ! guard_restart_rate_ok "$min_gap" "$reason"; then
        return 1
    fi

    if [ "${GUARD_SKIP_GRACE:-0}" != "1" ]; then
        echo "restart_allowed: grace ${GUARD_GRACE_SECONDS}s — re-checking before the restart (${reason})" >&2
        sleep "$GUARD_GRACE_SECONDS"
    fi

    if ! restart_allowed "$reason"; then
        return 1
    fi

    launchctl kickstart -k "gui/501/${GUARD_GATEWAY_LABEL}" 2>&1 | tail -1
    guard_mark_restart
    return 0
}

# safe_force_restart_gateway <reason> — restart the gateway even though a
# turn may be live. ONLY for a session that is genuinely wedged (the command
# lane is blocked and no new message can ever become a turn).
#
# It still respects the shared rate limiter, so a wedged-session detector
# that fires repeatedly cannot restart the gateway in a loop. That was one
# of the three sources of the 2026-11-05 restart storm.
#
# It does NOT wait out the grace period: the whole point is that the turn is
# already lost.
safe_force_restart_gateway() {
    local reason="${1:-unspecified}"

    if ! guard_restart_rate_ok "$GUARD_MIN_FORCE_RESTART_INTERVAL" "$reason"; then
        return 1
    fi

    launchctl kickstart -k "gui/501/${GUARD_GATEWAY_LABEL}" 2>&1 | tail -1
    guard_mark_restart
    return 0
}
