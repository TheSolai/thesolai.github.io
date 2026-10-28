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

    case "$st" in
        running)                                  echo "live" ;;
        done|killed|timeout|error|idle)           echo "idle" ;;
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
    # Only a PROVABLY idle session counts as idle. "live" and "unknown" both
    # mean: do not touch it.
    [ "$st" != "idle" ]
}

# restart_allowed — 0 if it is safe to restart right now, 1 if it must be
# deferred. Logs the reason to stderr so the caller can surface it.
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
safe_restart_gateway() {
    local reason="${1:-unspecified}"

    if ! restart_allowed "$reason"; then
        return 1
    fi

    launchctl kickstart -k "gui/501/${GUARD_GATEWAY_LABEL}" 2>&1 | tail -1
    return 0
}
