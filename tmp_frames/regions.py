#!/usr/bin/env python3
"""Locate off-palette pixels by region in the bevel probe.

The probe lays out four widgets at known logical coordinates in a 720x1280
canvas, captured into a 540x960 window (scale 0.75). This maps every
off-palette pixel back to the widget that produced it.
"""
import sys
from collections import Counter

sys.path.insert(0, "/Users/amre/.openclaw/workspace/tmp_frames")
from analyze import read_png, hexc, PALETTE

PATH = "/Users/amre/.openclaw/workspace/tmp_frames/probe2.png"
SCALE = 0.75

# name, logical x, y, w, h
REGIONS = [
    ("A plain themed Button", 20, 20, 220, 48),
    ("B custom BevelButton", 20, 90, 220, 48),
    ("C flat Button + icon", 20, 160, 220, 48),
    ("D bevel Card + label", 20, 230, 320, 70),
]

w, h, bpp, px = read_png(PATH)


def at(x, y):
    o = (y * w + x) * bpp
    return tuple(px[o:o + 3])


buckets = {}
outside = []
for y in range(h):
    for x in range(w):
        c = at(x, y)
        if hexc(c) in PALETTE:
            continue
        lx, ly = x / SCALE, y / SCALE
        placed = False
        for name, rx, ry, rw, rh in REGIONS:
            if rx <= lx < rx + rw and ry <= ly < ry + rh:
                buckets.setdefault(name, Counter())[c] += 1
                placed = True
                break
        if not placed:
            outside.append((x, y, c))

print("off-palette pixels by widget:")
for name, _x, _y, _w, _h in REGIONS:
    c = buckets.get(name, Counter())
    total = sum(c.values())
    print("  %-24s %5d px, %3d distinct shades" % (name, total, len(c)))
    for col, n in c.most_common(4):
        print("        %s x%d" % (hexc(col), n))

print("  %-24s %5d px" % ("outside any widget", len(outside)))
oc = Counter(c for _x, _y, c in outside)
for col, n in oc.most_common(8):
    print("        %s x%d" % (hexc(col), n))
if outside:
    xs = [x for x, _y, _c in outside]
    ys = [y for _x, y, _c in outside]
    print("        bbox x %d..%d  y %d..%d (logical x %.0f..%.0f y %.0f..%.0f)"
          % (min(xs), max(xs), min(ys), max(ys),
             min(xs) / SCALE, max(xs) / SCALE, min(ys) / SCALE, max(ys) / SCALE))
