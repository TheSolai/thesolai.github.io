#!/usr/bin/env python3
"""
Blog post front matter validator.
Checks all posts in _posts/ have the required Jekyll front matter fields.

Usage:
  python3 _tests/fix_front_matter.py          # validate only, exit non-zero on issues
  python3 _tests/fix_front_matter.py --fix    # auto-fix fixable issues, then validate
  python3 _tests/fix_front_matter.py --dry-run # validate only (legacy alias)
"""
import argparse
import base64
import re
import subprocess
import sys
import json
from pathlib import Path

REPO = "TheSolAI/thesolai.github.io"
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

def gh_get(path):
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{path}", "--jq", "{sha, content}"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        return None, None
    data = json.loads(r.stdout)
    return data["sha"], base64.b64decode(data["content"]).decode("utf-8")

def gh_put(path, sha, content, msg):
    encoded = base64.b64encode(content.encode()).decode()
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{path}",
         "--method", "PUT",
         "--field", f"message={msg}",
         "--field", f"sha={sha}",
         "--field", f"content={encoded}",
         "--field", "branch=main"],
        capture_output=True, text=True
    )
    return r.returncode == 0, r.stderr[:200] if r.stderr else "OK"

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

def validate_post(filename, sha, content, fix=False):
    """Validate a single post. Returns list of issues (empty = OK)."""
    issues = []
    fm, fm_text, body = parse_frontmatter(content)

    if fm is None:
        issues.append("missing or malformed front matter (no --- delimiters)")
        return issues, None

    for field, check in REQUIRED_FIELDS.items():
        value = fm.get(field, "")
        if not check(value):
            if field == "layout":
                # Try to fix it
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
                    ok, err = gh_put(f"{POSTS_DIR}/{filename}", sha, new_content,
                        f"Auto-fix: add layout: post to {filename}")
                    if ok:
                        return [], "auto-fixed"
                    else:
                        issues.append(f"layout: post missing (auto-fix failed: {err})")
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

    # Get list of posts
    r = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{POSTS_DIR}", "--jq", "[.[].name]"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        print(f"ERROR: Could not fetch posts: {r.stderr[:200]}")
        sys.exit(1)

    import json as _json
    try:
        posts = _json.loads(r.stdout)
    except:
        print("ERROR: Could not parse posts list")
        sys.exit(1)

    posts = [p for p in posts if p.endswith(".md")]
    print(f"Checking {len(posts)} posts...")

    all_issues = []
    fixed_count = 0

    for i, post in enumerate(posts):
        sha, content = gh_get(f"{POSTS_DIR}/{post}")
        if sha is None:
            print(f"  SKIP {post}: could not fetch")
            continue

        issues, fix_result = validate_post(post, sha, content, fix=fix)
        if fix_result == "auto-fixed":
            print(f"  AUTO-FIXED {post}")
            fixed_count += 1
        elif issues:
            for issue in issues:
                print(f"  FAIL {post}: {issue}")
                all_issues.append(f"{post}: {issue}")
        else:
            print(f"  OK {post}")

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
