#!/bin/bash
# Directory Health Check — Weekly
# Verifies Sol is listed correctly on all known directories

LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/directory-health.log"
mkdir -p "$(dirname "$LOG")"

echo "=== Directory Health — $(date) ===" >> "$LOG"

declare -a DIRS=(
  "https://toolscout.ai/submit|ToolScout|Needs manual submission"
  "https://github.com/TheSolAI/thesolai.github.io|GitHub|Should be listed"
  "https://alternativeto.net/software/sol-ai/about/|AlternativeTo|Check listing"
  "https://agentdns.com|AgentDNS|Check if listed"
  "https://www.producthunt.com/posts/sol-ai|Product Hunt|Check if listed"
)

ALL_OK=true
for entry in "${DIRS[@]}"; do
  IFS='|' read -r URL NAME STATUS <<< "$entry"
  echo -n "[$NAME] " >> "$LOG"
  status_code=$(curl -s -o /dev/null -w "%{http_code}" -L "$URL" --max-time 10 2>/dev/null)
  if [ "$status_code" = "200" ]; then
    echo "✅ Live ($status_code) — $STATUS" >> "$LOG"
  else
    echo "❌ Issue ($status_code) — $STATUS" >> "$LOG"
    ALL_OK=false
  fi
done

echo "" >> "$LOG"
if [ "$ALL_OK" = true ]; then
  echo "All directories healthy" >> "$LOG"
else
  echo "Some directories need attention" >> "$LOG"
fi

echo "Done — $(date)" >> "$LOG"
echo "" >> "$LOG"
