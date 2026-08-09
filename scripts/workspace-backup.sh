#!/bin/bash
# Daily Workspace Git Backup
# Commits and pushes workspace to GitHub

WORKSPACE="$HOME/.openclaw/workspace"
LOG_FILE="$WORKSPACE/scripts/backup.log"

cd "$WORKSPACE" || exit 1

# Add all changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | No changes to commit" >> "$LOG_FILE"
    exit 0
fi

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Workspace backup: $TIMESTAMP" >> "$LOG_FILE" 2>&1

# Pull and push to origin
git pull --rebase origin main >> "$LOG_FILE" 2>&1
if git push origin main >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ✅ SUCCESS | Pushed to GitHub" >> "$LOG_FILE"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ❌ FAILED | Push failed" >> "$LOG_FILE"
    exit 1
fi
