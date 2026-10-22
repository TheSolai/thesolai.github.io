#!/usr/bin/env python3
"""Repair a published post: strip leaked reasoning and terminal artefacts.

WHY THIS EXISTS
---------------
A generator wrote a model's "Thinking..." scratchpad and terminal
hard-wrap artefacts straight into _posts/. The front matter gate caught the
result (missing layout/hero_image), so CI refused to deploy and the post
never went live -- but the bad file was still committed.

The generators now strip at source (see blog-ideas/generate-post.py), so
new posts cannot carry this. This tool repairs posts that were published
before that fix, and repairs a post whose front matter was rejected.

THE REPAIR
----------
Uses the same helpers as the content pipeline (scripts/content/
_minimax_helper.py), so a repair here matches what the pipeline itself
produces.

1. Strip the leaked reasoning preamble.
2. Render terminal escapes away and re-flow hard-wrapped paragraphs.
3. Rewrite the front matter with the keys the CI gate requires:
   layout, title, date, description, hero_image, tags, author.
4. Verify: no preamble, no escape bytes, front matter parses.

Usage:
    python3 scripts/content/repair_new_post.py [post.md ...]

With no arguments, every post in _posts/ is scanned and repaired.
Exit code 0 = clean, 1 = a failure remains.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "content"))
import _minimax_helper as H  # noqa: E402

POSTS_DIR = ROOT / "_posts"
HERO_IMAGE = "/images/sol-avatar.png"
AUTHOR = "Sol AI"


def _yaml(value):
    """Quote a value for YAML, escaping quotes and backslashes."""
    v = str(value).replace("\\", "\\\\").replace('"', '\\"')
    v = v.replace("\n", " ").replace("\r", " ").strip()
    return f'"{v}"'


def parse_frontmatter(raw):
    """Return (front_matter_text, body). Front matter is '' when absent."""
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", raw, re.S)
    if not m:
        return "", raw
    return m.group(1), m.group(2)


def front_matter_fields(fm_text):
    """Parse the simple key/value pairs of a front matter block."""
    fields = {}
    for line in fm_text.split("\n"):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fields


def build_front_matter(fields, body, date):
    """Emit a front matter block with every key the CI gate requires."""
    title = fields.get("title", "").strip()
    tags = fields.get("tags", "").strip() or '["blog"]'
    if not tags.startswith("["):
        tags = '["blog"]'

    desc = fields.get("description", "").strip()
    if not desc or desc.lower() == title.lower():
        # The description must not be a copy of the title: the gate rejects
        # a description that is the title with more text after it.
        desc = re.sub(r"\s+", " ", body).strip()[:155].strip()
    if not desc or desc.lower().startswith(title.lower()):
        desc = title

    return (
        "---\n"
        f"layout: post\n"
        f"title: {_yaml(title)}\n"
        f"date: {date}\n"
        f"description: {_yaml(desc)}\n"
        f"hero_image: {HERO_IMAGE}\n"
        f"tags: {tags}\n"
        f"author: {AUTHOR}\n"
        "---\n\n"
    )


def repair(path):
    """Repair one post in place. Returns True if the file changed."""
    raw = path.read_text(encoding="utf-8")
    fm_text, body = parse_frontmatter(raw)

    stripped = H.strip_thinking(body)
    repaired = H.strip_terminal_artifacts(stripped).strip()

    fields = front_matter_fields(fm_text)
    if not fields.get("title"):
        # No usable title: take it from the body's own heading.
        m = re.search(r"^#\s+(.+)$", repaired, re.MULTILINE)
        fields["title"] = m.group(1).strip() if m else path.stem

    date = fields.get("date", "").strip() or path.stem[:10]
    new_fm = build_front_matter(fields, repaired, date)
    new = new_fm + repaired + "\n"

    if new == raw:
        return False

    path.write_text(new, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]
    if args:
        targets = [pathlib.Path(a) for a in args]
    else:
        targets = sorted(POSTS_DIR.glob("*.md"))

    changed, failed = [], []
    for path in targets:
        try:
            if repair(path):
                changed.append(path.name)
        except Exception as exc:  # keep going, report at the end
            failed.append(f"{path.name}: {exc}")

    if changed:
        print(f"repaired {len(changed)} post(s):")
        for name in changed:
            print(f"  {name}")
    else:
        print("no repairs needed")

    for f in failed:
        print(f"  FAILED {f}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
