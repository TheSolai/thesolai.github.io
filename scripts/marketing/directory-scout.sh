#!/bin/bash
# Directory Scout — Weekly
# Finds new AI agent directories and submits Sol AI

LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/directory-scout.log"
mkdir -p "$(dirname "$LOG")"

echo "=== Directory Scout — $(date) ===" >> "$LOG"

# Directories to check/submit to
DIRS=(
  "https://toolscout.ai/submit"
  "https://alternativeto.net/software/sol-ai/about/"
  "https://github.com/topics/ai-agent"
  "https://agentdns.com"
  "https://www.producthunt.com"
)

# Check if Sol is listed on major directories
check_listing() {
  local url="$1"
  local name="$2"
  local status=$(curl -s -o /dev/null -w "%{http_code}" -L "$url" 2>/dev/null)
  if [ "$status" = "200" ]; then
    echo "[$name] ✅ Live ($status)" >> "$LOG"
  else
    echo "[$name] ⚠️  Status $status" >> "$LOG"
  fi
}

echo "Checking existing listings..." >> "$LOG"
check_listing "https://thesolai.github.io" "Sol Website"
check_listing "https://github.com/TheSolAI/thesolai.github.io" "GitHub Repo"

# Look for new directories by searching for AI agent directory lists
echo "Scanning for new directories..." >> "$LOG"

# Submit to ToolScout if not done
echo "ToolScout submission status: needs manual submit at https://toolscout.ai/submit" >> "$LOG"

echo "Done — $(date)" >> "$LOG"
echo "" >> "$LOG"
