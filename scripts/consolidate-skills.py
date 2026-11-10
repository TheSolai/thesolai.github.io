#!/usr/bin/env python3
"""
consolidate-skills.py — gather every agent skill on this Mac into one folder.

Agent frameworks each keep their own skills directory: OpenClaw, Claude Code,
Cursor, the `.agents` standard, the Workshop, and OpenClaw's own bundled
stock skills. The result is the same idea scattered across nine trees, and
no single tool can see the lot.

This script copies every `SKILL.md` (with its whole skill directory) into one
canonical folder, deduplicating by skill name and recording where each came
from.

Layout produced:

    ~/Skills/
      <skill-name>/            the skill itself (SKILL.md + supporting files)
      .provenance.json         source paths, timestamps, and dedup decisions
      INDEX.md                 human-readable catalogue

Deduplication: when the same skill name appears in several trees, the copy
with the most recently modified SKILL.md wins (the tree most likely to be
actively maintained). Every losing copy is recorded in the provenance file
so nothing is silently lost.

Re-running is safe: it rebuilds the folder from scratch, and it never
deletes anything outside ~/Skills.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
DEST = os.path.join(HOME, "Skills")

# (label, path) pairs, in priority order for reporting. Order does not
# decide the winner -- recency does -- but it makes the INDEX readable.
SOURCES = [
    ("openclaw-workspace", os.path.join(HOME, ".openclaw/workspace/skills")),
    ("openclaw-global", os.path.join(HOME, ".openclaw/skills")),
    ("openclaw-plugin", os.path.join(HOME, ".openclaw/plugin-skills")),
    ("openclaw-agents", os.path.join(HOME, ".openclaw/workspace/.agents/skills")),
    ("openclaw-workshop", os.path.join(HOME, ".openclaw/agents/main/agent/workshop-skills")),
    ("openclaw-bundled", os.path.join(HOME, ".openclaw/tools/node-v24.21.0/lib/node_modules/openclaw/skills")),
    ("openclaw-custodian", os.path.join(HOME, ".openclaw/tools/node-v24.21.0/lib/node_modules/openclaw/custodian-skills")),
    ("agents-standard", os.path.join(HOME, ".agents/skills")),
    ("claude", os.path.join(HOME, ".claude/skills")),
    ("cursor", os.path.join(HOME, ".cursor/skills")),
]


def find_skill_md(root):
    """Return every SKILL.md under root, at any depth, but not nested
    inside another skill directory (avoid double counting)."""
    found = []
    if not os.path.isdir(root):
        return found
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            found.append(os.path.join(dirpath, "SKILL.md"))
            # Do not descend into a skill's own directory: a nested
            # reference copy is not a separate skill.
            dirnames[:] = []
    return found


def sha(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def read_name(skill_md):
    """Skill name: prefer the frontmatter 'name:', else the directory name."""
    try:
        with open(skill_md, encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
    except OSError:
        head = ""
    if head.startswith("---"):
        parts = head.split("---", 2)
        if len(parts) >= 2:
            for line in parts[1].splitlines():
                if line.strip().startswith("name:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return os.path.basename(os.path.dirname(skill_md))


def read_description(skill_md):
    try:
        with open(skill_md, encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
    except OSError:
        return ""
    if head.startswith("---"):
        parts = head.split("---", 2)
        if len(parts) >= 2:
            for line in parts[1].splitlines():
                if line.strip().startswith("description:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def copy_skill(src_md, dest_dir):
    """Copy the skill directory (everything alongside SKILL.md)."""
    src_dir = os.path.dirname(src_md)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "node_modules", "*.pyc"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dest", default=DEST)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    dest = args.dest

    # Discover every skill, keyed by name.
    by_name = {}
    total_found = 0
    for label, root in SOURCES:
        for md in find_skill_md(root):
            if not os.path.isdir(root):
                continue
            total_found += 1
            name = read_name(md)
            if not name:
                name = os.path.basename(os.path.dirname(md))
            by_name.setdefault(name, []).append({
                "name": name,
                "source_label": label,
                "source_root": root,
                "skill_md": md,
                "mtime": os.path.getmtime(md),
                "sha256": sha(md),
                "description": read_description(md),
            })

    # Winner per name: most recently modified SKILL.md.
    winners = {}
    for name, cands in by_name.items():
        cands.sort(key=lambda c: c["mtime"], reverse=True)
        winners[name] = cands[0]

    if args.dry_run:
        print(f"Would copy {len(winners)} unique skills "
              f"(from {total_found} copies) -> {dest}")
        for name in sorted(winners):
            cands = by_name[name]
            dup = "  [DUP x%d]" % len(cands) if len(cands) > 1 else ""
            print(f"  {name:<45} {cands[0]['source_label']}{dup}")
        return

    # Rebuild the destination.
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    provenance = {}
    for name in sorted(winners):
        win = winners[name]
        dest_dir = os.path.join(dest, name)
        copy_skill(win["skill_md"], dest_dir)
        provenance[name] = {
            "chosen_from": win["source_label"],
            "chosen_path": win["skill_md"],
            "mtime": datetime.fromtimestamp(win["mtime"], timezone.utc).isoformat(),
            "sha256": win["sha256"],
            "description": win["description"],
            "also_found_at": [
                {"source_label": c["source_label"], "path": c["skill_md"],
                 "mtime": datetime.fromtimestamp(c["mtime"], timezone.utc).isoformat(),
                 "sha256": c["sha256"]}
                for c in by_name[name][1:]
            ],
        }

    with open(os.path.join(dest, ".provenance.json"), "w", encoding="utf-8") as f:
        json.dump({
            "generated": datetime.now(timezone.utc).isoformat(),
            "sources": {label: root for label, root in SOURCES},
            "total_copies_found": total_found,
            "unique_skills": len(winners),
            "skills": provenance,
        }, f, indent=2, ensure_ascii=False)

    # Human catalogue.
    dupes = sum(1 for n in provenance.values() if n["also_found_at"])
    lines = [
        "# Skill Index",
        "",
        f"**{len(winners)} unique skills**, consolidated from {total_found} copies",
        f"across {len([s for s in SOURCES if os.path.isdir(s[1])])} source trees.",
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        f"{dupes} skills existed in more than one place; the most recently",
        "modified copy won. Every loser is recorded in `.provenance.json`.",
        "",
        "| Skill | From | Also in | Description |",
        "|---|---|---|---|",
    ]
    for name in sorted(provenance):
        e = provenance[name]
        also = ", ".join(sorted({a["source_label"] for a in e["also_found_at"]})) or "—"
        desc = (e["description"] or "").replace("|", "\\|")
        if len(desc) > 90:
            desc = desc[:87] + "..."
        lines.append(f"| `{name}` | {e['chosen_from']} | {also} | {desc} |")
    lines.append("")
    with open(os.path.join(dest, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Consolidated {total_found} copies -> {len(winners)} unique skills in {dest}")
    print(f"  duplicates resolved: {dupes}")
    print(f"  catalogue: {os.path.join(dest, 'INDEX.md')}")
    print(f"  provenance: {os.path.join(dest, '.provenance.json')}")


if __name__ == "__main__":
    main()
