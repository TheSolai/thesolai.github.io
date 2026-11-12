#!/usr/bin/env python3
"""Stop the tutorial card's buttons from stretching to the row height.

The coach card is a wide row: icon, title, body text, then the two
buttons on the right. The body text wraps to three lines, so the row is
123px tall, and Godot stretches a Button to fill the height of its
container by default. The result was two narrow vertical strips - "Got it"
measured 45x123 and "Skip" 26x123 - where their natural heights are 25 and
19. The text fit, but the control did not look like a button.

SHRINK_CENTER tells the container to give the button its natural height
and centre it in the row instead. The buttons keep their own minimum size,
so nothing is clipped and the row keeps its geometry.
"""
import io
import sys

PATH = "/Users/amre/Projects/GameStewKit/src/main.gd"

OLD = """	if str(state.tutorial.current().get("done", "")) == "":
		row.add_child(_button("Got it", func(): state.tutorial.advance()))
	var skip := _button("Skip", func(): state.skip_tutorial())
	skip.add_theme_color_override("font_color", COL_TEXT)
	skip.add_theme_font_size_override("font_size", 12)
	row.add_child(skip)
"""

NEW = """	if str(state.tutorial.current().get("done", "")) == "":
		var got_it := _button("Got it", func(): state.tutorial.advance())
		# The body text wraps to three lines, so this row is tall. A button
		# stretches to the row height by default, which turned "Got it" into
		# a 45x123 vertical strip. Keep the natural height, centred.
		got_it.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(got_it)
	var skip := _button("Skip", func(): state.skip_tutorial())
	skip.add_theme_color_override("font_color", COL_TEXT)
	skip.add_theme_font_size_override("font_size", 12)
	skip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(skip)
"""


def main() -> int:
    src = io.open(PATH, encoding="utf-8").read()
    if OLD not in src:
        print("ANCHOR NOT FOUND - no change made")
        return 1
    if src.count(OLD) != 1:
        print("ANCHOR NOT UNIQUE (%d matches) - no change made" % src.count(OLD))
        return 1
    out = src.replace(OLD, NEW)
    io.open(PATH, "w", encoding="utf-8").write(out)
    print("patched tutorial button vertical sizing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
