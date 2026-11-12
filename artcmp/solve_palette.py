#!/usr/bin/env python3
"""Solve the shared palette against measured KairoSoft reference values.

Inputs (measured, not guessed):
  - the sprite set's own pixel distribution, so usage weights are real
  - the UI text/background pairs the palette also has to serve, because the
    same 20 colours are the web UI's colour set

Objective:
  - sprite pixels get lighter and keep their punch
  - UI text contrast never regresses
  - K stays near-black charcoal (KairoSoft outlines are 1px near-black)
  - every ramp keeps a visible step so lighting() can step along it
"""

import colorsys
import glob
import json
import statistics

from PIL import Image

CUR = {
    "K": "#16120f", "D": "#2f251d", "P": "#453729",
    "N": "#6e624a", "S": "#845537", "Z": "#b0895f",
    "X": "#d6d4c8", "C": "#e8dcc4", "W": "#f7f2e3",
    "A": "#b4794a", "Y": "#d9a441", "G": "#e0b23c", "H": "#f2d98a",
    "T": "#c05f3c", "M": "#7d9a52", "L": "#5f9e8f",
    "E": "#6dd3df", "I": "#a8e8ef", "U": "#8b99a6", "R": "#8a8378",
}
BODY = ["K", "D", "P", "N", "S", "Z", "A"]
NEUTRAL = ["X", "C", "W", "U", "R"]
ACCENTS = ["Y", "G", "H", "T", "M", "L", "E", "I"]
RAMPS = [["K", "D", "P", "N", "S"], ["X", "C", "W"], ["Y", "G", "H"], ["L", "E", "I"]]

# Minimum saturation each accent keeps, so the palette stays punchy.
ACCENT_MIN_SAT = {
    "Y": 0.66, "G": 0.68, "T": 0.62, "M": 0.42,
    "L": 0.36, "E": 0.46, "H": 0.38, "I": 0.24,
}

# Every foreground/background pair the web UI draws text on.
UI_PAIRS = [
    ("D", "C"), ("A", "C"), ("M", "C"), ("U", "C"), ("L", "C"), ("T", "C"),
    ("N", "C"), ("K", "Y"), ("G", "D"), ("Z", "D"), ("W", "M"), ("N", "M"),
    ("K", "C"), ("P", "C"), ("P", "X"), ("W", "L"), ("W", "M"), ("W", "U"),
    ("D", "A"),
]

TARGET_SPRITE_LUM = 110.0
TARGET_SAT = 0.390

# The paper surfaces are pinned. They are the UI's canvas, not sprite body
# colour, and the solver drifts them because they are barely used in the
# sprites. C is the panel fill, W the raised highlight and X the recessed
# well, so the three have to stay visibly distinct or the bevels vanish.
PINNED = {"X": 211.2, "C": 220.9, "W": 241.8,
          "Y": 172.0, "G": 182.0, "H": 213.0, "T": 122.0}


def lum(rgb):
    return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000.0


def sat(rgb):
    return colorsys.rgb_to_hsv(*[c / 255 for c in rgb])[1]


