#!/bin/bash
# Daily Workspace Git Backup
# Commits and pushes workspace to GitHub
#
# Fixed 2026-10-22: the script used to `exit 0` as soon as there was
# nothing new to stage — which meant a commit that was already made
# locally but not yet pushed was silently left behind on the remote.
# The push/rebase now ALWAYS runs, so the remote always ends up matching
# local main.

WORKSPACE="$HOME/.openclaw/workspace"
LOG_FILE="$WORKSPACE/scripts/backup.log"

cd "$WORKSPACE" || exit 1

# Add all changes
git add -A

# Commit if there is anything new to commit.
if git diff --cached --quiet 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | No new changes to commit" >> "$LOG_FILE"
else
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "Workspace backup: $TIMESTAMP" >> "$LOG_FILE" 2>&1
fi

# Pull (rebase) and push — ALWAYS, even when nothing was committed.
# Local main may hold commits that were never pushed.
git pull --rebase origin main >> "$LOG_FILE" 2>&1
if git push origin main >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ✅ SUCCESS | Pushed to GitHub" >> "$LOG_FILE"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ❌ FAILED | Push failed" >> "$LOG_FILE"
    exit 1
fi
