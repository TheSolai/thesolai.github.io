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
#      FIX: compact the transcript so the next turn starts small — but only
#      when the session is IDLE. A busy session means the gateway's own
#      auto-compaction is recovering the turn in place; that recovery
#      delivers the reply, so it must never be interrupted.
#
# NEVER, under any circumstance:
#   * restart because Telegram reports pending updates (that is the bug that
#     caused the 2026-10-26 outage)
#   * restart because DNS is down (a restart cannot fix a resolver)
#   * kill a task that is not owned by a Telegram session (the 21-minute
#     "Memory Dreaming Promotion" cron is legitimate and must never be killed)
#   * ABORT a run to "help" a context-overflow recovery. The gateway recovers
#     the turn itself and delivers the reply ~50s later. Aborting is what
#     produced the "couldn't produce or deliver a reply" errors on
#     2026-10-28 (12:10, 12:12, 13:22).
#
# Usage: telegram-session-watchdog.sh [stuck_task_max_age_seconds]
#   default 1200 (20 min, safely past the 15 min exec timeout cap)

set -u
export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

# Shared restart guard — one source of truth for "is a Telegram turn live?".
# Sourced, not copied: exec-approvals-watchdog.sh and agent-db-vacuum.sh use
# the same rules, and they are all capable of killing a live reply.
GUARD_LIB="/Users/amre/.openclaw/workspace/scripts/lib/gateway-restart-guard.sh"
# shellcheck source=/dev/null
[ -f "$GUARD_LIB" ] && . "$GUARD_LIB"

STATE_DB="/Users/amre/.openclaw/state/openclaw.sqlite"
AGENT_DB="/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite"
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
    local pid mode="${1:-guarded}"
    pid=$(gateway_pid)
    if [ -z "$pid" ] || [ "$pid" = "-" ]; then
        log "  gateway not running — calling the service-recovery path instead"
        ensure_service_available
        return 0
    fi

    if [ "$mode" = "force" ]; then
        # FORCED restart. Only used for a WEDGED session, where the command
        # lane is permanently blocked and no new Telegram message can ever
        # become a turn. There the choice is "drop the stuck turn" or "the
        # bot is dead forever", and dropping it is obviously right.
        log "GATEWAY-RESTART pid=$pid reason=watchdog mode=force (wedged session — the stuck turn is lost, the lane is not)"
        launchctl kickstart -k "gui/501/${GATEWAY_LABEL}" 2>&1 | tail -1
        return 0
    fi

    # GUARDED restart: refuse to bounce the gateway while a Telegram turn is
    # live. The gateway's shutdown drain is 5s and a turn takes minutes, so
    # a restart here kills the reply the user is waiting for.
    if ! restart_allowed "watchdog"; then
        log "GATEWAY-RESTART DEFERRED — a Telegram turn is live (reason=watchdog)"
        return 1
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
#
# THE RULE: this function FAILS CLOSED. It returns 0 ("a turn is live") when
# it cannot prove the session is idle. The old implementation returned 1
# ("idle") on any error — including a failed database read — so a broken read
# silently handed the watchdog permission to reset a session that was
# mid-reply. Fail-open is how "couldn't produce or deliver a reply" happens.
#
# Signal 1 (authoritative): the gateway's own view.
#   `openclaw sessions list --json` reports status per session:
#     "running"  -> a turn is live
#     "done"/"killed"/"timeout"/null -> no active run (null = not tracked)
#   This is the same signal `openclaw doctor` reads.
#
# Signal 2 (fallback): session_windows.status in the agent DB, which backs
# the CLI value.
#
# The OLD implementation queried `task_runs` for a running row owned by the
# Telegram session — but task_runs only records EXEC tasks, never the agent
# turn itself. So it reported "idle" while a Telegram turn was mid-flight.
# That is how the watchdog reset a live session and dropped a reply.
#
# The implementation now lives in scripts/lib/gateway-restart-guard.sh so
# that every script capable of restarting the gateway asks the SAME question
# the same way. It fails closed: an unknown state counts as live.
cli_session_status() {
    [ -n "${GUARD_LIB:-}" ] || return 1
    guard_cli_session_status
}

