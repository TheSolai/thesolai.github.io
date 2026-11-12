#!/usr/bin/env python3
"""Render a region of a captured frame as ASCII art, for visual review."""
import sys
sys.path.insert(0, "/Users/amre/.openclaw/workspace")
from check_palette import load, PALETTE

CH = {
    "K": "#", "D": "d", "P": "p", "N": "n", "X": ".", "C": "c", "W": "w",
    "Y": "y", "G": "g", "H": "h", "T": "t", "M": "m", "L": "l", "E": "e",
    "I": "i", "U": "u", "R": "r", "A": "a", "S": "s", "Z": "z",
}


def render(path, x0, y0, x1, y1, step=1):
    w, h, ct, nch, pal, trns, rows = load(path)
    x1 = min(x1, w)
    y1 = min(y1, h)
    for y in range(y0, y1, step):
        line = ""
        for x in range(x0, x1, step):
            px = rows[y][x * nch:(x + 1) * nch]
            if ct == 3:
                idx = px[0]
                alpha = trns[idx] if (trns and idx < len(trns)) else 255
                if alpha == 0:
                    line += " "
                    continue
                rgb = pal[idx]
            else:
                rgb = (px[0], px[1], px[2])
            line += CH.get(PALETTE.get(rgb, "?"), "?")
        print("%4d %s" % (y, line))


if __name__ == "__main__":
    p = sys.argv[1]
    a = [int(v) for v in sys.argv[2:6]]
    st = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    render(p, a[0], a[1], a[2], a[3], st)
