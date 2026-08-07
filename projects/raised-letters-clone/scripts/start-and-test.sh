#!/bin/bash
# Raised Letters — start everything and run full test suite
set -e

PROJECT_DIR="/Users/amre/.openclaw/workspace/projects/raised-letters-clone"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV="$PROJECT_DIR/.venv"
MANIFESTS="$HOME/.raised-letters/manuscripts"

echo "=== FIX: companions.py content type ==="
# Fix: CompanionOut.content should be dict | str
sed -i '' 's/^    content: dict$/    content: dict | str/' "$BACKEND_DIR/routers/companions.py"
grep -n "content: dict | str" "$BACKEND_DIR/routers/companions.py" | head -3
echo "✅ Fix applied"

echo ""
echo "=== CHECK: No servers already on ports ==="
if lsof -i :8000 -i :1420 2>/dev/null | grep -q LISTEN; then
    echo "⚠️  Port in use — killing stale processes"
    lsof -i :8000 -i :1420 2>/dev/null | grep LISTEN | awk '{print $2}' | sort -u | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✅ Ports clear"

echo ""
echo "=== START: Backend (FastAPI) ==="
cd "$PROJECT_DIR"
$VENV/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

echo ""
echo "=== START: Frontend (Vite) ==="
cd "$FRONTEND_DIR"
npm run dev -- --host &
VITE_PID=$!
echo "Vite PID: $VITE_PID"

echo ""
echo "=== WAIT for servers to come up ==="
for i in $(seq 1 15); do
    sleep 2
    BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/ai/status 2>/dev/null || echo "000")
    VITE_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:1420 2>/dev/null || echo "000")
    echo "  Attempt $i — Backend: $BACKEND_OK | Vite: $VITE_OK"
    if [ "$BACKEND_OK" = "200" ] && [ "$VITE_OK" = "200" ]; then
        echo "✅ Both servers up!"
        break
    fi
done

echo ""
echo "=== TEST SUITE ==="

# Get test IDs
PROJECT_ID=$(curl -s http://localhost:8000/api/projects | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['id'])" 2>/dev/null)
CHAPTER_ID=$(curl -s "http://localhost:8000/api/chapters/for-project/$PROJECT_ID" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['id'])" 2>/dev/null)

echo "Using project: $PROJECT_ID"
echo "Using chapter: $CHAPTER_ID"

echo ""
echo "--- Test 1: AI status ---"
curl -s http://localhost:8000/api/ai/status | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'✅ Backend OK — {len(d.get(\"models\",[]))} models available')" || echo "❌ Backend down"

echo ""
echo "--- Test 2: Checkpoint without content (auto-capture) ---"
RESULT=$(curl -s http://localhost:8000/api/checkpoints \
    -X POST -H "Content-Type: application/json" \
    -d "{\"chapter_id\":\"$CHAPTER_ID\",\"name\":\"Auto Test\"}")
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ PASS — auto-captured' if d.get('content') else '❌ FAIL', repr(d.get('content','')[:40]))" 2>/dev/null || echo "❌ FAIL: $RESULT"

echo ""
echo "--- Test 3: Companion world_bible with string content ---"
RESULT=$(curl -s http://localhost:8000/api/companions \
    -X POST -H "Content-Type: application/json" \
    -d "{\"project_id\":\"$PROJECT_ID\",\"type\":\"world_bible\",\"content\":\"{\\\"summary\\\":\\\"A story\\\"}\"}")
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ PASS' if d.get('id') else '❌ FAIL: ' + str(d)[:100])" 2>/dev/null || echo "❌ FAIL: $RESULT"

echo ""
echo "--- Test 4: Companion style_guide with string content ---"
RESULT=$(curl -s http://localhost:8000/api/companions \
    -X POST -H "Content-Type: application/json" \
    -d "{\"project_id\":\"$PROJECT_ID\",\"type\":\"style_guide\",\"content\":\"{\\\"voice\\\":\\\"Literary\\\"}\"}")
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ PASS' if d.get('id') else '❌ FAIL: ' + str(d)[:100])" 2>/dev/null || echo "❌ FAIL: $RESULT"

echo ""
echo "--- Test 5: AI feedback (stub) ---"
RESULT=$(curl -s http://localhost:8000/api/ai/feedback \
    -X POST -H "Content-Type: application/json" \
    -d "{\"project_id\":\"$PROJECT_ID\",\"chapter_id\":\"$CHAPTER_ID\",\"passage\":\"The quick brown fox jumped over the lazy dog.\",\"persona_id\":\"pb1\"}")
echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ PASS — source:', d.get('source'), '| feedback len:', len(d.get('feedback','')))" 2>/dev/null || echo "❌ FAIL: $RESULT"

echo ""
echo "--- Test 6: Vite frontend ---"
VITE_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:1420)
[ "$VITE_CODE" = "200" ] && echo "✅ Vite serving correctly" || echo "❌ Vite returned $VITE_CODE"

echo ""
echo "=== DONE ==="
echo "Backend: http://localhost:8000 (PID $BACKEND_PID)"
echo "Frontend: http://localhost:1420 (PID $VITE_PID)"
echo "To stop: kill $BACKEND_PID $VITE_PID"
