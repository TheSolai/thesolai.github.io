#!/bin/bash
# Site content cron watchdog
# Detects any ai.sol.* LaunchAgent that isn't loaded and reloads it
# Runs every 10 minutes via ai.sol.site-cron-watchdog LaunchAgent
#
# Why this exists: macOS launchd sometimes drops LaunchAgents on reboot,
# update, or after certain errors. Without this, the site content goes silent.

PLIST_DIR="$HOME/Library/LaunchAgents"
LOADED=$(launchctl list 2>&1 | grep -oE "ai\.sol\.[a-zA-Z0-9.-]+" | sort -u)

RELOADED=0
for plist in "$PLIST_DIR"/ai.sol.*.plist; do
    [ -f "$plist" ] || continue
    name=$(basename "$plist" .plist)
    if ! echo "$LOADED" | grep -q "^${name}$"; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] missing: $name — reloading"
        launchctl load "$plist" 2>&1 | head -1
        RELOADED=$((RELOADED + 1))
    fi
done

if [ "$RELOADED" -gt 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] watchdog: reloaded $RELOADED agent(s)"
else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] watchdog: all $LOADED_COUNT agents loaded"
fi