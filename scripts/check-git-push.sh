#!/bin/bash
# Dross monitors the daily content pipeline git push status
# If git push failed in the last run, surface the issue

LOG="$HOME/Projects/sol-skills-bundle/scripts/content-pipeline/logs/sol-content.log"

if [ ! -f "$LOG" ]; then
    echo "Log not found"
    exit 0
fi

# Check last 30 lines for git push failure
last_push=$(tail -30 "$LOG" | grep -A2 "git.*push" | tail -5)

if echo "$last_push" | grep -q "non-zero exit status 1\|failed\|error"; then
    echo "⚠️  Git push failed in last pipeline run:"
    echo "$last_push"
    exit 1
else
    echo "✅ Git push OK"
    exit 0
fi
