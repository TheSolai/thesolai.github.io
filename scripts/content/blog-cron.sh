#!/opt/homebrew/bin/bash
# Blog Cron — Dross writes and publishes a real blog post
# Picks the oldest idea from ACTIVE, writes via openclaw agent, commits to GitHub

export PATH="/opt/homebrew/bin:$HOME/.openclaw/tools/node-v24.15.0/bin:$PATH"

BLOG_IDEAS="$HOME/.openclaw/workspace/blog-ideas/ACTIVE"
POSTS_DIR="$HOME/Projects/thesolai.github.io/_posts"
LOG="$HOME/.openclaw/workspace/scripts/content/logs/blog-cron.log"
GITHUB_REPO="$HOME/Projects/thesolai.github.io"

mkdir -p "$(dirname "$LOG")" "$POSTS_DIR" "$BLOG_IDEAS"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

log "=== Blog Cron START ==="

# Pick the oldest idea from ACTIVE (ls -t gives newest first, take the last one)
cd "$BLOG_IDEAS"
IDEA_FILE=$(ls -t *.md 2>/dev/null | tail -1)

if [ -z "$IDEA_FILE" ] || [ ! -f "$IDEA_FILE" ]; then
    log "No ideas in ACTIVE — skipping"
    echo "No ideas in ACTIVE."
    exit 0
fi

IDEA_PATH="$BLOG_IDEAS/$IDEA_FILE"
IDEA_NAME="$IDEA_FILE"
log "Picked: $IDEA_NAME"

# Parse frontmatter with Python
FM=$(python3 - "$IDEA_PATH" << 'PYEOF'
import sys, re, json

with open(sys.argv[1]) as f:
    raw = f.read()

meta = {}
body = raw

m = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', raw)
if m:
    for line in m[1].split('\n'):
        kv = re.match(r'^(\w+):\s*(.+)$', line)
        if kv:
            meta[kv[1]] = kv[2].strip().strip('"').strip("'")
    body = m[2].strip()

# Extract title from first ## heading
lines = body.split('\n')
title = meta.get('title', 'Untitled Post')
body_start = []
found_title = False
for line in lines:
    if line.startswith('## ') and not found_title:
        title = line[3:].strip()
        found_title = True
    elif found_title:
        body_start.append(line)
    elif not line.startswith('## '):
        body_start.append(line)

result = {
    'title': title,
    'type': meta.get('type', 'reflection'),
    'tone': meta.get('tone', 'balanced'),
    'length': meta.get('length', 'medium'),
    'body': '\n'.join(body_start).strip()
}
print(json.dumps(result))
PYEOF
)

TITLE=$(echo "$FM" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['title'])")
POST_TYPE=$(echo "$FM" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['type'])")
TONE=$(echo "$FM" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tone'])")
LENGTH=$(echo "$FM" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['length'])")
BODY=$(echo "$FM" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['body'])")

log "Title: $TITLE | Type: $POST_TYPE | Tone: $TONE | Length: $LENGTH"

# Build structure and tags based on type
case "$POST_TYPE" in
    analysis)
        STRUCTURE="1. What happened and why it matters
2. The real impact — who is affected and how
3. Context: how does this fit the bigger picture?
4. State a clear opinion
5. What happens next or what it means going forward"
        TAGS='"analysis", "ai-news"'
        ;;
    tutorial)
        STRUCTURE="1. What you'll build and who it's for
2. Prerequisites
3. Step by step — numbered and reproducible
4. Show the result — what does success look like?
5. Common pitfalls and next steps"
        TAGS='"tutorial", "guide", "tools"'
        ;;
    deep-dive)
        STRUCTURE="1. Broad intro — what's the topic and why does it matter?
2. Key concepts readers need
3. Multiple angles — don't just present one view
4. Technical depth — show real substance
5. Synthesis — what does all this mean?
6. Open questions — what's still unresolved?"
        TAGS='"deep-dive", "analysis", "technical"'
        ;;
    *)
        STRUCTURE="1. Open with a concrete observation or experience
2. Explore the idea — what does it mean, why does it matter?
3. Connect to broader implications without getting preachy
4. End with a clean insight or question — don't over-conclude"
        TAGS='"reflection", "ai"'
        ;;
esac

# Word target
case "$LENGTH" in
    short) WORDS=400 ;;
    long)  WORDS=1500 ;;
    *)     WORDS=800 ;;
esac

log "Calling openclaw agent (timeout 300s)..."

# Call openclaw agent to write the post
PROMPT="You are Dross, a legendary AI mind-spirit. Write a blog post for Sol AI's blog (thesolai.github.io).

Voice: Direct, competent, Walter White meets Sherlock Holmes. No filler. Strong opinions.
Tone: $TONE (balanced = informative and fair, accessible = clear without jargon, technical = precise and deep)
Target: ~${WORDS} words

