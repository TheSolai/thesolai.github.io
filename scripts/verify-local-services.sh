#!/bin/bash
# verify-local-services.sh — the ground truth for local service + model state.
#
# Never assert model/port/service state from memory. Run this.
#
# Usage: bash scripts/verify-local-services.sh
# Output: one line per service with HTTP status, plus the Ollama model list.

set -uo pipefail

check_http() {
  local name="$1" url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
  printf "%-22s %-32s HTTP %s\n" "$name" "$url" "${code:-000}"
}

echo "=== launchd services ==="
launchctl list 2>/dev/null | grep -E "ai\.sol\.(while-i-was-away|sloth-inbox|fridge-list)" || echo "(none registered)"

echo
echo "=== live HTTP ==="
check_http "while-i-was-away" "http://127.0.0.1:8876/"
check_http "sloth-inbox"      "http://127.0.0.1:8501/"
check_http "fridge-list"      "http://127.0.0.1:7860/"

echo
echo "=== ollama models (installed only) ==="
if curl -s --max-time 5 http://localhost:11434/api/tags 2>/dev/null | \
   grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | sort; then
  :
else
  echo "(ollama not reachable)"
fi
