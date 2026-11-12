#!/usr/bin/env python3
"""Repair the reel-spin capture harness.

The harness asserted on `ui._reel_labels` - an array of Labels holding a
FONT GLYPH per reel window. The reel no longer works that way: the symbols
are drawn MOTIFS (TextureRects holding sprites), and the member is
`_reel_icons`. The field name was never updated, so the very first access
raised, the script aborted BEFORE `quit()` ran, and the Godot window hung
until the watchdog fired. That is why the reel step reported
"the reel capture produced no glyph output".

The fix keeps the harness's contract with validate.sh (three pipe-separated
symbol names, one per reel) but derives each name from the TEXTURE that is
in the window instead of from a font glyph. The measurement is still exact -
a symbol name is a symbol name - and it is now measuring what the reel
actually draws.
"""
import io
import sys

HARNESS = "/Users/amre/Projects/GameStewKit/tests/reel_spin_capture.gd"
VALIDATE = "/Users/amre/Projects/GameStewKit/tests/validate.sh"

EDITS = [
    # --- harness: the union rect now comes from the icon rects -----------
    ("""	for l in ui._reel_labels:
		var lr: Rect2 = l.get_global_rect()
		rect = rect.merge(lr) if rect.size != Vector2.ZERO else lr""",
     """	for icon in ui._reel_icons:
		var lr: Rect2 = icon.get_global_rect()
		rect = rect.merge(lr) if rect.size != Vector2.ZERO else lr"""),

    # --- harness: the symbol read --------------------------------------
    ("""func _glyphs() -> String:
	var parts: Array[String] = []
	for l in ui._reel_labels:
		parts.append(l.text)
	return "|".join(parts)""",
     """## The identity of what is in each reel window.
##
## The reel symbols are DRAWN MOTIFS, not font glyphs: each window holds a
## TextureRect whose texture is the symbol's sprite. So the name comes from
## the texture that is in the window - "symbol_clover.png" reads back as
## "clover" - and a window with no texture yet reads as "-".
func _symbols() -> String:
	var parts: Array[String] = []
	for icon in ui._reel_icons:
		parts.append(_symbol_of(icon))
	return "|".join(parts)


func _symbol_of(icon: TextureRect) -> String:
	var tex := icon.texture
	if tex == null:
		return "-"
	var file := tex.resource_path.get_file()
	if file.ends_with(".png"):
		file = file.substr(0, file.length() - 4)
	if file.begins_with("symbol_"):
		file = file.substr("symbol_".length())
	return file"""),

    # --- harness: the printed lines -------------------------------------
    ("""	print("[reel] spin pressed; glyphs now: ", _glyphs())""",
     """	print("[reel] spin pressed; symbols now: ", _symbols())"""),
    ("""			print("[reel] staggered frame glyphs: ", _glyphs())""",
     """			print("[reel] staggered frame symbols: ", _symbols())"""),
    ("""	print("[reel] settled glyphs: ", _glyphs())""",
     """	print("[reel] settled symbols: ", _symbols())"""),
    ("""	var seen := {}
	for i in 14:
		await create_timer(0.07).timeout
		var g := _glyphs()""",
     """	var seen := {}
	for i in 14:
		await create_timer(0.07).timeout
		var g := _symbols()"""),
    ("""	print("[reel] distinct glyph states during spin: ", seen.size())""",
     """	print("[reel] distinct symbol states during spin: ", seen.size())"""),

    # --- validate.sh: the two greps and their seds ----------------------
    ("""	SETTLED=$(grep -E "settled glyphs:" "$REEL_LOG" | tail -1 | sed 's/.*settled glyphs: //')
	STAGGER=$(grep -E "staggered frame glyphs:" "$REEL_LOG" | tail -1 | sed 's/.*staggered frame glyphs: //')""",
     """	SETTLED=$(grep -E "settled symbols:" "$REEL_LOG" | tail -1 | sed 's/.*settled symbols: //')
	STAGGER=$(grep -E "staggered frame symbols:" "$REEL_LOG" | tail -1 | sed 's/.*staggered frame symbols: //')"""),
    ("""	# The reel must land on three DIFFERENT symbols, and the windows must
	# stop in sequence rather than in lockstep. This is asserted on GLYPHS,
	# not on pixels: a vision model describes a crop unreliably, but a glyph
	# string is exact.""",
     """	# The reel must land on three DIFFERENT symbols, and the windows must
	# stop in sequence rather than in lockstep. This is asserted on SYMBOL
	# NAMES, not on pixels: a vision model describes a crop unreliably, but
	# a name read straight off the sprite in the window is exact."""),
    ("""		fail "the reel capture produced no glyph output\"""",
     """		fail "the reel capture produced no symbol output\""""),
    ("""	step "Reel capture (the stagger, asserted on glyphs)\"""",
     """	step "Reel capture (the stagger, asserted on symbols)\""""),
]


def patch(path, edits, label):
    src = io.open(path, encoding="utf-8").read()
    applied = 0
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            print("  %s: ANCHOR MISS (%d matches): %s" % (label, n, old.splitlines()[0][:70]))
            continue
        src = src.replace(old, new)
        applied += 1
    io.open(path, "w", encoding="utf-8").write(src)
    return applied


def main():
    a = patch(HARNESS, EDITS[:6], "harness")
    b = patch(VALIDATE, EDITS[6:], "validate")
    print("harness edits=%d validate edits=%d" % (a, b))
    return 0 if (a == 6 and b == 4) else 1


if __name__ == "__main__":
    sys.exit(main())
