#!/usr/bin/env python3
"""
Quick generation trigger — BlogStudio calls this to spawn a Sol sub-agent.
BlogStudio: python3 ~/Projects/blog-ideas/generate-post-cli.py <idea-file>

Uses `openclaw agent --agent main` to generate posts via Sol (MiniMax M2.7).
BlogStudio must be running on the same machine as the OpenClaw gateway.

Primary path: openclaw cron run "Blog Idea Generation"  →  Sol isolated session  →  GitHub
Secondary: python3 generate-post-cli.py <idea-file>  →  Sol via openclaw agent  →  GitHub
"""

import subprocess
import json
import sys
import os
import urllib.request
import base64
import re
import datetime

REPO = "TheSolAI/thesolai.github.io"
POSTS_DIR = "_posts"
GH_TOKEN = None

def get_token():
    global GH_TOKEN
    if GH_TOKEN: return GH_TOKEN
    result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
    GH_TOKEN = result.stdout.strip() if result.returncode == 0 else None
    return GH_TOKEN

def gh_api(endpoint, method='GET', data=None, branch='main'):
    token = get_token()
    if not token: return None
    url = f"https://api.github.com/repos/{REPO}/{endpoint}"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    if branch and branch != 'main':
        headers['X-GitHub-Api-Classic-Headers'] = ''
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read())
    except Exception as e:
        # Try with branch ref override
        if branch and branch != 'main':
            url_with_ref = f"https://api.github.com/repos/{REPO}/{endpoint}?ref=refs/heads/{branch}"
            req = urllib.request.Request(url_with_ref, method=method, data=body, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15) as res:
                    return json.loads(res.read())
            except: pass
        return None

def parse_frontmatter(raw):
    fm = {'body': raw}
    m = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', raw)
    if not m: return fm
    fm['body'] = m[2]
    for line in m[1].split('\n'):
        kv = re.match(r'^(\w+):\s*(.*)$', line)
        if kv:
            fm[kv[1]] = kv[2].strip().replace('"', '').replace("'", "")
    return fm

def create_branch_from_main(branch_name):
    """Create a new branch from main."""
    # Get main branch SHA
    main_ref = gh_api('git/ref/heads/main')
    if not main_ref or not main_ref.get('object', {}).get('sha'):
        return False
    sha = main_ref['object']['sha']
    result = gh_api('git/refs', method='POST', data={
        'ref': f'refs/heads/{branch_name}',
        'sha': sha
    })
    return result is not None

def save_draft(title, content, date, tags, desc='', branch='draft'):
    if branch != 'main':
        create_branch_from_main(branch)
    
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    filename = f"{date}-{slug}.md"
    path = f"{POSTS_DIR}/{filename}"
    tag_str = '[' + ', '.join(f'"{t.strip()}"' for t in tags) + ']' if tags else '["blog"]'
    body_text = f'---\ntitle: "{title}"\ndate: {date}\ndescription: "{desc or title}"\ntags: {tag_str}\nlayout: post\n---\n\n{content}'
    
    sha = None
    existing = gh_api(f'contents/{path}', branch=branch)
    if existing and existing.get('sha'): sha = existing['sha']
    
    payload = {'message': f'Draft: {title}', 'content': base64.b64encode(body_text.encode()).decode(), 'branch': branch}
    if sha: payload['sha'] = sha
    
    result = gh_api(f'contents/{path}', method='PUT', data=payload, branch=branch)
    if result and result.get('content'):
        return {'status': 'success', 'filename': filename, 'path': path, 'branch': branch}
    return {'status': 'error'}

def generate_with_openclaw(prompt):
    """Generate text using Sol via openclaw agent CLI."""
    result = subprocess.run(
        ['openclaw', 'agent', '--agent', 'main', '--message', prompt, '--timeout', '300'],
        capture_output=True, text=True, timeout=330
    )
    if result.returncode != 0:
        raise Exception(f"openclaw agent error (exit {result.returncode}): {result.stderr}")
    # Strip TUI noise: box drawing chars, plugin/gateway logging, empty lines
    lines = result.stdout.splitlines()
    clean_lines = []
    skip_mode = False
    for line in lines:
        stripped = line.strip()
        # Skip lines that are clearly plugin/gateway logging
        if stripped.startswith('[plugins]') or stripped.startswith('openclaw') or not stripped:
            continue
        # Skip box-drawing character lines (TUI startup noise)
        if re.match(r'^[\│╔╗╚╝║═╬╠╣╦╩╪╱╲╳░▒▓█▌▐◇\s─\-]+\s*$', line):
            skip_mode = True
            continue
        if skip_mode:
            # Continue skipping until we hit a normal content line
            if stripped and not re.match(r'^[\│╔╗╚╝║═╬╠╣╦╩╪╱╲╳░▒▓█▌▐]', stripped):
                skip_mode = False
            else:
                continue
        clean_lines.append(line)
    return '\n'.join(clean_lines).strip()

