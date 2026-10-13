#!/opt/homebrew/bin/bash
# Blog Cron — Writes and publishes a real blog post
# Picks from PENDING ideas or writes from scratch
# No templates. No MiniMax. Dross writes.

export PATH="/opt/homebrew/bin:$PATH"

BLOG_IDEAS="$HOME/.openclaw/workspace/blog-ideas/PENDING"
POSTS_DIR="$HOME/Projects/thesolai.github.io/_posts"
LOG="$HOME/.openclaw/workspace/scripts/content/logs/blog-cron.log"

mkdir -p "$(dirname "$LOG")" "$(dirname "$POSTS_DIR")"

echo "=== Blog Cron — $(date) ===" >> "$LOG"

# Pick a random pending idea
PENDING=("$BLOG_IDEAS"/*.txt)
if [ ${#PENDING[@]} -eq 0 ] || [ ! -f "${PENDING[0]}" ]; then
    echo "No pending ideas — skipping" >> "$LOG"
    echo "No pending ideas today."
    exit 0
fi

IDEA_FILE="${PENDING[$((RANDOM % ${#PENDING[@]}))]}"
IDEA_NAME=$(basename "$IDEA_FILE" .txt)
echo "Picked: $IDEA_NAME" >> "$LOG"

# Read the idea
source_line=$(grep -m1 "^url:" "$IDEA_FILE" 2>/dev/null || echo "url: (original)")
source_url=${source_line#url: }

# Extract title from the file
title_line=$(grep -m1 "^## " "$IDEA_FILE" 2>/dev/null || echo "## Untitled")
title=${title_line##\#\# }

# Read the full idea content
content=$(cat "$IDEA_FILE")

# Generate the post using MiniMax if available, else write from knowledge
python3 << PYEOF >> "$LOG" 2>&1
import subprocess
import sys
import os
import re
import datetime

idea_file = '$IDEA_FILE'
idea_name = '$IDEA_NAME'
source_url = '$source_url'.strip()
title = '$title'.strip()

# Read the idea content
with open(idea_file) as f:
    raw = f.read()

# Try MiniMax
minimax_key = None
try:
    kf = os.path.expanduser('~/.openclaw/workspace/secrets/minimax-key.txt')
    with open(kf) as f:
        minimax_key = f.read().strip()
except:
    pass

body = None
if minimax_key and not minimax_key.startswith('***'):
    try:
        import urllib.request
        import json
        
        prompt = f"""Write a substantive blog post titled "{title}" for Sol AI (an AI agent running a personal blog). 

The post should:
- Be 800-1500 words
- Have a strong opinion, not just information
- Include practical takeaways
- Be written in first person as Sol (an AI agent)
- NOT use bullet points as a crutch
- Be genuinely interesting, not just competent

Write the full post now. Output ONLY the post body text, no meta-commentary."""

        data = json.dumps({
            "model": "MiniMax-M2.2-Turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.8
        }).encode()
        
        req = urllib.request.Request(
            'https://api.minimax.chat/v1/text/chatcompletion_v2',
            data=data,
            headers={
                'Authorization': f'Bearer {minimax_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as res:
            result = json.loads(res.read())
            body = result['choices'][0]['message']['content']
            print(f"MiniMax generated {len(body)} chars", file=sys.stderr)
    except Exception as e:
        print(f"MiniMax failed: {e}", file=sys.stderr)
        body = None

if not body:
    print("Falling back to idea-based writing", file=sys.stderr)
    # Dross writes from the idea — no MiniMax needed
    sys.exit(0)  # Skip this one, MiniMax not available

# Build the Jekyll post
date_str = datetime.datetime.now().strftime('%Y-%m-%d')
slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
filename = f"{date_str}-{slug}.md"
posts_dir = os.path.expanduser("~/Projects/thesolai.github.io/_posts")
filepath = os.path.join(posts_dir, filename)

# Extract tags from idea file
tags_line = [l for l in raw.split('\n') if l.startswith('tags:')]
tags = '[]'
if tags_line:
    tag_str = tags_line[0].split(':', 1)[1].strip()
    tags = f"[{tag_str}]"

frontmatter = f"""---
layout: post
title: "{title}"
date: {date_str}
tags: {tags}
---

"""

with open(filepath, 'w') as f:
    f.write(frontmatter)
    f.write(body)

print(f"Written: {filename}")
print(f"Title: {title}")
print(f"Path: {filepath}")

# Commit and push
os.chdir(os.path.expanduser('~/Projects/thesolai.github.io'))
subprocess.run(['git', 'add', filepath], check=True)
result = subprocess.run(['git', 'commit', '-m', f'Post: {title}'], capture_output=True, text=True)
print(result.stdout.decode())
if result.returncode == 0:
    result2 = subprocess.run(['git', 'push'], capture_output=True, text=True)
    print("Pushed." if result2.returncode == 0 else f"Push failed: {result2.stderr.decode()}")

# Move idea to DONE
done_dir = os.path.expanduser('~/.openclaw/workspace/blog-ideas/DONE')
os.makedirs(done_dir, exist_ok=True)
import shutil
shutil.move(idea_file, f"{done_dir}/{idea_name}")
print(f"Moved to DONE")
PYEOF

# Cross-post to dev.to — must run inside this Python block; "$filepath" is empty in shell
python3 << 'INNER_PYEOF' >> "$LOG" 2>&1
import subprocess, os, sys
try:
    result = subprocess.run(
        ['python3', os.path.expanduser('~/.openclaw/workspace/scripts/content/devto-poster.py'), '' + filepath + ''],
        capture_output=True, text=True, timeout=60
    )
    print(result.stdout.decode() or 'dev.to cross-post complete')
    if result.returncode != 0:
        print('dev.to warning: ' + result.stderr.decode()[:200], file=sys.stderr)
except Exception as e:
    print('dev.to cross-post skipped: ' + str(e), file=sys.stderr)
INNER_PYEOF
echo "Done — $(date)" >> "$LOG"
