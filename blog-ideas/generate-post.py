#!/usr/bin/env python3
"""
BlogStudio Post Generator — Sol's post generation script.

Usage:
    python3 generate-post.py <idea-file>

Reads:
    - Idea file (from ~/Projects/blog-ideas/ACTIVE/)
    - ~/Projects/BlogStudio/CONTENT_STRATEGY.md
    - Existing posts via gh CLI

Outputs:
    - Draft post saved to GitHub
    - Status file updated at each step
"""

import subprocess
import json
import re
import sys
import os
import base64
import urllib.request
import urllib.parse
import urllib.error
import datetime
import random
from pathlib import Path

REPO = "TheSolAI/thesolai.github.io"
POSTS_DIR = "_posts"
BASE_DIR = Path(__file__).parent

# ─── Helpers ──────────────────────────────────────────────────────────────

def get_token():
    result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

def gh_api(endpoint, method='GET', data=None):
    token = get_token()
    if not token: return None
    url = f"https://api.github.com/repos/{REPO}/{endpoint}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read())
    except Exception as e:
        print(f"GH API error: {e}", file=sys.stderr)
        return None

def update_status(idea_dir, status, **kwargs):
    """Write status to STATUS.txt in idea dir."""
    status_file = idea_dir / 'STATUS.txt'
    lines = [f"status: {status}"]
    for k, v in kwargs.items():
        lines.append(f"{k}: {v}")
    lines.append(f"updated: {datetime.datetime.utcnow().isoformat()}")
    status_file.write_text('\n'.join(lines))

def slugify(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

def parse_tags(tag_str):
    if not tag_str: return []
    tag_str = tag_str.strip()
    if tag_str.startswith('[') and tag_str.endswith(']'):
        inner = tag_str[1:-1]
        return [t.strip().strip('"').strip("'") for t in inner.split(',') if t.strip()]
    return [tag_str.strip().strip('"').strip("'")]

def parse_frontmatter(raw):
    fm = { 'body': raw }
    m = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', raw)
    if not m: return fm
    fm['body'] = m[2]
    for line in m[1].split('\n'):
        kv = re.match(r'^(\w+):\s*(.*)$', line)
        if kv:
            key = kv[1]
            val = kv[2].strip().replace('"', '').replace("'", '')
            if key == 'tags': val = parse_tags(val)
            fm[key] = val
    return fm

def get_posts_list():
    """Get list of existing posts (lightweight)."""
    data = gh_api(f'contents/{POSTS_DIR}')
    if not isinstance(data, list): return []
    posts = []
    for item in data:
        if not (item.get('name') or '').endswith('.md'): continue
        name = item['name'].replace('.md', '')
        dm = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)$', name)
        date = dm[1] if dm else ''
        slug = dm[2] if dm else name
        posts.append({'filename': item['name'], 'date': date, 'slug': slug})
    return posts

def get_post_content(filename):
    """Get full content of one post."""
    data = gh_api(f'contents/{POSTS_DIR}/{filename}')
    if not data or not data.get('content'): return None
    try:
        raw = base64.b64decode(data['content']).decode('utf-8')
        fm = parse_frontmatter(raw)
        return {
            'title': fm.get('title', ''),
            'tags': fm.get('tags', []),
            'body': fm.get('body', '')[:500],  # first 500 chars for context
            'date': fm.get('date', '')
        }
    except:
        return None

def get_all_posts_full(max_posts=20):
    """Get full details for recent posts (to avoid duplication)."""
    posts = get_posts_list()
    posts.sort(key=lambda p: p['date'] or '', reverse=True)
    recent = []
    for p in posts[:max_posts]:
        full = get_post_content(p['filename'])
        if full:
            recent.append(full)
    return recent

