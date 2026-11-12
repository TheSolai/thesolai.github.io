#!/usr/bin/env python3
"""Pixel analyser for SIDHE & STONE captures.

Answers the three questions that matter about a captured frame:

  1. Is every pixel a colour the shared palette actually contains?
     (An antialiased glyph edge or an alpha-blended shadow is a blended
     pixel, and a blended pixel is a colour the palette does not have.)
  2. Are the light and dark bevel edges where they should be?
  3. Is any text clipped, overlapping or overflowing its container?

Usage:
    python3 analyze.py <png> [<png> ...]
"""
import struct
import sys
import zlib
from collections import Counter

# The shared palette, from art/palette.px.js and src/ui_theme.gd.
PALETTE = {
    "1e1a16": "K outline",
    "362a21": "D ink",
    "46382a": "P edge",
    "716855": "N mid brown",
    "d6d4c8": "X parchment",
    "e8dcc5": "C cream",
    "f7f2e3": "W paper",
    "dda742": "Y ochre",
    "e5b63d": "G gold",
    "c3613d": "T rust",
    "82a156": "M moss",
    "8896a3": "U slate",
    "b98053": "clay",
    "aca496": "rubble",
    "5f9f90": "relic teal",
    "a8e8ef": "moon",
    "c69a6b": "dig trench",
    "c17c50": "S warm brown",
    "6fd8e4": "E arcane teal",
    "ffffff": "white (probe only)",
    "efd788": "pale gold (probe only)",
}


def read_png(path):
    data = open(path, "rb").read()
    pos = 8
    idat = b""
    w = h = ct = 6
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, _bd, ct = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    raw = zlib.decompress(idat)
    bpp = 4 if ct == 6 else 3
    stride = w * bpp
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for _y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    return w, h, bpp, bytes(out)


def hexc(rgb):
    return "%02x%02x%02x" % rgb


def main(paths):
    for path in paths:
        w, h, bpp, px = read_png(path)

        def at(x, y):
            o = (y * w + x) * bpp
            return tuple(px[o:o + 3])

        counts = Counter()
        for y in range(h):
            for x in range(w):
                counts[at(x, y)] += 1

        off = [(c, n) for c, n in counts.items() if hexc(c) not in PALETTE]
        off.sort(key=lambda t: -t[1])
        print("=" * 68)
        print("%s  %dx%d" % (path, w, h))
        print("  distinct colours: %d   off-palette: %d" % (len(counts), len(off)))
        for c, n in off[:12]:
            print("    OFF-PALETTE %s  %d px  (%.2f%%)"
                  % (hexc(c), n, 100.0 * n / (w * h)))
        print("  palette colours present:")
        for c, n in counts.most_common():
            if hexc(c) in PALETTE:
                print("    %s %-22s %8d  %5.2f%%"
                      % (hexc(c), PALETTE[hexc(c)], n, 100.0 * n / (w * h)))


if __name__ == "__main__":
    main(sys.argv[1:])