def hex_of(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def rgb_of(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(h):
    r, g, b = rgb_of(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def load_sprites(root="assets/sprites"):
    """Per-sprite palette-key histograms, so weights reflect real usage."""
    per_sprite = []
    for path in sorted(glob.glob(f"{root}/*.png")):
        if "atlas" in path:
            continue
        im = Image.open(path).convert("RGBA")
        keys = []
        for p in im.get_flattened_data():
            if p[3] > 127:
                k = next((kk for kk, c in CUR_RGB.items() if c == p[:3]), None)
                if k:
                    keys.append(k)
        per_sprite.append(keys)
    return per_sprite


CUR_RGB = {k: rgb_of(v) for k, v in CUR.items()}
BASE = {k: colorsys.rgb_to_hsv(*[c / 255 for c in rgb]) for k, rgb in CUR_RGB.items()}


def build(target_lum, sat_mult):
    """Solve each key's value so it lands on its target luminance."""
    out = {}
    for k, base in CUR_RGB.items():
        h, s, _v = BASE[k]
        ns = min(0.93, s * sat_mult[k])
        if k in PINNED:
            lo, hi = 0.0, 1.0
            for _ in range(34):
                mid = (lo + hi) / 2
                c = colorsys.hsv_to_rgb(h, ns, mid)
                if lum([x * 255 for x in c]) < PINNED[k]:
                    lo = mid
                else:
                    hi = mid
            c = colorsys.hsv_to_rgb(h, ns, (lo + hi) / 2)
            out[k] = hex_of([x * 255 for x in c])
            continue
        lo, hi = 0.0, 1.0
        for _ in range(34):
            mid = (lo + hi) / 2
            c = colorsys.hsv_to_rgb(h, ns, mid)
            if lum([x * 255 for x in c]) < target_lum[k]:
                lo = mid
            else:
                hi = mid
        c = colorsys.hsv_to_rgb(h, ns, (lo + hi) / 2)
        out[k] = hex_of([x * 255 for x in c])
    return out


def score(target_lum, sat_mult, per_sprite):
    pal = build(target_lum, sat_mult)
    pen = 0.0

    all_lum = []
    all_sat = []
    for keys in per_sprite:
        for k in keys:
            all_lum.append(lum(rgb_of(pal[k])))
            all_sat.append(sat(rgb_of(pal[k])))
    mean_lum = statistics.mean(all_lum)
    mean_sat = statistics.mean(all_sat)
    per_sprite_median = statistics.median(
        [statistics.mean([lum(rgb_of(pal[k])) for k in keys]) for keys in per_sprite]
    )

    # UI contrast must not regress, and must clear an absolute legibility floor.
    for fg, bg in UI_PAIRS:
        old = contrast(CUR[fg], CUR[bg])
        new = contrast(pal[fg], pal[bg])
        if new < old * 0.92:
            pen += (old * 0.92 - new) * 60
        if new < 1.8:
            pen += (1.8 - new) * 40

    for k, floor in ACCENT_MIN_SAT.items():
        pen += max(0.0, floor - sat(rgb_of(pal[k]))) * 60

    # KairoSoft outlines are near-black charcoal.
    if not 14 <= lum(rgb_of(pal["K"])) <= 30:
        pen += 16

    # Every ramp needs a visible step for lighting() to travel along.
    for grp in RAMPS:
        for i in range(len(grp) - 1):
            d = lum(rgb_of(pal[grp[i + 1]])) - lum(rgb_of(pal[grp[i]]))
            if d < 10:
                pen += (10 - d) * 3

    # The three paper surfaces must stay distinguishable, or a raised panel
    # and a recessed well end up the same colour.
    if lum(rgb_of(pal["W"])) - lum(rgb_of(pal["C"])) < 14:
        pen += (14 - (lum(rgb_of(pal["W"])) - lum(rgb_of(pal["C"])))) * 8
    if lum(rgb_of(pal["C"])) - lum(rgb_of(pal["X"])) < 8:
        pen += (8 - (lum(rgb_of(pal["C"])) - lum(rgb_of(pal["X"])))) * 8

    pen += abs(per_sprite_median - TARGET_SPRITE_LUM) * 1.2
    pen += abs(mean_sat - TARGET_SAT) * 45
    return pen, pal, mean_lum, mean_sat, per_sprite_median


def main():
    per_sprite = load_sprites()
    tl = {k: BASE[k][2] * 255 for k in CUR}
    sm = {k: 1.0 for k in CUR}
    for k in BODY:
        sm[k] = 0.84
    for k in NEUTRAL:
        sm[k] = 0.95
    tl.update({
        "K": 22, "D": 52, "P": 84, "N": 124, "S": 120, "Z": 166, "A": 146,
        "X": 212, "C": 224, "W": 244, "Y": 170, "G": 180, "H": 216,
        "T": 130, "M": 140, "L": 144, "E": 186, "I": 214, "U": 164, "R": 154,
    })

    best = None
    # Deterministic coordinate descent: fast, and it always finishes.
    for sweep in range(14):
        improved = False
        for k in CUR:
            for axis in ("lum", "sat"):
                for delta in (6, -6, 3, -3, 1.5, -1.5):
                    t2, s2 = dict(tl), dict(sm)
                    if axis == "lum":
                        t2[k] = max(8, min(250, t2[k] + delta))
                    else:
                        s2[k] = max(0.05, min(1.0, s2[k] + delta * 0.012))
                    sc, pal, ml, ms, ps = score(t2, s2, per_sprite)
                    if best is None or sc < best[0] - 1e-9:
                        best = (sc, dict(t2), dict(s2), pal, ml, ms, ps)
                        tl, sm = t2, s2
                        improved = True
        if not improved:
            break

    sc, tl, sm, pal, ml, ms, ps = best
    print(f"score {sc:.3f}")
    print(f"FINAL sprite mean lum {ml:.1f}  per-sprite median {ps:.1f}  mean sat {ms:.3f}")
    print(f"OLD   sprite mean lum 95.6  per-sprite median 94.9  mean sat 0.412\n")
    for k in CUR:
        print(f"  {k}: {CUR[k]} -> {pal[k]}   lum {lum(CUR_RGB[k]):5.1f}->{lum(rgb_of(pal[k])):5.1f}"
              f"  sat {sat(CUR_RGB[k]):.2f}->{sat(rgb_of(pal[k])):.2f}")
    for grp in RAMPS:
        print("  ramp", "".join(grp), [round(lum(rgb_of(pal[k])), 1) for k in grp])
    print("\nUI contrast:")
    for fg, bg in UI_PAIRS:
        old = contrast(CUR[fg], CUR[bg])
        new = contrast(pal[fg], pal[bg])
        flag = "" if new >= old * 0.92 else "  <-- REGRESSION"
        print(f"  {fg} on {bg}: {old:5.2f} -> {new:5.2f}{flag}")
    with open("/tmp/kairo/final_palette.json", "w") as fh:
        json.dump(pal, fh, indent=1)
    print("\nsaved /tmp/kairo/final_palette.json")


if __name__ == "__main__":
    main()
