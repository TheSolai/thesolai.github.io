#!/bin/bash
# telegram-session-compact.sh
#
# Keeps the OpenClaw session transcript windows bounded.
#
# Why this exists (2026-10-24, refined 2026-10-28):
#   The OpenClaw context engine puts the ENTIRE session transcript into the
#   prompt and does not trim it to fit the context budget. The window is
#   measured in bytes, and ~900 KB of transcript is ~= the 184,800-token
#   budget of a 204,800-token context window. Once the window passes that,
#   EVERY turn trips `context-overflow-midturn-precheck`, pays ~45s of
#   LLM auto-compaction, and still lands over budget — because the LLM
#   summariser emits artifacts truncated at both ends
#   ("compaction-safeguard: ... loss=summary-tail,suffix-head") and never
#   persists a smaller window (session_transcript_archives stays 0).
#
#   `openclaw sessions compact --max-lines N` IS the reliable shrink: it
#   hard-truncates the persisted window. Measured on the Telegram session:
#   200 events / 963 KB  ->  99 events / 564 KB (kept 100 lines).
#
#   IMPORTANT: --max-lines counts EVENTS, not bytes. A single event can be a
#   30-60 KB thinking block, so "60 lines" still left the Telegram window at
#   216 KB and the cron window at 588 KB. 20 events keeps the starting window
#   near 60-70 KB, which is what actually gives a turn room to grow before it
#   hits the 184,800-token (715 KB) prompt budget.
#
#   It is a no-op when the window is under budget ("No compaction needed"),
#   so it is safe to call unconditionally whenever the session is idle.
#   It refuses while a run is active ("has an active run") or while work is
#   queued ("has queued work"), hence the wait loop.
#
#   The Telegram session also has a watchdog that escalates past this script
#   (abort the runaway turn -> compact -> reset the session). This script
#   must NOT abort anything: the other sessions below belong to long, healthy
#   runs such as the 21-minute "Memory Dreaming Promotion" cron.
#
# Usage: telegram-session-compact.sh [max_lines] [wait_seconds]
#   max_lines    transcript EVENTS to keep (default 20)
#   wait_seconds how long to wait for an in-flight run to end (default 900)

set -u

export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

# The sessions worth keeping bounded. The Telegram one is the one that
# actually goes silent; the main and cron sessions overflow the same way but
# more quietly, so they are included.
KEYS=(
  "agent:main:telegram:direct:8125193571"
  "agent:main:main"
  "agent:main:cron:debe0687-a581-4c01-9194-8c049cf8b5e0"
)
MAX_LINES="${1:-20}"
WAIT_SECONDS="${2:-900}"
LOG="/Users/amre/.openclaw/workspace/scripts/telegram-session-compact.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

compact_one() {
    local key="$1"
    local deadline attempt out result
    deadline=$(( $(date +%s) + WAIT_SECONDS ))
    attempt=0
    result=""

    while [ "$(date +%s)" -lt "$deadline" ]; do
        attempt=$(( attempt + 1 ))
        out=$(openclaw sessions compact "$key" --max-lines "$MAX_LINES" 2>&1 | tail -2)
        if echo "$out" | grep -qi "active run\|queued work"; then
            if [ $(( attempt % 10 )) -eq 0 ]; then
                log "  [$key] still busy (attempt ${attempt}, $(date '+%H:%M:%S')) — waiting"
            fi
            sleep 20
            continue
        fi
        result="$out"
        break
    done

    if [ -z "$result" ]; then
        log "  [$key] gave up after ${WAIT_SECONDS}s: session busy, no compaction performed"
        return 1
    fi

    case "$result" in
        *"No compaction needed"*) log "  [$key] ok: window under budget, nothing to do" ;;
        *"kept "*)               log "  [$key] compacted: $result" ;;
        *"not reachable"*|*"ECONNREFUSED"*) log "  [$key] warn: gateway unreachable — skipping this tick" ;;
        *)                       log "  [$key] unexpected result: $(echo "$result" | tr '\n' ' ' | cut -c1-160)" ;;
    esac
    return 0
}

for key in "${KEYS[@]}"; do
    compact_one "$key"
done
exit 0
