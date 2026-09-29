LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/community-pulse.log"
mkdir -p "$(dirname "$LOG")"
echo "=== Community Pulse — $(date) ===" >> "$LOG"
HN_RESP=$(curl -s "https://hn.algolia.com/api/v1/search?query=sol+ai+agent+sol-alias&tags=story" 2>/dev/null)
if echo "$HN_RESP" | grep -q "hits"; then
  COUNT=$(echo "$HN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('hits',[])))" 2>/dev/null || echo "0")
  echo "HN mentions: $COUNT" >> "$LOG"
  if [ "$COUNT" -gt 0 ]; then
    echo "$HN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(h['url'], '|', h.get('title','')[:60]) for h in d.get('hits',[])[:3]]" >> "$LOG" 2>/dev/null
  fi
else
  echo "HN API: no response" >> "$LOG"
fi
status=$(curl -s -o /dev/null -w "%{http_code}" -L "https://thesolai.github.io" --max-time 10 2>/dev/null)
echo "Sol website: $status" >> "$LOG"
echo "Done — $(date)" >> "$LOG"
