#!/usr/bin/env python3
"""Fast iteration harness for a candidate sprite grid.

Takes a name plus a list of rows, and reports everything the authoritative
verifier cares about, plus a couple of things it does not check but the art
direction demands (4-connected silhouette, so pxl's 1px K outline will not
split the shape).

Usage: python3 try_grid.py <name> <rows-file>
  where <rows-file> holds one 16-wide row per line.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path.home() / "Projects/GameStewKit"
sys.path.insert(0, str(ROOT / "ai"))

from verify_sprites import HEX_TO_KEY, PALETTE_HEX, luminance  # noqa: E402

MIN_COLOURS, MAX_COLOURS = 3, 7
ALLOWED = {(16, 16), (24, 24)}


def lum(key: str) -> float:
    return luminance(PALETTE_HEX[key])


def report(name: str, rows: list[str]) -> None:
    w = len(rows[0]) if rows else 0
    h = len(rows)
    problems: list[str] = []

    if (w, h) not in ALLOWED:
        problems.append(f"canvas {w}x{h} not allowed")
    for y, r in enumerate(rows):
        if len(r) != w:
            problems.append(f"row {y} is {len(r)} wide, expected {w}")

    colours: set[str] = set()
    for r in rows:
        for ch in r:
            if ch != ".":
                if ch not in PALETTE_HEX:
                    problems.append(f"illegal key {ch!r}")
                elif ch == "I":
                    problems.append("palette key 'I' is forbidden")
                else:
                    colours.add(ch)

    if not (MIN_COLOURS <= len(colours) <= MAX_COLOURS):
        problems.append(f"{len(colours)} colours, budget is {MIN_COLOURS}-{MAX_COLOURS}")

    # Connectivity: 8-connected for the verifier, 4-connected for the outline.
    opaque = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."}
    if opaque:
        start = min(opaque, key=lambda p: (p[1], p[0]))
        seen = {start}
        stack = [start]
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in opaque and n not in seen:
                    seen.add(n)
                    stack.append(n)
        if len(seen) != len(opaque):
            problems.append(f"{len(opaque) - len(seen)} detached island(s)")

        seen4 = {start}
        stack = [start]
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in opaque and n not in seen4:
                    seen4.add(n)
                    stack.append(n)
        if len(seen4) != len(opaque):
            problems.append(f"{len(opaque) - len(seen4)} px only diagonally linked "
                            f"(outline may split)")

    # Lighting, measured the way the verifier measures it: on the EXPORTED
    # sprite, which is the canvas plus a 1px K outline. Approximate that by
    # adding the outline ring.
    ex = w + 2
    grid = [["."] * ex for _ in range(h + 2)]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                grid[y + 1][x + 1] = c
    for y in range(h + 2):
        for x in range(ex):
            if grid[y][x] == ".":
                if any(0 <= ny < h + 2 and 0 <= nx < ex and grid[ny][nx] != "."
                       for ny in (y - 1, y, y + 1) for nx in (x - 1, x, x + 1)):
                    grid[y][x] = "K"

    mid_x, mid_y = ex / 2.0, (h + 2) / 2.0
    tl: list[float] = []
    br: list[float] = []
    for y in range(h + 2):
        for x in range(ex):
            c = grid[y][x]
            if c == ".":
                continue
            if x < mid_x and y < mid_y:
                tl.append(lum(c))
            elif x >= mid_x and y >= mid_y:
                br.append(lum(c))

    lit = "OK"
    if tl and br:
        tm, bm = sum(tl) / len(tl), sum(br) / len(br)
        if tm <= bm:
            lit = f"FAIL tl={tm:.3f} br={bm:.3f}"
        else:
            lit = f"OK tl={tm:.3f} br={bm:.3f}"

    print(f"--- {name}  {w}x{h}  colours={len(colours)} ({''.join(sorted(colours))})")
    print(f"    lighting: {lit}")
    for p in problems:
        print(f"    PROBLEM: {p}")
    if not problems:
        print("    no mechanical problems")
    print()
    for y, r in enumerate(rows):
        print(f"  {r}")


if __name__ == "__main__":
    nm = sys.argv[1]
    rows = [ln.rstrip("\n") for ln in open(sys.argv[2]) if ln.strip() != ""]
    report(nm, rows)