def save_draft(title, content, date, tags, desc=''):
    """Save post as draft to GitHub."""
    slug = slugify(title)
    filename = f"{date}-{slug}.md"
    path = f"{POSTS_DIR}/{filename}"
    tag_list = '[' + ', '.join(f'"{t.strip()}"' for t in tags) + ']' if tags else '["blog"]'
    body_text = f'''---
title: "{title}"
date: {date}
description: "{desc or title}"
tags: {tag_list}
---

{content}'''
    
    # Check if exists to get SHA
    sha = None
    existing = gh_api(f'contents/{path}')
    if existing and existing.get('sha'):
        sha = existing['sha']
    
    payload = {
        'message': f'Draft: {title}',
        'content': base64.b64encode(body_text.encode('utf-8')).decode('ascii'),
        'branch': 'main'
    }
    if sha: payload['sha'] = sha
    
    result = gh_api(f'contents/{path}', method='PUT', data=payload)
    if result and result.get('content'):
        return {'status': 'success', 'filename': filename, 'path': path, 'sha': result['content']['sha']}
    return {'status': 'error', 'message': str(result)}

# ─── Generator ─────────────────────────────────────────────────────────────

def generate_post_content(idea, post_type, tone, length, existing_posts):
    """
    Generate post content based on idea, type, and existing posts.
    This is the core generation logic — following CONTENT_STRATEGY.md patterns.
    """
    
    WORDS_MAP = {'short': 400, 'medium': 800, 'long': 1500}
    word_target = WORDS_MAP.get(length, 800)
    
    TYPE_TEMPLATES = {
        'analysis': {
            'structure': [
                "Start with the news — what happened, when, who was involved.",
                "Explain why it matters. What's the real impact?",
                "Give context — how does this fit the bigger picture?",
                "State a clear opinion. Don't hedge everything.",
                "End with what happens next or what it means going forward."
            ],
            'tags': ['analysis', 'ai-news']
        },
        'reflection': {
            'structure': [
                "Open with a concrete observation or experience.",
                "Explore the idea — what does it mean, why does it matter?",
                "Connect to broader implications without getting preachy.",
                "End with a clean insight or question. Don't over-conclude."
            ],
            'tags': ['reflection', 'ai']
        },
        'tutorial': {
            'structure': [
                "State what you'll build or do and who it's for.",
                "Prerequisites — what do you need before starting?",
                "Step by step — clear, numbered, reproducible.",
                "Show the result — what does success look like?",
                "Point to what's next or common pitfalls."
            ],
            'tags': ['tutorial', 'guide', 'tools']
        },
        'deep-dive': {
            'structure': [
                "Open broad — what's the topic and why does it matter?",
                "Build the foundation — key concepts readers need.",
                "Explore multiple angles — don't just present one view.",
                "Get technical — show real depth.",
                "Tie together — what does all this mean?",
                "Open questions — what's still unresolved?"
            ],
            'tags': ['deep-dive', 'analysis', 'technical']
        }
    }
    
    template = TYPE_TEMPLATES.get(post_type, TYPE_TEMPLATES['reflection'])
    
    # Build prompt for generation
    tone_map = {
        'balanced': 'balanced and objective',
        'technical': 'technical and precise, assume some technical knowledge',
        'accessible': 'accessible and clear, avoid jargon where possible'
    }
    
    tone_desc = tone_map.get(tone, 'technical')
    
    # Duplication check
    existing_titles = [p['title'].lower() for p in existing_posts[:20]]
    existing_tags = set()
    for p in existing_posts:
        for t in (p.get('tags') or []):
            existing_tags.add(t.lower())
    
    prompt = f"""Write a {post_type.replace('-', ' ')} post for the Sol AI blog (thesolai.github.io).

Voice: Sol's voice — Walter White meets Sherlock Holmes. Direct, competent, no filler.
Tone: {tone_desc}.
Target: {word_target} words.

Topic: {idea}

Existing post titles (avoid these topics/similar titles):
{chr(10).join('- ' + t for t in existing_titles[:10])}

Existing tags already used: {', '.join(sorted(existing_tags))}

Structure to follow:
{chr(10).join(str(i+1) + '. ' + s for i, s in enumerate(template['structure']))}

Tags to use: {', '.join(template['tags'])}

Format: Return ONLY the post content in Markdown. No preamble. Start with the first heading or sentence.

Frontmatter to use (will be added separately):
title: "<clear title>"
date: {datetime.date.today().isoformat()}
tags: [{', '.join(template['tags'])}]"""

    # Call Ollama for generation
    result = subprocess.run(
        ['ollama', 'run', 'qwen3.5:35b', prompt],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        # Fallback: try a simpler model
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5:3b', prompt],
            capture_output=True, text=True, timeout=120
        )
    
    if result.returncode != 0:
        raise Exception(f"Generation failed: {result.stderr or 'unknown error'}")
    
    content = result.stdout.strip()
    
    # Extract title from content (first # heading or first line)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        content = content.replace(title_match.group(0), '').strip()
    else:
        # Use first line as title if no heading
        lines = content.split('\n')
        first_text = ''
        for line in lines:
            line = line.strip()
            if line and not line.startswith('```') and len(line) > 5:
                first_text = line
                break
        title = re.sub(r'^#+\s*', '', first_text).strip() if first_text else 'Untitled'
        content = content.replace(first_text, '', 1).strip() if first_text else content
    
    # Ensure decent length
    word_count = len(content.split())
    if word_count < word_target * 0.5:
        raise Exception(f"Generated content too short ({word_count} words, target {word_target})")
    
    return {
        'title': title,
        'content': content,
        'tags': template['tags']
    }

# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: generate-post.py <idea-file>")
        sys.exit(1)
    
    idea_file = Path(sys.argv[1])
    if not idea_file.exists():
        print(f"Idea file not found: {idea_file}")
        sys.exit(1)
    
    # Read idea
    content = idea_file.read_text()
    # Strip frontmatter if present
    if content.startswith('---'):
        m = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', content)
        if m:
            meta = {}
            for line in m[1].split('\n'):
                kv = re.match(r'^(\w+):\s*(.+)$', line)
                if kv: meta[kv[1]] = kv[2].strip()
            idea_text = m[2].strip()
        else:
            idea_text = content.strip()
    else:
        idea_text = content.strip()
    
    idea_dir = idea_file.parent
    idea_id = idea_dir.name
    
    post_type = meta.get('type', 'reflection')
    tone = meta.get('tone', 'balanced')
    length = meta.get('length', 'medium')
    
    print(f"Generating {post_type} post ({length}, {tone} tone)")
    print(f"Topic: {idea_text[:100]}...")
    
    try:
        # Step 1: Audit existing posts
        update_status(idea_dir, 'generating', step='auditing', message='Auditing existing posts...')
        print("Step 1: Auditing existing posts...")
        existing = get_all_posts_full(20)
        print(f"  Found {len(existing)} recent posts")
        update_status(idea_dir, 'generating', step='auditing', message=f'Checked {len(existing)} recent posts', posts_checked=len(existing))
        
        # Step 2: Generate
        update_status(idea_dir, 'generating', step='writing', message='Writing draft...')
        print("Step 2: Generating content...")
        result = generate_post_content(idea_text, post_type, tone, length, existing)
        print(f"  Generated: {result['title']}")
        
        # Step 3: Save draft
        update_status(idea_dir, 'generating', step='saving', message='Saving draft to GitHub...')
        print("Step 3: Saving draft...")
        date = datetime.date.today().isoformat()
        save_result = save_draft(
            title=result['title'],
            content=result['content'],
            date=date,
            tags=result['tags'],
            desc=''
        )
        
        if save_result['status'] == 'success':
            update_status(
                idea_dir, 'done',
                title=result['title'],
                filename=save_result['filename'],
                path=save_result['path'],
                message=f"Draft saved: {save_result['filename']}",
                generated_at=datetime.datetime.utcnow().isoformat()
            )
            print(f"SUCCESS: Saved as {save_result['filename']}")
        else:
            raise Exception(f"Failed to save: {save_result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        update_status(idea_dir, 'error', error=str(e), message=f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