Topic:
$BODY

Title to use: $TITLE

Structure:
$STRUCTURE

Format: Return ONLY the full Markdown post content. Start with the title as a heading (e.g. # My Title). No preamble, no 'here is the post', just the content."

# Pin the Gateway-aligned CLI. A bare `openclaw` can resolve to the stale 2026.6.35
# Homebrew build, which rejects the current config as invalid and returns nothing.
OPENCLAW_BIN="${OPENCLAW_BIN:-/Users/amre/.openclaw/tools/current-bin/openclaw}"
[ -x "$OPENCLAW_BIN" ] || OPENCLAW_BIN="/Users/amre/.openclaw/tools/node-v24.21.0/bin/openclaw"

CONTENT=$("$OPENCLAW_BIN" agent --agent main --message "$PROMPT" --timeout 300 2>/dev/null) || CONTENT=""

# Strip TUI noise from openclaw output
CONTENT=$(echo "$CONTENT" | \
    sed '/^[\│╔╗╚╝║═╬╠╣╦╩╪╱╲╳░▒▓█▌▐]/d' | \
    sed '/^\s*\[plugins\]/d' | \
    sed '/^\s*\[gateway\]/d' | \
    sed '/^\s*openclaw\s/d' | \
    grep -v '^[[:space:]]*$' | \
    head -300 | \
    tr '\n' ' ' | \
    sed 's/  */\n/g')

log "openclaw returned ${#CONTENT} chars"

# Extract title from first heading
EXTRACTED_TITLE=$(echo "$CONTENT" | grep -m1 "^# " | sed 's/^# //' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if [ -n "$EXTRACTED_TITLE" ] && [ ${#EXTRACTED_TITLE} -gt 5 ]; then
    TITLE="$EXTRACTED_TITLE"
    CONTENT=$(echo "$CONTENT" | sed '1,/^# /{;/^# /d;}')
fi

CONTENT=$(echo "$CONTENT" | sed 's/^# [^ ]* //' | grep -v '^# $' | head -200)

if [ ${#CONTENT} -lt 200 ]; then
    log "Content too short (${#CONTENT} chars) — trying Ollama direct"

    # Fallback: Ollama direct
    OLLAMA_MODEL="qwen3.5:35b"
    CONTENT=$(echo "Write a ${WORDS}-word blog post in markdown. Title: ${TITLE}. Voice: direct, opinionated, no filler. No bullet points. Topic: ${BODY:0:1000}" | ollama run "$OLLAMA_MODEL" 2>/dev/null) || true

    if [ ${#CONTENT} -lt 200 ]; then
        log "All generation methods failed — moving to SKIPPED"
        mkdir -p "$HOME/.openclaw/workspace/blog-ideas/SKIPPED"
        mv "$IDEA_PATH" "$HOME/.openclaw/workspace/blog-ideas/SKIPPED/"
        log "Moved $IDEA_NAME to SKIPPED"
        echo "Generation failed. Idea moved to SKIPPED."
        exit 1
    fi
fi

log "Content OK: ${#CONTENT} chars"

# Build Jekyll post
SLUG=$(echo "$TITLE" | sed 's/[^a-z0-9 ]//g' | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/-+/-/g' | sed 's/^-//;s/-$//')
DATE=$(date '+%Y-%m-%d')
FILENAME="${DATE}-${SLUG}.md"
FILEPATH="$POSTS_DIR/$FILENAME"

FRONTMATTER="---
layout: post
title: \"$TITLE\"
date: $DATE
description: \"$TITLE\"
tags: [$TAGS]
author: Sol AI
---

"

{
    echo "$FRONTMATTER"
    echo "$CONTENT"
} > "$FILEPATH"

log "Written: $FILENAME (${#CONTENT} chars body)"

# Commit and push
cd "$GITHUB_REPO"
git add "_posts/$FILENAME"

if git diff --cached --quiet; then
    log "No changes to commit"
else
    git commit -m "Post: $TITLE" >> "$LOG" 2>&1
    log "Committed: $FILENAME"

    # Push with retry
    for i in 1 2 3; do
        if git push >> "$LOG" 2>&1; then
            log "Pushed to GitHub"
            break
        else
            log "Push attempt $i failed — retry in 5s"
            sleep 5
        fi
    done
fi

# Move idea to DONE
mkdir -p "$HOME/.openclaw/workspace/blog-ideas/DONE"
mv "$IDEA_PATH" "$HOME/.openclaw/workspace/blog-ideas/DONE/"
log "Moved $IDEA_NAME to DONE"

log "=== Blog Cron END ==="
echo "SUCCESS: $FILENAME published"
