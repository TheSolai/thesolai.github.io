#!/bin/bash
# Daily compilation delivery for the zlib-kindle skill.
#
# Runs the cap-aware, resumable delivery script in ONE tracked foreground
# process. Never nohup, never backgrounded: the agent that runs this
# must be able to see the exit code and the final verdict line.
#
# Exit codes from deliver_compilations.py:
#   0  everything delivered
#   1  some titles failed
#   3  clean daily-cap stop, state intact
#
# This wrapper normalises case 3 into a plain message with exit 0, so a
# full day's budget is not reported as a job failure (which would trip
# the failure-alert path on a routine, expected stop).
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE/.." || exit 1

OUT=$(/opt/homebrew/bin/python3 scripts/deliver_compilations.py 2>&1)
CODE=$?

if [ "$CODE" -eq 3 ]; then
  echo "Daily send cap reached; stopped with state intact. Nothing was lost and no duplicate was sent."
  exit 0
fi

# A no-op day prints nothing, so the job stays silent on Telegram.
if echo "$OUT" | grep -q "=== delivered 0, failed 0"; then
  exit 0
fi

echo "$OUT"
exit "$CODE"
