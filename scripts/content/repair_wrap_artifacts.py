#!/usr/bin/env python3
"""Repair terminal hard-wrap artifacts in Jekyll posts.

THE ARTIFACT
-------------
These posts were captured from a terminal that hard-wrapped output at ~80
columns. When a word straddled the wrap point, the terminal emitted:

    <text ending in a partial word> ESC[<N>D ESC[K
    <the complete word> <rest of the line>

`ESC[<N>D` moves the cursor back N columns and `ESC[K` erases from the
cursor to end of line -- so on a real terminal the partial word vanishes and
the sentence reads correctly. A browser does not execute these escapes, so
the published page shows the word TWICE:

    "…the core logic layer correct"
    "corrected an edge case that had slipped…"

Measured across all 13 affected posts: 725 fragments, and in every single
one the next line's first word starts with exactly the erased token. The
repair is therefore exact, not heuristic.

THE REPAIR
----------
1. Simulate the terminal: for each line, apply the cursor-back/erase
   semantics to recover the text a terminal would have displayed.
2. Re-flow each paragraph: the wrap split sentences at arbitrary points,
   so join the rendered lines back together with a single space.

Markdown structure is preserved: headings, list items, blockquotes, tables
and fenced code blocks keep their own lines and are never joined.

Dry-run by default; pass --apply to rewrite files.
"""
import argparse
import pathlib
import re
import sys

# CSI sequences we care about. Any other ESC sequence is left alone.
ESC_CURSOR_BACK = re.compile(r"\x1b\[(\d*)D")
ESC_ERASE_EOL = re.compile(r"\x1b\[K")
ANY_CSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# A line that starts a new markdown block.
BLOCK_START = re.compile(
    r"^(?:\s{0,3}(?:#{1,6}\s|>|```|~~~|-{3,}\s*$|\|)|\s*(?:[-*+]|\d+[.)])\s)"
)
FENCE = re.compile(r"^\s*(?:```|~~~)")


def render_line(raw: str) -> str:
    """Return the text a terminal would display for this raw line.

    Simulates cursor-back (ESC[N D) and erase-to-end-of-line (ESC[K).
    """
    buf: list[str] = []
    cursor = 0
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\x1b":
            m = ESC_CURSOR_BACK.match(raw, i)
            if m:
                n = int(m.group(1) or 1)
                cursor = max(0, cursor - n)
                i = m.end()
                continue
            m = ESC_ERASE_EOL.match(raw, i)
            if m:
                del buf[cursor:]
                i = m.end()
                continue
            m = ANY_CSI.match(raw, i)
            if m:
                # Unknown CSI: drop it (it carries no visible text).
                i = m.end()
                continue
            i += 1
            continue
        if cursor < len(buf):
            buf[cursor] = ch
            cursor += 1
        else:
            buf.append(ch)
            cursor += 1
        i += 1
    return "".join(buf)


def is_blank(line: str) -> bool:
    return not line.strip()


def is_fence(line: str) -> bool:
    return bool(FENCE.match(line))


def repair_body(body: str) -> str:
    """Re-flow a rendered body, preserving markdown block structure."""
    raw_lines = body.split("\n")
    lines = [render_line(l) for l in raw_lines]

    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        if is_blank(line):
            out.append("")
            i += 1
            continue

        # Fenced code block: copy verbatim until the closing fence.
        if is_fence(line):
            out.append(line.rstrip())
            i += 1
            while i < n:
                out.append(lines[i].rstrip())
                closing = is_fence(lines[i])
                i += 1
                if closing:
                    break
            continue

        # A block-start line begins its own block; continuation lines that
        # belong to it are joined on.
        if BLOCK_START.match(line):
            block = [line.rstrip()]
            i += 1
            while i < n and not is_blank(lines[i]) and not is_fence(lines[i]) \
                    and not BLOCK_START.match(lines[i]):
                block.append(lines[i].strip())
                i += 1
            out.append(" ".join(x for x in block if x).rstrip())
            continue

        # Plain paragraph: join every following non-blank, non-block line.
        para = [line.strip()]
        i += 1
        while i < n and not is_blank(lines[i]) and not is_fence(lines[i]) \
                and not BLOCK_START.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(" ".join(x for x in para if x).rstrip())

    # Collapse runs of blank lines to a single blank line.
    collapsed: list[str] = []
    for l in out:
        if not l.strip() and collapsed and not collapsed[-1].strip():
            continue
        collapsed.append(l)
    return "\n".join(collapsed)


def split_front_matter(text: str):
    """Return (front_matter_str, body_str) or (None, None)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, None
    end = next((i for i, l in enumerate(lines) if i > 0 and l.strip() == "---"), None)
    if end is None:
        return None, None
    return "\n".join(lines[: end + 1]), "\n".join(lines[end + 1:])


def process(path: pathlib.Path):
    text = path.read_text(errors="replace")
    fm, body = split_front_matter(text)
    if fm is None:
        return None, "no front matter"

    if not ANY_CSI.search(body):
        return None, "no escape sequences"

    fixed = repair_body(body)

    # Safety: the repaired body must not be empty and must keep the prose.
    if len(fixed.strip()) < 200:
        return None, "too short after repair"
    if fixed.count("```") != body.count("```"):
        return None, "code fence count changed"
    for h in re.findall(r"^#{1,6} .+$", body, re.M):
        if h not in fixed:
            return None, f"heading lost: {h[:40]}"

    new_text = fm + "\n" + fixed
    if not new_text.endswith("\n"):
        new_text += "\n"

    removed = len(re.findall(r"\x1b\[[0-9;?]*[A-Za-z]", body))
    return new_text, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="_posts")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    files = sorted(root.glob("*.md"))
    fixed = skipped = 0
    for p in files:
        try:
            res = process(p)
        except Exception as e:  # never abort the whole run
            print(f"ERROR {p.name}: {e}")
            skipped += 1
            continue
        if res is None:
            continue
        new_text, reason = res
        if isinstance(reason, str):
            print(f"SKIP ({reason}): {p.name}")
            skipped += 1
            continue
        fixed += 1
        verb = "FIXED" if args.apply else "WOULD FIX"
        print(f"{verb}: {p.name} (removed {reason} escape sequences)")
        if args.apply:
            p.write_text(new_text)
    print(f"\n{fixed} {'fixed' if args.apply else 'would be fixed'}, {skipped} skipped, {len(files)} scanned")


if __name__ == "__main__":
    main()
