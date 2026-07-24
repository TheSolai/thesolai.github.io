#!/usr/bin/env python3
"""
Skill Resolver — v1.0.0
Matches task keywords to skill bodies for mandatory injection.

Usage:
  python3 resolver.py <message> [--skills-dir DIR] [--config CONFIG] [--json] [--debug]

Output:
  Matched skill bodies (or empty if none found).
  Exit code 0 always. Prints to stdout.
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_SKILLS_DIR = os.path.expanduser("~/.openclaw/skills")


def load_config(config_path):
    """Load config JSON from the given path."""
    config_path = os.path.expanduser(config_path)
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    with open(config_path) as f:
        return json.load(f)


def normalize(s):
    """Normalize string: lowercase, replace non-alphanumeric with spaces."""
    return re.sub(r'[^a-z0-9 ]', ' ', s.lower())


def message_matches(message, keywords):
    """Check if message matches any of the given keywords (substring or word boundary)."""
    norm = normalize(message)
    for kw in keywords:
        kw_lower = kw.lower()
        if len(kw_lower) <= 3:
            # Short keywords: substring match
            if kw_lower in norm:
                return True
        else:
            # Longer keywords: word-boundary match
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, norm):
                return True
    return False


def load_skill_body(slug, skills_dir, paths=None):
    """Load skill body from paths list or from skills_dir/slug/SKILL.md fallback."""
    # Try explicit paths first
    if paths:
        for path in paths:
            path = os.path.expanduser(path)
            if os.path.exists(path):
                with open(path) as f:
                    return f.read()

    # Fallback: skills_dir/slug/SKILL.md
    fallback = os.path.join(skills_dir, slug, "SKILL.md")
    if os.path.exists(fallback):
        with open(fallback) as f:
            return f.read()
    return None


def resolve(message, config_path=None, skills_dir=None):
    """Main resolve function: returns list of matched skill dicts."""
    if config_path is None:
        config_path = DEFAULT_CONFIG
    if skills_dir is None:
        skills_dir = DEFAULT_SKILLS_DIR

    config = load_config(config_path)
    results = []

    for skill_key, skill_info in config.get("skills", {}).items():
        keywords = skill_info.get("keywords", [])
        paths = skill_info.get("paths", [])
        slug = skill_info.get("slug", skill_key)

        if not message_matches(message, keywords):
            continue

        body = load_skill_body(slug, skills_dir, paths)
        if body:
            results.append({
                "skill": skill_key,
                "slug": slug,
                "body": body,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Skill Resolver")
    parser.add_argument("message", nargs="?", help="Message to match against keywords")
    parser.add_argument("--skills-dir", default=DEFAULT_SKILLS_DIR,
                        help="Skills directory")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="Config JSON path")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--debug", action="store_true",
                        help="Show matched skills")

    args = parser.parse_args()
    message = args.message

    if not message:
        # Try reading from stdin
        message = sys.stdin.read().strip()

    if not message:
        print("# Skill Resolver — no message provided", file=sys.stderr)
        print("No message provided.", file=sys.stderr)
        sys.exit(0)

    results = resolve(message, config_path=args.config, skills_dir=args.skills_dir)

    if args.json:
        print(json.dumps(results, indent=2))
        sys.exit(0)

    if args.debug:
        print(f"# Skill Resolver — {len(results)} skill(s) matched for: {message[:80]}")
        for r in results:
            print(f"  + {r['skill']} ({r['slug']}) — {len(r['body'])} chars")
        print()
        if not results:
            sys.exit(0)

    if not results:
        sys.exit(0)

    for r in results:
        print("---\n# Skill: " + r["skill"] + " (" + r["slug"] + ")\n")
        print(r["body"])
        print()


if __name__ == "__main__":
    main()
