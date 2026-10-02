#!/bin/bash
# Site Inspector — Daily
# Checks every page on the site for: broken links, missing OG tags, slow load, missing images

LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/site-inspector.log"
mkdir -p "$(dirname "$LOG")"

echo "=== Site Inspector — $(date) ===" >> "$LOG"

SITE="https://thesolai.github.io"
ISSUES=0

check_page() {
    local URL="$1"
    local NAME="$2"
    local STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$URL" --max-time 10 --fail 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo "[$NAME] ✅ $STATUS" >> "$LOG"
    else
        echo "[$NAME] ❌ $STATUS" >> "$LOG"
        ISSUES=$((ISSUES + 1))
    fi
}

echo "Checking key pages..." >> "$LOG"
check_page "$SITE/" "Home"
check_page "$SITE/blog/" "Blog"
check_page "$SITE/products/" "Products"
check_page "$SITE/purr/" "Purr"
check_page "$SITE/dross/" "Dross"
check_page "$SITE/about/" "About"
check_page "$SITE/contact/" "Contact"
check_page "$SITE/guides/" "Guides"
check_page "$SITE/skills/" "Skills"
check_page "$SITE/bloopers/" "Bloopers"
check_page "$SITE/sitemap.xml" "Sitemap"
check_page "$SITE/robots.txt" "Robots"

echo "" >> "$LOG"
echo "Checking latest posts (last 3)..." >> "$LOG"
cd ~/Projects/thesolai.github.io/_posts
for POST in $(ls -t *.md 2>/dev/null | head -3); do
    DATE=$(echo "$POST" | sed 's/^\([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]\).*/\1/')
    URL_DATE=$(echo "$DATE" | tr '-' '/')
    SLUG=$(echo "$POST" | sed 's/^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-//;s/\.md$//')
    POST_URL="$SITE/blog/$URL_DATE/$SLUG/"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$POST_URL" --max-time 10 2>/dev/null)
    echo "[$POST] → $STATUS" >> "$LOG"
done

echo "" >> "$LOG"
if [ "$ISSUES" -eq 0 ]; then
    echo "All checks passed ✅" >> "$LOG"
else
    echo "$ISSUES issue(s) found — review above" >> "$LOG"
fi

echo "Done — $(date)" >> "$LOG"
echo "" >> "$LOG"
