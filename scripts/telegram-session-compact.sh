#!/bin/bash
# telegram-session-compact.sh
#
# Keeps the Telegram direct session's transcript window bounded.
#
# Why this exists (2026-10-24):
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
#   hard-truncates the persisted window. Measured on this session:
#   200 events / 963 KB  ->  99 events / 564 KB (kept 100 lines).
#
#   It is a no-op when the window is under budget ("No compaction needed"),
#   so it is safe to call unconditionally whenever the session is idle.
#   It refuses while a run is active, hence the wait loop.
#
# Usage: telegram-session-compact.sh [max_lines] [wait_seconds]
#   max_lines    transcript lines to keep (default 100)
#   wait_seconds how long to wait for an in-flight run to end (default 900)

set -u

export PATH="/Users/amre/.openclaw/tools/current-bin:$PATH"

KEY="agent:main:telegram:direct:8125193571"
MAX_LINES="${1:-100}"
WAIT_SECONDS="${2:-900}"
LOG="/Users/amre/.openclaw/workspace/scripts/telegram-session-compact.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

DEADLINE=$(( $(date +%s) + WAIT_SECONDS ))
ATTEMPT=0
RESULT=""

while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    ATTEMPT=$((ATTEMPT + 1))
    OUT=$(openclaw sessions compact "$KEY" --max-lines "$MAX_LINES" 2>&1 | tail -2)
    if echo "$OUT" | grep -qi "active run"; then
        if [ $((ATTEMPT % 10)) -eq 0 ]; then
            log "run still active (attempt ${ATTEMPT}, $(date '+%H:%M:%S')) — waiting"
        fi
        sleep 20
        continue
    fi
    RESULT="$OUT"
    break
done

if [ -z "$RESULT" ]; then
    log "gave up after ${WAIT_SECONDS}s: session busy, no compaction performed"
    exit 1
fi

case "$RESULT" in
    *"No compaction needed"*) log "ok: window under budget, nothing to do" ;;
    *"kept "*)               log "compacted: $RESULT" ;;
    *)                       log "unexpected result: $RESULT" ;;
esac
exit 0
