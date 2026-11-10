#!/bin/zsh
# MoEShift server launcher (supervised by launchd).
# Waits for prepared experts, then runs the MoEShift OpenAI-compatible server on 8081.

set -u
LOG=/tmp/moeshift-server.log
exec >>"$LOG" 2>&1

MANIFEST=/Users/amre/.moeshift/models/qwen-3.6-35b-a3b-wolf/experts/manifest.json
CONFIG=/Users/amre/.config/moeshift/config.json

echo "[$(date -u +%T)] server launcher up, waiting for experts + config..."
WAITED=0
while [ ! -f "$MANIFEST" ] || [ ! -f "$CONFIG" ]; do
  sleep 20
  WAITED=$((WAITED + 20))
  if [ $WAITED -gt 21600 ]; then
    echo "[$(date -u +%T)] timed out waiting for experts/config"
    exit 1
  fi
done
echo "[$(date -u +%T)] experts + config present, starting moeshift on 127.0.0.1:8081"
exec /opt/homebrew/bin/moeshift --config /Users/amre/.config/moeshift/config.json