def generate_post(idea, post_type, tone, length, branch='main'):
    """Generate a full blog post using Sol via openclaw agent."""
    
    WORDS = {'short': 400, 'medium': 800, 'long': 1500}.get(length, 800)
    TONE_MAP = {'balanced': 'balanced and informative', 'technical': 'technical and precise', 'accessible': 'clear and accessible'}
    TONES = {'analysis': ['What happened', 'Why it matters', 'What it means going forward'],
             'reflection': ['Opening observation', 'Personal insight', 'Clean ending that invites thought'],
             'tutorial': ['What you will build', 'Step by step', 'Show the result', 'Next steps'],
             'deep-dive': ['Broad intro', 'Key concepts', 'Multiple angles', 'Technical depth', 'Synthesis']}
    
    tone_desc = TONE_MAP.get(tone, 'balanced')
    struct = TONES.get(post_type, TONES['reflection'])
    struct_str = '\n'.join(f"{i+1}. {s}" for i, s in enumerate(struct))
    
    # Get existing posts to avoid duplication
    posts = gh_api(f'contents/{POSTS_DIR}', branch=branch)
    existing_titles = []
    if isinstance(posts, list):
        posts.sort(key=lambda p: p.get('name',''), reverse=True)
        for p in posts[:10]:
            if p.get('name','').endswith('.md'):
                full = gh_api(f'contents/{POSTS_DIR}/{p["name"]}', branch=branch)
                if full and full.get('content'):
                    try:
                        raw = base64.b64decode(full['content']).decode('utf-8')
                        fm = parse_frontmatter(raw)
                        existing_titles.append(fm.get('title',''))
                    except: pass
    
    prompt = f"""Write a {post_type} blog post for the Sol AI blog (thesolai.github.io).

Voice: Sol's voice — direct, competent, Walter White meets Sherlock Holmes. No filler.
Tone: {tone_desc}.
Target: ~{WORDS} words.

Topic: {idea}

Structure:
{struct_str}

Already published (avoid these titles/topics):
{chr(10).join('- ' + t for t in existing_titles[:8]) if existing_titles else 'None yet'}

Format: Return ONLY the Markdown content. Start with a heading. No preamble.

"""

    content = generate_with_openclaw(prompt)
    
    # Extract title from first heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        content = content.replace(title_match.group(0), '', 1).strip()
    else:
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('```')]
        first = next((l for l in lines if len(l) > 10), 'Untitled')
        title = re.sub(r'^#+\s*', '', first).strip()
        content = content.replace(first, '', 1).strip()
    
    # Derive tags from type
    TAG_MAP = {'analysis': ['analysis', 'ai-news'], 'reflection': ['reflection', 'ai'],
               'tutorial': ['tutorial', 'guide'], 'deep-dive': ['deep-dive', 'analysis', 'technical']}
    
    return {'title': title, 'content': content, 'tags': TAG_MAP.get(post_type, ['blog'])}

def main():
    if len(sys.argv) < 2:
        print("Usage: generate-post-cli.py <idea-file>")
        sys.exit(1)
    
    idea_file = sys.argv[1]
    if not os.path.exists(idea_file):
        print(f"Idea file not found: {idea_file}")
        sys.exit(1)
    
    content = open(idea_file).read()
    meta = {}
    # Parse frontmatter
    if content.startswith('---'):
        m = re.match(r'^---\n([\s\S]*?)\n---\n?([\s\S]*)$', content)
        if m:
            for line in m[1].split('\n'):
                kv = re.match(r'^(\w+):\s*(.+)$', line)
                if kv: meta[kv[1]] = kv[2].strip()
            idea_text = m[2].strip()
        else:
            idea_text = content.strip()
    else:
        # Try to parse key: value pairs from top of file
        lines = content.split('\n')
        parsed_lines = []
        for i, line in enumerate(lines):
            kv = re.match(r'^(\w+):\s*(.+)$', line)
            if kv:
                meta[kv[1]] = kv[2].strip()
            else:
                parsed_lines = lines[i:]
                break
        idea_text = '\n'.join(parsed_lines).strip()
    
    post_type = meta.get('type', 'reflection')
    tone = meta.get('tone', 'balanced')
    length = meta.get('length', 'medium')
    github_path = meta.get('idea_github_path', '')
    
    print(f"Generating {post_type} post ({length}, {tone})...")
    print(f"Topic: {idea_text[:80]}...")
    
    # Save directly to main — no draft branches, no PRs
    date = datetime.date.today().isoformat()
    
    try:
        # Generate
        result = generate_post(idea_text, post_type, tone, length, branch='main')
        print(f"Generated: {result['title']}")
        
        # Save directly to main
        save_result = save_draft(result['title'], result['content'], date, result['tags'], branch='main')
        
        if save_result['status'] == 'success':
            print(f"SUCCESS: Published as {save_result['filename']} to main")
            # Delete the idea file
            os.unlink(idea_file)
            print(f"Cleaned up idea file")
            return 0
        else:
            print(f"Save failed: {save_result}")
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
