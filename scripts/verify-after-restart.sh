#!/bin/bash
# Wait for the gateway to restart (pid change), then verify the cache-TTL
# patch actually took effect: no NEW markers, the window shrinks, and the
# Telegram path works.
DIST_MARK="cache-ttl-no-minimax"
OLD_PID=$(launchctl list | awk '$3=="ai.openclaw.gateway"{print $1}')
echo "$(date '+%H:%M:%S') old gateway pid=$OLD_PID — waiting for a restart"

for i in $(seq 1 720); do
    NEW_PID=$(launchctl list | awk '$3=="ai.openclaw.gateway"{print $1}')
    if [ -n "$NEW_PID" ] && [ "$NEW_PID" != "$OLD_PID" ]; then
        echo "$(date '+%H:%M:%S') RESTARTED: pid $OLD_PID -> $NEW_PID"
        break
    fi
    [ $((i % 30)) -eq 1 ] && echo "$(date '+%H:%M:%S') still waiting (${i}0s)"
    sleep 10
done

NEW_PID=$(launchctl list | awk '$3=="ai.openclaw.gateway"{print $1}')
[ "$NEW_PID" = "$OLD_PID" ] && { echo "$(date '+%H:%M:%S') gave up waiting for a restart"; exit 1; }

echo "$(date '+%H:%M:%S') waiting 90s for the gateway to settle, then watching for new markers"
sleep 90
echo "--- healthz ---"
curl -s -m 8 -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:18789/healthz

echo "--- cache-TTL markers written since the restart ---"
/opt/homebrew/bin/python3 /Users/amre/.openclaw/workspace/scripts/health/cache-ttl-audit.py --minutes 3 --json 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin); s=d.get('sessions',[])
if not s: print('  NONE — the patch is live')
for x in s: print('  ',x['session_key'][:50],'markers=',x['markers'],'bytes=',x['marker_bytes'])
"
echo "--- telegram window size ---"
DB=/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite
sid=$(sqlite3 "$DB" "SELECT session_id FROM session_windows WHERE session_key='agent:main:telegram:direct:8125193571' ORDER BY created_at DESC LIMIT 1;")
sqlite3 "$DB" "SELECT '  '||COUNT(*)||' events, '||COALESCE(SUM(COALESCE(t.event_utf8_bytes,0)),0)||' bytes, last '||datetime(MAX(t.created_at)/1000,'unixepoch') FROM session_transcript_active_events ae LEFT JOIN transcript_events t ON t.session_id=ae.session_id AND t.seq=ae.event_seq WHERE ae.session_id='$sid';"
echo "--- done ---"
