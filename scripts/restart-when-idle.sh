#!/bin/bash
# Restart the gateway as soon as the Telegram session is idle.
# Used to load the cache-TTL worker patch. The shared guard decides when it is
# safe; this only supplies the patience.
. /Users/amre/.openclaw/workspace/scripts/lib/gateway-restart-guard.sh
for i in $(seq 1 240); do
    if ! telegram_turn_live; then
        echo "$(date '+%H:%M:%S') telegram idle — restarting to load the cache-TTL worker patch"
        safe_restart_gateway "load cache-TTL worker patch" && echo "$(date '+%H:%M:%S') restart issued"
        exit 0
    fi
    [ $((i % 10)) -eq 1 ] && echo "$(date '+%H:%M:%S') still waiting for an idle Telegram session (${i}0s)"
    sleep 10
done
echo "$(date '+%H:%M:%S') gave up waiting"
exit 1
