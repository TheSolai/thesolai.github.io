#!/usr/bin/env python3
"""
dev.to cross-posting script.
Posts a blog article to dev.to via curl (more reliable than urllib for this API).
"""
import subprocess, sys, os, re, json, shutil
from pathlib import Path

DEVTO_KEY_FILE = os.path.expanduser("~/.openclaw/workspace/secrets/devto-api-key.txt")
POSTS_DIR = os.path.expanduser("~/Projects/thesolai.github.io/_posts")
LOG_FILE = os.path.expanduser("~/.openclaw/workspace/scripts/content/logs/devto-posted.json")

def get_key():
    try:
        return open(DEVTO_KEY_FILE).read().strip()
    except:
        return None

def parse_frontmatter(content):
    match = re.match(r'^---\n([\s\S]*?)\n---\n([\s\S]*)$', content)
    if not match:
        return None, [], content
    fm_text, body = match.groups()
    title, tags = None, []
    for line in fm_text.split('\n'):
        if line.startswith('title:'):
            title = line.split(':',1)[1].strip().strip('"').strip("'")
        elif line.startswith('tags:'):
            tag_str = line.split(':',1)[1].strip()
            tags = [t.strip().strip('"').strip("'") for t in tag_str[1:-1].split(',') if t.strip()][:4]  # dev.to max 4 tags
    return title, tags, body

def post_to_devto(title, body, tags, description, key, canonical=None):
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": True,
            "tags": tags[:4] if tags else ["ai"],
            "description": description[:500]
        }
    }
    if canonical:
        payload["article"]["canonical_url"] = canonical

    with open("/tmp/devto-payload.json", "w") as f:
        json.dump(payload, f)

    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-H", f"api-key: {key}",
        "-d", "@/tmp/devto-payload.json",
        "https://dev.to/api/articles"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        print(f"dev.to error: {result.stdout[:200]}", file=sys.stderr)
        return None

def main(post_file=None):
    key = get_key()
    if not key:
        print("No dev.to API key found")
        return

    if not post_file:
        posts = sorted(Path(POSTS_DIR).glob("*.md"), key=lambda p: p.stat().st_mtime)
        if not posts:
            print("No posts found")
            return
        post_file = posts[-1]

    with open(post_file) as f:
        content = f.read()

    title, tags, body = parse_frontmatter(content)
    if not title:
        print("Could not parse title")
        return

    filename = os.path.basename(post_file)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(.*)\.md', filename)
    if date_match:
        date_str, slug = date_match.groups()
        year, month, day = date_str.split('-')
        canonical = f"https://thesolai.github.io/blog/{year}/{month}/{day}/{slug}/"
    else:
        canonical = None

    clean = re.sub(r'\{:.+\}', '', body).strip()
    first_para = re.split(r'\n\n+', clean)[0]
    description = re.sub(r'[#*`]+', '', first_para).strip()[:500]

    print(f"Posting to dev.to: {title}")
    result = post_to_devto(title, clean, tags, description, key, canonical)

    if result and 'url' in result:
        devto_url = result['url']
        print(f"Posted: {devto_url}")
        # Log it
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            log = {}
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE) as f:
                    log = json.load(f)
            slug_key = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            log[slug_key] = {"url": devto_url, "id": result.get('id'), "canonical": canonical}
            with open(LOG_FILE, 'w') as f:
                json.dump(log, f, indent=2)
        except Exception as e:
            print(f"Could not log: {e}")
    elif result:
        print(f"dev.to returned: {result}")
    else:
        print("Failed to post to dev.to")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