telegram_turn_active() {
    if [ -n "${GUARD_LIB:-}" ] && [ -f "$GUARD_LIB" ]; then
        telegram_turn_live
        return $?
    fi
    # Guard library missing: fail closed, never assume idle.
    log "  restart-guard library missing — assuming a turn is LIVE and deferring"
    return 0
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
#   tier 2  the session is BUSY -> defer, never abort
#   tier 3  the window is still oversized AND the session is idle -> reset
#           the session (`sessions delete` archives the transcript to a
#           recoverable .zst and clears the window; the next message starts
#           fresh)
#
# WHY NOTHING HERE EVER ABORTS A RUN (learned 2026-10-28, the hard way):
#   A context-overflow death line and a live run are usually the SAME event:
#   the gateway's own auto-compaction recovers an overflowed turn IN PLACE by
#   replacing the prompt with a summary and letting the turn continue.
#   Proven: 13:21:54 "auto-compaction succeeded" -> 13:22:22 the reply went
#   out. Aborting that run destroyed the recovery and produced the exact
#   error this watchdog exists to prevent ("OpenClaw couldn't produce or
#   deliver a reply", run e66ea972, killed 13:22:19).
#
#   So the rules are:
#     1. NEVER abort a run in this heal — not by session key, not by runId.
#     2. A busy session means the gateway is recovering a turn. LEAVE IT.
#     3. A death runId is healed ONCE (state file), so a stale log line is
#        never re-detected against a later turn.
#     4. Only touch the Telegram session when the death is ATTRIBUTED to it.
#        Foreign and unattributed deaths are reported and ignored.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Attribution: WHICH session did a dead run belong to?
#
# The gateway log line "embedded run agent end: ... error=Context overflow"
# carries NO session key. The watchdog therefore treated a context death in
# ANY session (a cron, a skill-workshop review, an isolated evaluation) as a
# death in the Telegram session — and then compacted, or RESET, the user's
# live Telegram session. On 2026-10-28 12:52 that reset killed the turn that
# was answering her 12:46 message; the gateway then logged
#   "visible channel turn dispatched with no queued reply payloads:
#    messageId=2303 ... cause=skipped:reply_operation_aborted"
# which is exactly the "OpenClaw couldn't produce or deliver a reply"
# symptom she reported.
#
# The transcript in the agent DB carries the runId, so the owning session can
# be looked up directly. A death that belongs to another session is REPORTED
# and IGNORED — it must never touch the Telegram session.
# ---------------------------------------------------------------------------
telegram_session_id() {
    [ -f "$AGENT_DB" ] || return 1
    sqlite3 "$AGENT_DB" \
        "SELECT session_id FROM session_windows WHERE session_key='$KEY' ORDER BY created_at DESC LIMIT 1;" \
        2>/dev/null | head -1 | tr -d ' '
}

# Which session did a dead run belong to?
#
# Signal 1 (best): the gateway log. A context-overflow death emits two
# adjacent lines — "embedded run agent end ... error=Context overflow"
# (carries the runId) and, ~10ms later, "[context-overflow-diag]"
# (carries sessionKey=). Pairing them attributes the death with no database
# read at all.
#
# Signal 2 (fallback): the runId inside the transcript events in the agent DB.
#
# Either way, the answer is "unknown" when it cannot be determined — and
# "unknown" means DO NOT TOUCH THE TELEGRAM SESSION. An unattributed death is
# far more likely to belong to some cron or workshop review than to Amre's
# live chat, and treating it as hers is what reset her session on 2026-10-28.
death_owner_from_log() {
    local death_line="$1" diag_line e1 e2 delta
    diag_line=$(tail -600 "$GATEWAY_LOG" 2>/dev/null \
        | grep -a "context-overflow-diag" | tail -1)
    [ -n "$diag_line" ] || { echo "unknown"; return; }

    e1=$(date -j -u -f '%Y-%m-%dT%H:%M:%S' "$(echo "$death_line" | cut -c1-19)" '+%s' 2>/dev/null)
    e2=$(date -j -u -f '%Y-%m-%dT%H:%M:%S' "$(echo "$diag_line" | cut -c1-19)" '+%s' 2>/dev/null)
    if [ -z "$e1" ] || [ -z "$e2" ]; then echo "unknown"; return; fi
    delta=$((e1 - e2))

    # The two lines are written milliseconds apart. Anything further apart is
    # a different death and must not be paired.
    if [ "$delta" -gt 5 ] || [ "$delta" -lt -5 ]; then echo "unknown"; return; fi

    echo "$diag_line" | grep -aoE 'sessionKey=[^ ]+' | head -1 | cut -d= -f2
}

death_session_key() {
    local run_id="$1" owner death_line="${2:-}"
    [ -n "$run_id" ] || { echo "unknown"; return; }

    if [ -n "$death_line" ]; then
        owner=$(death_owner_from_log "$death_line")
        if [ -n "$owner" ] && [ "$owner" != "unknown" ]; then
            echo "$owner"
            return
        fi
    fi

    [ -f "$AGENT_DB" ] || { echo "unknown"; return; }
    owner=$(sqlite3 "$AGENT_DB" "
        SELECT DISTINCT w.session_key
        FROM transcript_events t
        JOIN session_windows w ON w.session_id = t.session_id
        WHERE t.event_json LIKE '%$run_id%'
        LIMIT 1;" 2>/dev/null | head -1 | tr -d ' ')
    [ -n "$owner" ] || { echo "unknown"; return; }
    echo "$owner"
}

compact_session() {
    openclaw sessions compact "$KEY" --max-lines 20 2>&1 | tail -2
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
        # THE SESSION IS BUSY — AND THAT IS GOOD NEWS, NOT BAD NEWS.
        #
        # A context-overflow death line and a live run are the SAME event most
        # of the time: the gateway's own auto-compaction recovers an
        # overflowed turn IN PLACE (it replaces the prompt with a summary and
        # lets the turn continue). Proven on 2026-10-28: 13:21:54
        # "auto-compaction succeeded" -> 13:22:22 the reply was delivered.
        #
        # The watchdog used to "help" by aborting the dead run and compacting
        # again. That destroyed the recovery: the run carrying the user's
        # message was killed a few seconds before it would have replied, and
        # she saw exactly the error this watchdog was meant to prevent:
        #   "OpenClaw couldn't produce or deliver a reply"
        # That happened to run e66ea972 on 2026-10-28 (killed 13:22:19).
        #
        # RULE: NEVER ABORT A RUN IN THIS HEAL. Not by session key, not by
        # runId, not ever. If the session is busy, the right move is to leave
        # it alone and let the gateway finish its recovery. Deferring costs
        # one watchdog cycle; aborting costs the user her reply.
        log "  session is busy (run ${dead_run_id}) — NOT aborting; the gateway's auto-compaction is recovering the turn in place. Deferring."
        return 1
    fi

    bytes=$(transcript_bytes)
    if [ -n "$bytes" ] && [ "$bytes" -gt "$MAX_WINDOW_BYTES" ] 2>/dev/null; then
        if telegram_turn_active; then
            # NEVER reset while a turn is live. `sessions delete` kills the run
            # that is about to deliver the reply, and the user sees
            # "couldn't produce or deliver a reply". Defer instead: the
            # OVERSIZED WINDOW pass below shrinks the window once the turn ends.
            log "  window still oversized (${bytes} bytes > ${MAX_WINDOW_BYTES}) but a Telegram turn is LIVE — deferring the reset (resetting now would drop the reply)"
            return 1
        fi
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
    if telegram_turn_active; then
        log "  session busy with a live turn (${bytes} bytes) — not touching it; will retry"
        return 1
    fi
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
        # The gateway log stamps events in UTC; compare in UTC too, otherwise
        # the 5-minute window silently breaks the moment the machine's
        # timezone stops being GMT.
        CUTOFF=$(date -u -v-5M '+%Y-%m-%dT%H:%M:%S')
        if [[ "$STAMP" > "$CUTOFF" ]]; then
            # Run ids can be compound ("skill-workshop-review:<uuid>"), so pull
            # the UUID out rather than the whole runId token.
            DEAD_RUN_ID=$(echo "$RECENT_DEATH" \
                | grep -aoE '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}' \
                | head -1)
            OWNER=$(death_session_key "$DEAD_RUN_ID" "$RECENT_DEATH")
            if [ -n "$OWNER" ] && [ "$OWNER" != "$KEY" ] && [ "$OWNER" != "unknown" ]; then
                # A context death in somebody else's session (a cron, a
                # skill-workshop review, an isolated evaluation) is NOT the
                # Telegram session's problem. Healing the Telegram session for
                # it reset the user's live turn and dropped her reply.
                log "FOREIGN CONTEXT DEATH in '${OWNER}' (run ${DEAD_RUN_ID}) — Telegram session NOT touched"
            elif [ "$OWNER" = "unknown" ]; then
                # UNATTRIBUTED. We could not prove whose session died, so we
                # do not act on the Telegram session at all. The oversized
                # window is still caught by the independent size check below
                # (Heal 2b), which also refuses to touch a live turn — so
                # nothing is lost by refusing here.
                log "CONTEXT DEATH ${DEAD_RUN_ID} UNATTRIBUTED — Telegram session NOT touched"
            elif [ -f "$HEALED_STATE" ] && [ "$(cat "$HEALED_STATE" 2>/dev/null)" = "$DEAD_RUN_ID" ]; then
                # Heal each dead run EXACTLY ONCE. Without this, the same stale
                # death line is re-detected on every watchdog run for as long as
                # it stays in the log window — and each re-detection aborted a
                # live turn (2026-10-28: Amre lost two replies that way).
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
# FORCED: the lane is already wedged, so the guarded path would refuse to
# restart (a turn is live — the stuck one) and the bot would stay dead.
# The stuck turn is lost; the lane comes back.
restart_gateway force
log "watchdog action complete"
exit 0
