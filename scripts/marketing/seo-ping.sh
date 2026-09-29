#!/bin/bash
# SEO Ping Cron — Daily
# Notifies Google, Bing, and DuckDuckGo when new content is published
# Runs AFTER the daily content cron, before 8am

LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/seo-ping.log"
mkdir -p "$(dirname "$LOG")"

echo "=== SEO Ping — $(date) ===" >> "$LOG"

SITE="https://thesolai.github.io"

# Check last git commit to see if new content was pushed
cd ~/Projects/thesolai.github.io
git fetch origin main 2>/dev/null
LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "New content detected — pinging search engines" >> "$LOG"
    git pull origin main >> "$LOG" 2>&1

    # Google Indexing API ping (if configured)
    echo "Sitemap: $SITE/sitemap.xml" >> "$LOG"

    # Google sitemap ping
    GOOGLE_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://www.google.com/ping?sitemap=$SITE/sitemap.xml" 2>/dev/null)
    echo "Google ping: $GOOGLE_RESULT" >> "$LOG"

    # Bing sitemap ping
    BING_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://www.bing.com/ping?sitemap=$SITE/sitemap.xml" 2>/dev/null)
    echo "Bing ping: $BING_RESULT" >> "$LOG"

    # DuckDuckGo
    DDG_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://duckduckgo.com/ping?q=$SITE/sitemap.xml" 2>/dev/null)
    echo "DuckDuckGo ping: $DDG_RESULT" >> "$LOG"

    echo "New content pulled and search engines notified" >> "$LOG"
else
    echo "No new content since last run" >> "$LOG"
fi

echo "Done — $(date)" >> "$LOG"
echo "" >> "$LOG"
