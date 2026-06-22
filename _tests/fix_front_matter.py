#!/usr/bin/env python3
"""
Fix missing front matter in blog posts.
Run: python3 _tests/fix_front_matter.py
"""
import re
from pathlib import Path
import sys

SITE_DIR = Path(__file__).parent.parent
POSTS_DIR = SITE_DIR / "_posts"

# Posts that are stubs - should not be published
STUBS = [
    "2026-06-22-thinking.md",
    "2026-06-22-the-ai-adoption-paradox-usage-vs-engineering.md",
]

# Clawhub posts needing description added
CLAWHUB_POSTS = [
    "clawhub-guide-2026-04-12.md",
    "clawhub-guide-2026-04-19.md",
    "clawhub-guide-2026-04-26.md",
    "clawhub-guide-2026-05-27.md",
    "clawhub-guide-2026-05-31.md",
    "clawhub-guide-2026-06-07.md",
    "clawhub-guide-2026-06-14.md",
    "clawhub-guide-2026-06-21.md",
    "deep-dive-2026-06-12.md",
]

# Posts needing date and layout fixed (from filename date)
DATE_FIXES = {
    "2026-06-21-us-states-ai-regulation-trump-executive-order.md": "2026-06-21",
    "2026-06-21-uk-google-cma-publishers-ai-search.md": "2026-06-21",
    "2026-06-21-eu-ai-act-omnibus-deal-nudification-ban.md": "2026-06-21",
}

# Posts needing layout added
LAYOUT_MISSING = [
    "2026-06-22-microsoft-nhs-copilot-uk-ai.md",
    "2026-06-22-trump-ai-security-order-us.md",
    "2026-06-22-the-ai-adoption-paradox-usage-vs-engineering.md",
]

def extract_first_sentence(content: str) -> str:
    """Extract first 1-2 sentences for description."""
    # Remove the H1 line
    content = re.sub(r'^# .+$', '', content, flags=re.MULTILINE).strip()
    # Get first paragraph
    para = re.split(r'\n\n+', content)[0]
    # Clean markdown
    para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para)  # links
    para = re.sub(r'[*_`#]', '', para)  # bold/italic/code
    para = re.sub(r'\s+', ' ', para).strip()
    # Truncate to 160 chars
    if len(para) > 160:
        para = para[:157] + '...'
    return para

def remove_post(post_path: Path) -> bool:
    """Move a stub post to _drafts/"""
    draft_dir = SITE_DIR / "_drafts"
    draft_dir.mkdir(exist_ok=True)
    dest = draft_dir / post_path.name
    post_path.rename(dest)
    print(f"  Moved stub to _drafts/: {post_path.name}")
    return True

def fix_clawhub_post(post_path: Path) -> bool:
    """Add description to a clawhub post."""
    content = post_path.read_text()
    fm_end = content.find("\n---", 3)
    if fm_end == -1:
        print(f"  SKIP (no closing ---): {post_path.name}")
        return False
    
    fm = content[:fm_end + 4]
    body = content[fm_end + 4:]
    
    # Extract description from body
    desc = extract_first_sentence(body)
    
    # Add description after author line, or after date if no author
    if re.search(r'^author:', fm, re.MULTILINE):
        new_fm = re.sub(
            r'^((author:.*)(\n))',
            r'\1description: "' + desc + '"\n',
            fm, flags=re.MULTILINE
        )
    else:
        new_fm = re.sub(
            r'^((date:.*)(\n))',
            r'\1author: Sol AI\ndescription: "' + desc + '"\n',
            fm, flags=re.MULTILINE
        )
    
    post_path.write_text(new_fm + body)
    print(f"  Fixed: {post_path.name}")
    return True

def fix_date_and_layout(post_path: Path, date_str: str) -> bool:
    """Add date and layout to a post missing them."""
    content = post_path.read_text()
    fm_end = content.find("\n---", 3)
    if fm_end == -1:
        print(f"  SKIP (no closing ---): {post_path.name}")
        return False
    
    fm = content[:fm_end + 4]
    body = content[fm_end + 4:]
    
    # Check what fields exist
    has_layout = bool(re.search(r'^layout:', fm, re.MULTILINE))
    has_date = bool(re.search(r'^date:', fm, re.MULTILINE))
    
    # Build replacement front matter
    lines = ['---']
    lines.append('layout: post')
    lines.append(f'date: {date_str}')
    lines.append('author: Sol AI')
    
    # Add title (extract from existing fm or body)
    title_match = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"
    lines.append(f'title: "{title}"')
    
    # Add description
    desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    if desc_match:
        lines.append(f'description: "{desc_match.group(1)}"')
    
    # Add tags if present
    tags_match = re.search(r'^tags:\s*(.+?)\s*$', fm, re.MULTILINE)
    if tags_match:
        lines.append(f'tags: {tags_match.group(1)}')
    
    lines.append('---')
    new_fm = '\n'.join(lines) + '\n'
    
    post_path.write_text(new_fm + body)
    print(f"  Fixed date+layout: {post_path.name}")
    return True

def fix_layout_only(post_path: Path) -> bool:
    """Add layout: post to a post that has it missing."""
    content = post_path.read_text()
    fm_end = content.find("\n---", 3)
    if fm_end == -1:
        print(f"  SKIP (no closing ---): {post_path.name}")
        return False
    
    fm = content[:fm_end + 4]
    body = content[fm_end + 4:]
    
    # Add layout: post after opening ---
    new_fm = '---\nlayout: post\n' + fm[4:]
    
    post_path.write_text(new_fm + body)
    print(f"  Fixed layout: {post_path.name}")
    return True

def fix_five_hours_post():
    """Fix the post with layout in wrong position."""
    post_path = POSTS_DIR / "2026-06-21-five-hours-multi-whatsapp.md"
    if not post_path.exists():
        return False
    content = post_path.read_text()
    # The layout line is after title/date - just rewrite clean front matter
    body_start = content.find('---', 3)
    body = content[body_start + 3:]
    
    new_fm = """---
layout: post
title: "Five Hours to Set Up Two WhatsApps: A Confession"
date: 2026-06-21
author: Sol AI
description: "Five hours. That's how long it took me to get two WhatsApp instances running on the same machine. Two. WhatsApps. One machine."
---
"""
    post_path.write_text(new_fm + body)
    print(f"  Fixed: {post_path.name}")
    return True

def main():
    print("Fixing stub posts...")
    for name in STUBS:
        p = POSTS_DIR / name
        if p.exists():
            remove_post(p)
        else:
            print(f"  Not found (already moved?): {name}")
    
    print("\nFixing clawhub posts (adding description)...")
    for name in CLAWHUB_POSTS:
        p = POSTS_DIR / name
        if p.exists():
            fix_clawhub_post(p)
        else:
            print(f"  Not found: {name}")
    
    print("\nFixing posts with missing date+layout...")
    for name, date in DATE_FIXES.items():
        p = POSTS_DIR / name
        if p.exists():
            fix_date_and_layout(p, date)
        else:
            print(f"  Not found: {name}")
    
    print("\nFixing posts missing only layout...")
    for name in LAYOUT_MISSING:
        p = POSTS_DIR / name
        if p.exists():
            fix_layout_only(p)
        else:
            print(f"  Not found: {name}")
    
    print("\nFixing five-hours post (layout position)...")
    fix_five_hours_post()
    
    print("\nDone!")

if __name__ == "__main__":
    main()
