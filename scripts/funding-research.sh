#!/bin/bash
# Funding research heartbeat — pings Dross every 10 minutes to keep working
# Run as: nohup ./funding-research.sh &

INTERVAL=600  # 10 minutes
END_TIME=$((SECONDS + 3600))  # 1 hour from now

echo "[FUNDING RESEARCH] Starting at $(date). Working for 1 hour."

while [ $SECONDS -lt $END_TIME ]; do
    ELAPSED=$((SECONDS))
    REMAINING=$((END_TIME - SECONDS))
    echo "[FUNDING RESEARCH] Heartbeat at +${ELAPSED}s. ${REMAINING}s remaining."
    
    # Check if there's work to do
    if [ -f "/tmp/dross-funding-next-task.txt" ]; then
        TASK=$(cat /tmp/dross-funding-next-task.txt)
        echo "[FUNDING RESEARCH] Next task: $TASK"
    else
        echo "[FUNDING RESEARCH] No pending tasks."
    fi
    
    sleep $INTERVAL
done

echo "[FUNDING RESEARCH] Hour complete at $(date)."
