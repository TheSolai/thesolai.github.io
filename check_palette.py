#!/usr/bin/env python3
"""Check captured frames against the closed palette.

Every rendered pixel must be EXACTLY one of the palette colours (or a fully
transparent pixel). Anti-aliasing or alpha blending shows up here as an
off-palette pixel.
"""
import struct
import sys
import zlib
from collections import Counter

PALETTE = {
    (0x1e, 0x1a, 0x16): "K",
    (0x36, 0x2a, 0x21): "D",
    (0x46, 0x38, 0x2a): "P",
    (0x71, 0x68, 0x55): "N",
    (0xc1, 0x7c, 0x50): "S",
    (0xc6, 0x9a, 0x6b): "Z",
    (0xd6, 0xd4, 0xc8): "X",
    (0xe8, 0xdc, 0xc5): "C",
    (0xf7, 0xf2, 0xe3): "W",
    (0xb9, 0x80, 0x53): "A",
    (0xdd, 0xa7, 0x42): "Y",
    (0xe5, 0xb6, 0x3d): "G",
    (0xef, 0xd7, 0x88): "H",
    (0xc3, 0x61, 0x3d): "T",
    (0x82, 0xa1, 0x56): "M",
    (0x5f, 0x9f, 0x90): "L",
    (0x6f, 0xd8, 0xe4): "E",
    (0xa8, 0xe8, 0xef): "I",
    (0x88, 0x96, 0xa3): "U",
    (0xac, 0xa4, 0x96): "R",
}


def load(path):
    d = open(path, "rb").read()
    i, idat, pal, trns, ihdr = 8, b"", None, None, None
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        i += 12 + ln
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", data)
        elif typ == b"PLTE":
            pal = [tuple(data[j:j + 3]) for j in range(0, ln, 3)]
        elif typ == b"tRNS":
            trns = list(data)
        elif typ == b"IDAT":
            idat += data
    w, h, bd, ct = ihdr[0], ihdr[1], ihdr[2], ihdr[3]
    assert bd == 8, "bit depth %d" % bd
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(idat)
    stride = w * nch
    out = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        f = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if f == 1:
            for x in range(nch, stride):
                line[x] = (line[x] + line[x - nch]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - nch] if x >= nch else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - nch] if x >= nch else 0
                b = prev[x]
                c = prev[x - nch] if x >= nch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out.append(bytes(line))
        prev = line
    return w, h, ct, nch, pal, trns, out


def main(path):
    w, h, ct, nch, pal, trns, rows = load(path)
    counts = Counter()
    bad = Counter()
    total = 0
    for y in range(h):
        r = rows[y]
        for x in range(w):
            px = r[x * nch:(x + 1) * nch]
            if ct == 3:
                idx = px[0]
                alpha = trns[idx] if (trns and idx < len(trns)) else 255
                if alpha == 0:
                    counts["transparent"] += 1
                    total += 1
                    continue
                rgb = pal[idx]
            else:
                alpha = px[3] if nch == 4 else 255
                if alpha != 255:
                    counts["partial-alpha"] += 1
                    total += 1
                    continue
                rgb = (px[0], px[1], px[2])
            total += 1
            name = PALETTE.get(rgb)
            if name:
                counts[name] += 1
            else:
                bad[rgb] += 1
    name = path.split("/")[-1]
    off = sum(bad.values())
    pct = 100.0 * off / max(1, total)
    print("%-28s %dx%d  off-palette=%d (%.3f%%)" % (name, w, h, off, pct))
    if bad:
        for rgb, n in bad.most_common(8):
            print("      %s  x%d" % ("#%02x%02x%02x" % rgb, n))
    if counts:
        print("      palette: " + "  ".join(
            "%s=%d" % (k, counts[k]) for k in sorted(counts) if k != "transparent"))
    if "partial-alpha" in counts:
        print("      !! PARTIAL ALPHA present: %d px" % counts["partial-alpha"])
    return pct


if __name__ == "__main__":
    worst = 0.0
    for p in sys.argv[1:]:
        worst = max(worst, main(p))
    print("\nworst off-palette share: %.3f%%" % worst)
