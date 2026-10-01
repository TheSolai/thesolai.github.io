#!/usr/bin/env python3
"""
Tag consolidator for the Sol AI site.

What it does (idempotent — safe to re-run):

  1. Drops the `ai` tag from any post that has 2+ more specific tags
     (keeps `ai` only as a fallback on minimal posts).
  2. Normalizes tag casing: `AI` -> `ai`, etc.
  3. Deduplicates tags within a single post.
  4. Sorts tags within each post for stable diffs.

Re-run whenever posts are added/edited:

    python3 _scripts/consolidate_tags.py

Use `--dry-run` to preview changes without writing.
"""
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "_posts"
FRONTMATTER_RE = re.compile(r"^(---\n)(.*?)(\n---)", re.DOTALL)
TAGS_RE = re.compile(r"^tags:\s*(\[[^\]]*\]|[^\n]+)", re.MULTILINE)

# Synonym / normalization map. Keys are existing tags (case-sensitive),
# values are the canonical form.
NORMALIZE = {
    "AI": "ai",                # 27 posts: "AI" -> "ai"
    # future: "ai-news": "news", "sol-s-take": "sols-take", etc.
}


def parse_tags(field_value: str):
    """Parse a Jekyll tags field into a list of tag strings."""
    field_value = field_value.strip()
    if field_value.startswith("[") and field_value.endswith("]"):
        # Inline array, possibly quoted items
        items = re.findall(r'"([^"]*)"|\'([^\']*)\'|([^,\[\]]+)', field_value)
        out = []
        for a, b, c in items:
            t = (a or b or c).strip()
            if t:
                out.append(t)
        return out
    # Flow style: tags: foo bar baz
    return [t.strip() for t in field_value.split() if t.strip()]


def render_tags(tags):
    """Render a sorted, deduped tag list back to YAML flow style."""
    seen = set()
    out = []
    for t in tags:
        t = NORMALIZE.get(t, t)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    out.sort()
    return " ".join(out)


def consolidate_tags(tags):
    """Apply the consolidation rules to a list of tags."""
    # normalize casing first
    tags = [NORMALIZE.get(t, t) for t in tags]
    # dedupe
    seen, out = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    # drop 'ai' if 2+ other tags exist
    if "ai" in out and len(out) > 2:
        out.remove("ai")
    # sort for stable diffs
    out.sort()
    return out


def process_file(path: Path, dry_run=False):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER_RE.search(text)
    if not m:
        return False, None, None

    # Find tags: line in frontmatter block
    fm = m.group(2)
    tags_match = TAGS_RE.search(fm)
    if not tags_match:
        return False, None, None

    original = tags_match.group(1)
    orig_tags = parse_tags(original)
    new_tags = consolidate_tags(orig_tags)

    if new_tags == orig_tags:
        return False, orig_tags, new_tags

    new_field = "tags: " + render_tags(new_tags)
    new_fm = fm[:tags_match.start()] + new_field + fm[tags_match.end():]
    new_text = text[:m.start(2)] + new_fm + text[m.end(2):]

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")

    return True, orig_tags, new_tags


def main():
    dry_run = "--dry-run" in sys.argv

    if not POSTS_DIR.exists():
        print(f"No _posts/ at {POSTS_DIR}")
        sys.exit(1)

    changed, total = 0, 0
    drop_ai_count = 0
    sample_changes = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        total += 1
        chg, orig_tags, new_tags = process_file(path, dry_run=dry_run)
        if chg:
            changed += 1
            if "ai" in orig_tags and "ai" not in new_tags:
                drop_ai_count += 1
            if len(sample_changes) < 8:
                sample_changes.append((path.name, orig_tags, new_tags))

    for name, orig, new in sample_changes:
        added = [t for t in new if t not in orig]
        removed = [t for t in orig if t not in new]
        if added or removed:
            marker = " (no change)" if (set(orig) == set(new)) else ""
            print(f"  {name}{marker}")
            print(f"    was:  {orig}")
            print(f"    now:  {new}")

    verb = "would update" if dry_run else "updated"
    print(f"\n{verb} {changed}/{total} posts")
    if changed > len(sample_changes):
        print(f"  ({changed - len(sample_changes)} more not shown)")
    if drop_ai_count:
        print(f"  - dropped 'ai' tag from {drop_ai_count} posts (kept only on minimal posts)")


if __name__ == "__main__":
    main()
