import re

p = '/Users/amre/Projects/GameStewKit/src/main.gd'
s = open(p).read()

# 1. fix the undefined colour constants in the new helper code
s = s.replace('_flat_style(COL_X)', '_flat_style(COL_GROUND)')
s = s.replace('_box_style(COL_C, col)', '_box_style(COL_PANEL, col)')
s = s.replace('_box_style(COL_W, col)', '_box_style(COL_CARD, col)')

# 2. the web HUD shows demand in the top bar; match it in Godot
old = '''	var luck_box := HBoxContainer.new()
	luck_box.add_theme_constant_override("separation", 3)
	luck_box.add_child(_chip(COL_SLATE))
	_lbl_luck = _stat_label("Luck 0.0", COL_TEXT)
	luck_box.add_child(_lbl_luck)
	row.add_child(luck_box)
'''
new = '''	var luck_box := HBoxContainer.new()
	luck_box.add_theme_constant_override("separation", 3)
	luck_box.add_child(_chip(COL_SLATE))
	_lbl_luck = _stat_label("Luck 0.0", COL_TEXT)
	luck_box.add_child(_lbl_luck)
	row.add_child(luck_box)

	# Demand: how many exhibits pay today. The drawn icon carries it, the
	# number stays in text.
	var demand_box := HBoxContainer.new()
	demand_box.add_theme_constant_override("separation", 3)
	demand_box.add_child(_icon("icon_demand", 18))
	_lbl_demand = _stat_label("0", COL_TEXT)
	demand_box.add_child(_lbl_demand)
	row.add_child(demand_box)
'''
assert old in s, "luck_box block not found"
s = s.replace(old, new)

# 3. declare the handle
old2 = 'var _lbl_luck: Label\n'
assert old2 in s
s = s.replace(old2, 'var _lbl_luck: Label\nvar _lbl_demand: Label\n')

# 4. refresh it
old3 = '\t_lbl_luck.text = "Luck %.1f" % state.luck()\n'
assert old3 in s
s = s.replace(old3, old3 + '\t_lbl_demand.text = "%d" % state.demand()\n')

for bad in ('COL_C,', 'COL_X)', 'COL_W,'):
    assert bad not in s, "still uses %s" % bad

open(p, 'w').write(s)
print("main.gd fixed")
