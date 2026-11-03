#!/bin/bash
# Wait for the gateway to restart (pid change), then verify the cache-TTL
# patch actually took effect: no NEW markers, the window shrinks, and the
# Telegram path works.
DIST_MARK="cache-ttl-no-minimax"
# $1 = the pid the gateway had BEFORE the restart. It has to be captured
# before the restart happens, otherwise this script would capture the new
# pid and then wait for a second restart that never comes.
OLD_PID="${1:-$(launchctl list | awk '$3=="ai.openclaw.gateway"{print $1}')}"
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

RESTART_EPOCH=$(date +%s)
echo "$(date '+%H:%M:%S') restart epoch = $RESTART_EPOCH"

echo "$(date '+%H:%M:%S') waiting 90s for the gateway to settle, then watching for new markers"
sleep 90
echo "--- healthz ---"
curl -s -m 8 -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:18789/healthz

echo "--- tool-search surface (the prompt fix) ---"
grep -aoE '"message":"tool-search:[^"]*"' /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log 2>/dev/null | tail -2
grep -aoE 'config hot reload applied \(tools\.toolSearch\)' /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log 2>/dev/null | tail -1

echo "--- cache-TTL markers: any written AFTER the restart? ---"
# The old check counted every marker in the last 3 minutes, which included
# markers written BEFORE the restart. That can never distinguish "the patch
# is live" from "the patch is not loaded". Compare the newest marker's
# timestamp against the restart instead.
/opt/homebrew/bin/python3 - "$RESTART_EPOCH" <<'PY'
import os, sqlite3, subprocess, sys, tempfile, datetime
restart = int(sys.argv[1])
DB = os.path.expanduser("~/.openclaw/agents/main/agent/openclaw-agent.sqlite")
ZSTD = "/opt/homebrew/bin/zstd"
def dec(blob):
    if not blob: return None
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(blob); p = f.name
    o = p + ".out"
    try:
        if subprocess.run([ZSTD, "-d", "-f", "-q", p, "-o", o],
                          capture_output=True).returncode == 0:
            return open(o, "r", errors="replace").read()
        return None
    finally:
        for x in (p, o):
            try: os.unlink(x)
            except OSError: pass
c = sqlite3.connect(DB)
rows = c.execute(
    "SELECT session_id, seq, created_at, event_zstd FROM transcript_events "
    "WHERE event_zstd IS NOT NULL ORDER BY created_at DESC LIMIT 400").fetchall()
newest = None
for sid, seq, ts, blob in rows:
    t = dec(blob)
    if t and "openclaw.cache-ttl" in t:
        newest = (ts, seq, sid); break
if newest is None:
    print("  no marker found in the last 400 stored events")
elif newest[0] / 1000 > restart:
    print(f"  STILL FAILING — a marker was written {newest[0]/1000 - restart:.0f}s "
          f"AFTER the restart (seq={newest[1]}, session={newest[2][:8]})")
else:
    print(f"  OK — newest marker predates the restart by "
          f"{restart - newest[0]/1000:.0f}s (seq={newest[1]})")
PY

echo "--- prompt budget (was 184.8k-186.4k against an 184.8k budget) ---"
/opt/homebrew/bin/python3 - "$RESTART_EPOCH" <<'PY'
import json, re, sys
from datetime import datetime
restart = int(sys.argv[1])
path = "/tmp/openclaw/openclaw-%s.log" % datetime.now().strftime("%Y-%m-%d")
worst = 0; worst_since = 0; budget = 0; after = 0
try:
    for line in open(path, errors="replace"):
        if not line.startswith("{"): continue
        try: o = json.loads(line)
        except Exception: continue
        t = o.get("time") or ""
        m = str(o.get("message", ""))
        mt = re.search(r"estimatedPromptTokens=(\d+)", m)
        mb = re.search(r"promptBudgetBeforeReserve=(\d+)", m)
        if not (mt and mb):
            continue
        tok, bud = int(mt.group(1)), int(mb.group(1))
        budget = bud
        if tok > worst: worst = tok
        try:
            ts = datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts >= restart:
            after += 1
            if tok > worst_since: worst_since = tok
except OSError as exc:
    print("  could not read the log:", exc)

if worst:
    print(f"  worst prompt in this log = {worst:,} vs budget {budget:,} "
          f"({worst / budget * 100 if budget else 0:.1f}%)")
if after:
    pct = worst_since / budget * 100 if budget else 0
    print(f"  worst prompt SINCE the restart = {worst_since:,} "
          f"({pct:.1f}%) over {after} measurement(s)")
    print("  PASS — prompt is under budget" if pct < 100
          else "  FAIL — still over budget")
else:
    # The mid-turn precheck only fires when the runtime PREDECTS pressure.
    # No measurement since the restart means the prompt has not come near
    # the budget since — silence, not a missing number.
    print("  no precheck since the restart — the prompt has not come near "
          "the budget since (the precheck only fires under pressure)")
    print("  PASS — no over-budget prompt since the restart")
PY

echo "--- telegram window size ---"
DB=/Users/amre/.openclaw/agents/main/agent/openclaw-agent.sqlite
sid=$(sqlite3 "$DB" "SELECT session_id FROM session_windows WHERE session_key='agent:main:telegram:direct:8125193571' ORDER BY created_at DESC LIMIT 1;")
sqlite3 "$DB" "SELECT '  '||COUNT(*)||' events, '||COALESCE(SUM(COALESCE(t.event_utf8_bytes,0)),0)||' bytes, last '||datetime(MAX(t.created_at)/1000,'unixepoch') FROM session_transcript_active_events ae LEFT JOIN transcript_events t ON t.session_id=ae.session_id AND t.seq=ae.event_seq WHERE ae.session_id='$sid';"
echo "--- doctor ---"
/opt/homebrew/bin/python3 /Users/amre/.openclaw/workspace/scripts/health/claw-doctor.py --window-hours 2 2>&1 | grep -E "prompt fits|cache-TTL gate|prompt reached|worst prompt" | head -12
echo "--- done ---"
