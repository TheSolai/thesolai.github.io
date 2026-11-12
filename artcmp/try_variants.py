#!/usr/bin/env python3
"""Try several candidate grids for a sprite, side by side.

Rows are written as (text) and padded/truncated to the canvas width by the
script itself, so a miscounted row is impossible to slip through.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path.home() / "Projects/GameStewKit"
sys.path.insert(0, str(ROOT / "ai"))

from verify_sprites import HEX_TO_KEY, PALETTE_HEX, luminance  # noqa: E402

MIN_COLOURS, MAX_COLOURS = 3, 7


def lum(key: str) -> float:
    return luminance(PALETTE_HEX[key])


def analyse(rows: list[str], w: int = 16) -> tuple[list[str], str]:
    problems: list[str] = []
    rows = [r.ljust(w, ".")[:w] for r in rows]
    h = len(rows)

    colours = {c for r in rows for c in r if c != "."}
    bad = {c for c in colours if c not in PALETTE_HEX or c == "I"}
    if bad:
        problems.append(f"illegal key(s) {sorted(bad)}")
    if not (MIN_COLOURS <= len(colours) <= MAX_COLOURS):
        problems.append(f"{len(colours)} colours, budget {MIN_COLOURS}-{MAX_COLOURS}")

    opaque = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != "."}
    if opaque:
        start = min(opaque, key=lambda p: (p[1], p[0]))
        for label, deltas in (
            ("8-connected", ((1, 0), (-1, 0), (0, 1), (0, -1),
                             (1, 1), (1, -1), (-1, 1), (-1, -1))),
            ("4-connected", ((1, 0), (-1, 0), (0, 1), (0, -1))),
        ):
            seen = {start}
            stack = [start]
            while stack:
                x, y = stack.pop()
                for dx, dy in deltas:
                    n = (x + dx, y + dy)
                    if n in opaque and n not in seen:
                        seen.add(n)
                        stack.append(n)
            if len(seen) != len(opaque):
                problems.append(
                    f"{len(opaque) - len(seen)} px not {label} to the rest")

    # exported sprite = canvas + 1px K outline
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
    if tl and br:
        tm, bm = sum(tl) / len(tl), sum(br) / len(br)
        lit = f"tl={tm:.3f} br={bm:.3f} {'OK' if tm > bm else 'FAIL'}"
    else:
        lit = "n/a"

    return problems, f"{len(colours)} colours ({''.join(sorted(colours))})  {lit}"


def show(name: str, rows: list[str], w: int = 16) -> None:
    problems, summary = analyse(rows, w)
    print(f"=== {name}: {summary}")
    for p in problems:
        print(f"    PROBLEM: {p}")
    for r in rows:
        print(f"  {r.ljust(w, '.')[:w]}")
    print()


if __name__ == "__main__":
    spec = Path(sys.argv[1])
    ns: dict = {}
    exec(spec.read_text(), ns)  # noqa: S102 - local test harness
    for name, rows in ns["CANDIDATES"]:
        show(name, rows)
