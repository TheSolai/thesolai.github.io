#!/usr/bin/env python3
"""
Blog post front matter validator.
Checks all posts in _posts/ have the required Jekyll front matter fields.

Reads posts from the LOCAL filesystem (the repo is checked out in CI as
well as on the developer's machine). Does NOT call the GitHub API — the
previous version did, which hung indefinitely in CI when `gh` wasn't
installed in the runner.

Usage:
  python3 _tests/fix_front_matter.py          # validate only, exit non-zero on issues
  python3 _tests/fix_front_matter.py --fix    # auto-fix fixable issues, then validate
  python3 _tests/fix_front_matter.py --dry-run # validate only (legacy alias)
"""
import argparse
import re
import sys
from pathlib import Path

POSTS_DIR = "_posts"

# Required fields and what "correct" looks like for each
REQUIRED_FIELDS = {
    "title":    lambda v: bool(v.strip()),
    "date":     lambda v: bool(re.match(r"^\d{4}-\d\d-\d\d", v.strip())),
    "layout":   lambda v: v.strip() == "post",
    "description": lambda v: len(v.strip()) > 0,
}

# Fields that can be auto-fixed
AUTO_FIXABLE = {"layout"}


def list_posts() -> list[str]:
    """Return markdown filenames in _posts/. Local FS read, no API."""
    p = Path(POSTS_DIR)
    if not p.exists():
        return []
    return sorted(child.name for child in p.glob("*.md"))


def read_post(filename: str) -> str:
    """Read a post from the local checkout. Returns "" on missing."""
    p = Path(POSTS_DIR) / filename
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")

def parse_frontmatter(content):
    """Return (fm_dict, fm_text, body) or (None, None, None) if malformed."""
    if not content.startswith("---"):
        return None, None, None
    fm_end = content.find("\n---", 3)
    if fm_end == -1:
        return None, None, None
    fm_text = content[3:fm_end]
    body = content[fm_end + 4:]
    fm = {}
    for line in fm_text.split("\n"):
        kv = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if kv:
            fm[kv[1]] = kv[2].strip()
    return fm, fm_text, body

def extract_date_from_filename(filename):
    m = re.match(r"^(20\d\d-\d\d-\d\d)-", filename)
    return m.group(1) if m else None

def write_post(filename: str, content: str) -> bool:
    """Write a post back to disk. Returns True on success."""
    try:
        (Path(POSTS_DIR) / filename).write_text(content, encoding="utf-8")
        return True
    except OSError as e:
        return False


def validate_post(filename, content, fix=False):
    """Validate a single post. Returns (issues, fix_result) where fix_result
    is "auto-fixed" if --fix applied a fix, else None."""
    issues = []
    fm, fm_text, body = parse_frontmatter(content)

    if fm is None:
        issues.append("missing or malformed front matter (no --- delimiters)")
        return issues, None

    for field, check in REQUIRED_FIELDS.items():
        value = fm.get(field, "")
        if not check(value):
            if field == "layout":
                # Try to fix it (developer tool — only with --fix locally)
                if fix and "layout" in AUTO_FIXABLE:
                    new_fm_lines = ["---"]
                    for line in fm_text.split("\n"):
                        stripped = line.strip()
                        if stripped.startswith("layout:"):
                            continue  # skip old layout
                        new_fm_lines.append(line)
                    # Insert layout: post after opening ---
                    new_fm_lines.insert(1, "layout: post")
                    new_fm_lines.append("---")
                    new_content = "\n".join(new_fm_lines) + "\n" + body
                    if write_post(filename, new_content):
                        return [], "auto-fixed"
                    issues.append("layout: post missing (auto-fix failed: write error)")
                else:
                    issues.append("layout: post missing")
            elif field == "date":
                issues.append("date missing or malformed (should be YYYY-MM-DD)")
            else:
                issues.append(f"{field} missing or empty")

    return issues, None

def main():
    parser = argparse.ArgumentParser(description="Validate blog post front matter")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix fixable issues (missing layout: post)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate only (legacy alias for no-op fix)")
    args = parser.parse_args()
    fix = args.fix and not args.dry_run

    posts = list_posts()
    print(f"Checking {len(posts)} posts...")

    all_issues = []
    fixed_count = 0

    for i, post in enumerate(posts):
        content = read_post(post)
        if not content:
            print(f"  SKIP {post}: could not read")
            continue

        issues, fix_result = validate_post(post, content, fix=fix)
        if fix_result == "auto-fixed":
            print(f"  AUTO-FIXED {post}")
            fixed_count += 1
        elif issues:
            for issue in issues:
                print(f"  FAIL {post}: {issue}")
                all_issues.append(f"{post}: {issue}")
        else:
            # quiet on success — only print failures
            pass

    print()
    if fixed_count:
        print(f"Auto-fixed {fixed_count} posts.")
    if all_issues:
        print(f"FAILED: {len(all_issues)} issue(s) found.")
        print("\nIssues:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print(f"All {len(posts)} posts OK.")
        sys.exit(0)

if __name__ == "__main__":
    main()
