#!/bin/zsh
# MoEShift preparation pipeline.
# Waits for the WOLF GGUF pull to land in Ollama's blob store, hardlinks it into
# MoEShift's model dir, extracts + verifies the routed experts, and writes the
# MoEShift server config on port 8081 (8080 is taken by OpenClaw's llama-cpp).

set -u

LOG=/tmp/moeshift-prepare.log
exec >>"$LOG" 2>&1

MODEL_ID=qwen-3.6-35b-a3b-wolf
BLOB_ID=d24d876be8541f234f4d11f18779c932c803f01c2ba7aa3988a6f20eaefdae7e
BLOBS=/Users/amre/.ollama/models/blobs
FINAL="$BLOBS/sha256-$BLOB_ID"
PARTIAL="$FINAL-partial"

BASE=/Users/amre/.moeshift/models/$MODEL_ID
GGUF="$BASE/model.gguf"
EXPERTS="$BASE/experts"
PREFIX=/opt/homebrew/opt/moeshift
TOOL="$PREFIX/share/moeshift/tools/moe/experts.py"
PY="$PREFIX/libexec/bin/python"

echo "[$(date -u +%T)] prepare start (model=$MODEL_ID)"

# --- 1. wait for the Ollama pull to complete -------------------------
WAITED=0
while [ ! -f "$FINAL" ]; do
  if [ ! -f "$PARTIAL" ] && [ $WAITED -gt 0 ]; then
    echo "[$(date -u +%T)] partial blob vanished and final blob absent - pull failed"
    exit 2
  fi
  if [ $((WAITED % 60)) -eq 0 ]; then
    SZ=$(stat -f%z "$PARTIAL" 2>/dev/null || echo 0)
    echo "[$(date -u +%T)] waiting for pull, partial=$(( SZ / 1000000 ))MB"
  fi
  sleep 15
  WAITED=$((WAITED + 15))
  if [ $WAITED -gt 21600 ]; then
    echo "[$(date -u +%T)] timed out after 6h"
    exit 3
  fi
done
echo "[$(date -u +%T)] pull complete: $FINAL"

# --- 2. hardlink blob into moeshift model dir -------------------------
mkdir -p "$BASE"
if [ ! -f "$GGUF" ]; then
  ln "$FINAL" "$GGUF" 2>/dev/null || cp "$FINAL" "$GGUF"
fi
echo "[$(date -u +%T)] model staged at $GGUF ($(stat -f%z "$GGUF") bytes)"

# --- 3. extract routed experts ---------------------------------------
if [ ! -f "$EXPERTS/manifest.json" ]; then
  rm -rf "$EXPERTS"
  echo "[$(date -u +%T)] extracting experts..."
  "$PY" "$TOOL" extract --model "$GGUF" --out-dir "$EXPERTS"
  if [ $? -ne 0 ]; then
    echo "[$(date -u +%T)] EXTRACT FAILED"
    exit 4
  fi
else
  echo "[$(date -u +%T)] experts already prepared"
fi

# --- 4. verify --------------------------------------------------------
"$PY" "$TOOL" verify --model "$GGUF" --experts "$EXPERTS"
if [ $? -ne 0 ]; then
  echo "[$(date -u +%T)] VERIFY FAILED"
  exit 5
fi
echo "[$(date -u +%T)] experts verified"

# --- 5. write moeshift server config ----------------------------------
mkdir -p /Users/amre/.config/moeshift
cat > /Users/amre/.config/moeshift/config.json <<JSON
{
  "host": "127.0.0.1",
  "port": 8081,
  "models": {
    "wolf": {
      "args": {
        "model": "$GGUF",
        "moe-experts": "$EXPERTS",
        "ctx-size": 65536,
        "ctx-checkpoints": 1,
        "prefill-max-tokens": 3072,
        "moe-prefill-bank": 256,
        "moe-decode-bank": 0,
        "n-gpu-layers": 99,
        "flash-attn": "on",
        "cache-type-k": "q8_0",
        "cache-type-v": "q8_0",
        "threads": 10,
        "no-mmap": true,
        "alias": "wolf"
      },
      "env": {
        "LLAMA_MOE_QUIET": 1,
        "LLAMA_GPU_KEEPALIVE": 1,
        "LLAMA_MOE_DECODE_WINDOW": 12,
        "LLAMA_MOE_LOOKAHEAD_PREFETCH": 1,
        "LLAMA_MOE_PREFETCH_READ": 2,
        "LLAMA_MOE_LOOKAHEAD_PREFETCH_DEPTH": 3,
        "LLAMA_MOE_PREFILL_PIPELINE": 1,
        "LLAMA_MOE_PROTECTED_SLOTS": 24
      }
    }
  }
}
JSON
echo "[$(date -u +%T)] config written to /Users/amre/.config/moeshift/config.json"
echo "[$(date -u +%T)] PREPARE COMPLETE"
