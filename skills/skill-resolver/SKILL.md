---
name: skill-resolver
description: Match a task to the right skill body and inject it automatically. Use when a request mentions a tool or file type (SQLite, PDF, DOCX, XLSX, browser, email, weather, diagrams) and the agent needs the matching skill's instructions before acting.
metadata: {"clawdbot":{"emoji":"🧭","requires":{"bins":["python3"]}}}
---

# Skill Resolver

Turns a plain-language request into the body of the skill that handles it.

`config.json` maps each skill to the keywords that trigger it and the file
paths where that skill's `SKILL.md` lives. The resolver matches keywords
against a message, loads the matching skill bodies, and prints them — ready to
be injected into the agent's context before the task is attempted.

## Usage

```bash
python3 resolver.py "query the sqlite db for open invoices"
```

Other flags:

```bash
python3 resolver.py "extract this PDF" --json      # machine-readable output
python3 resolver.py "check the weather" --debug     # show what matched, and why
python3 resolver.py "render a mermaid diagram" --skills-dir ~/.openclaw/skills
```

With no message argument the resolver reads stdin:

```bash
echo "make a spreadsheet of this data" | python3 resolver.py
```

Exit code is always 0 — an unmatched message is a valid result, not an error.

## How matching works

- Keywords are normalised to lowercase and split on non-alphanumeric
  characters.
- Keywords of 3 characters or fewer match as a substring (`pdf`, `csv`).
- Longer keywords match on word boundaries, so `db` does not fire on
  "database" but `database` does not fire on "databases" either.
- The first skill in `config.json` whose keyword list matches wins for each
  distinct match — several skills can match one message.

## Skill body lookup

For each match, the resolver tries the skill's `paths` from `config.json` in
order (with `~` expanded), then falls back to
`<skills-dir>/<slug>/SKILL.md`. If no body is found the match is skipped
rather than emitted empty.

## Adding a skill to the resolver

Add an entry under `"skills"` in `config.json`:

```json
"weather": {
  "keywords": ["weather", "forecast", "temperature"],
  "slug": "weather",
  "paths": ["~/.openclaw/skills/weather/SKILL.md"]
}
```

- `keywords` — the phrases that should trigger this skill.
- `slug` — the directory name used for the `<skills-dir>/<slug>/SKILL.md`
  fallback.
- `paths` — explicit locations to search first, most specific first.

Then verify it resolves:

```bash
python3 resolver.py "what's the weather" --debug
```

## Files

- `config.json` — keyword and path mappings.
- `resolver.py` — the matcher and loader.
