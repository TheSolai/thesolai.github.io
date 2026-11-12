#!/usr/bin/env python3
"""Polish the SIDHE & STONE Godot UI.

Edits src/main.gd, src/goals.gd and tests/ in /Users/amre/Projects/GameStewKit.
Region surgery is anchor-based (stripped line match, with occurrence
counting) so indentation and line numbers cannot drift.
"""
import os
import re
import shutil

REPO = "/Users/amre/Projects/GameStewKit"


def T(s):
    """Convert 4-space-per-level indentation to tabs (the repo's style)."""
    return re.sub(r"^((?:    )+)", lambda m: "\t" * (len(m.group(1)) // 4), s, flags=re.M)


class Editor:
    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="utf-8") as fh:
            self.lines = fh.read().split("\n")
        self.ops = 0

    def _hits(self, anchor, start=0):
        return [i for i, l in enumerate(self.lines)
                if i >= start and l.strip() == anchor.strip()]

    def _find(self, anchor, start=0, occ=1):
        hits = self._hits(anchor, start)
        if len(hits) < occ:
            raise SystemExit("ANCHOR NOT FOUND (%d/%d): %r" % (len(hits), occ, anchor))
        return hits[occ - 1]

    def replace(self, start_anchor, end_anchor, new_text, s_occ=1, e_occ=1):
        i = self._find(start_anchor, 0, s_occ)
        j = self._find(end_anchor, i, e_occ)
        block = T(new_text).rstrip("\n").split("\n")
        self.lines[i:j + 1] = block
        self.ops += 1

    def insert_after(self, anchor, new_text, occ=1):
        i = self._find(anchor, 0, occ)
        self.lines[i + 1:i + 1] = T(new_text).rstrip("\n").split("\n")
        self.ops += 1

    def insert_before(self, anchor, new_text, occ=1):
        i = self._find(anchor, 0, occ)
        self.lines[i:i] = T(new_text).rstrip("\n").split("\n")
        self.ops += 1

    def sub(self, old, new, occ=1):
        hits = self._hits(old)
        if len(hits) < occ:
            raise SystemExit("SUB NOT FOUND (%d/%d): %r" % (len(hits), occ, old))
        i = hits[occ - 1]
        indent = self.lines[i][:len(self.lines[i]) - len(self.lines[i].lstrip())]
        self.lines[i] = indent + new.strip()
        self.ops += 1

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines))


# ------------------------------------------------------------------ main.gd

m = Editor(os.path.join(REPO, "src", "main.gd"))

# --- 1. a secondary ink that is legal on cream and parchment -------------
m.insert_after(
    'const COL_SLATE := Color("8896a3")    ## U - neutral metal',
    '''
## P - secondary text. N is legal on paper white ONLY, so wherever the
## surface is cream (C) or parchment (X) the dim text uses this instead.
const COL_DIM_P := Color("46382a")
''')

# --- 2. node handles for the semantic chips ------------------------------
m.insert_after(
    'var _bar_goal: ProgressBar',
    '''
var _chip_money: ColorRect
var _chip_payout: ColorRect
var _chip_status: ColorRect
var _chip_goal: ColorRect
var _odds_body: VBoxContainer
''')

# --- 3. the theme owns every control -------------------------------------
m.insert_after(
    'func _build_ui() -> void:',
    '''
\t# The ONE theme, applied to the root, so every button, scrollbar and
\t# progress track in the tree is styled from the shared palette instead of
\t# Godot's default dark grey.
\ttheme = StoneTheme.build()
''')

# --- 4. top bar: sprite-backed money and charms --------------------------
m.replace(
    '_lbl_day = _stat_label("Day 1", COL_TEXT)',
    'row.add_child(_lbl_luck)',
    '''
    _lbl_day = _stat_label("Day 1", COL_TEXT)
    row.add_child(_lbl_day)

    # Money: the drawn coin carries "money", the number stays in text.
    var money_box := HBoxContainer.new()
    money_box.add_theme_constant_override("separation", 3)
    money_box.add_child(_icon("icon_coin", 18))
    _lbl_money = _stat_label("£240", COL_TEXT)
    money_box.add_child(_lbl_money)
    # Negative money is bad news: a rust CHIP says so, the text stays dark.
    _chip_money = _chip(COL_RUST)
    _chip_money.visible = false
    money_box.add_child(_chip_money)
    row.add_child(money_box)

    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    row.add_child(spacer)

    # Charms: the drawn charm carries the resource, the count stays in text.
    var charm_box := HBoxContainer.new()
    charm_box.add_theme_constant_override("separation", 3)
    charm_box.add_child(_icon("icon_charm", 18))
    _lbl_charms = _stat_label("6", COL_TEXT)
    charm_box.add_child(_lbl_charms)
    row.add_child(charm_box)

    var luck_box := HBoxContainer.new()
    luck_box.add_theme_constant_override("separation", 3)
    luck_box.add_child(_chip(COL_SLATE))
    _lbl_luck = _stat_label("Luck 0.0", COL_TEXT)
    luck_box.add_child(_lbl_luck)
    row.add_child(luck_box)
    ''')

# --- 5. milestone header: legal dim ink + a chip for "all earned" --------
m.replace(
    'ghead.add_child(_label("MILESTONE", COL_DIM, 11))',
    'ghead.add_child(_label("MILESTONE", COL_DIM, 11))',
    '''
    ghead.add_child(_label("MILESTONE", COL_DIM_P, 11))
    # Good news about the ladder: a moss chip, never moss TEXT.
    _chip_goal = _chip(COL_MOSS)
    _chip_goal.visible = false
    ghead.add_child(_chip_goal)
    ''')

m.sub('_lbl_goal_sub = _label("", COL_DIM, 11)',
      '_lbl_goal_sub = _label("", COL_DIM_P, 11)')

# --- 6. reel head: payout chip, the Odds button, the spin button ---------
m.replace(
    '_lbl_payout = Label.new()',
    'head.add_child(_lbl_payout)',
    '''
    # A good or bad multiplier is a CHIP beside the number, not a coloured
    # number: coloured text on a cream surface is not in the palette rules.
    _chip_payout = _chip(COL_MOSS)
    _chip_payout.visible = false
    head.add_child(_chip_payout)

    _lbl_payout = Label.new()
    _lbl_payout.text = "×1.00"
    _lbl_payout.add_theme_color_override("font_color", COL_TEXT)
    _lbl_payout.add_theme_font_size_override("font_size", 15)
    head.add_child(_lbl_payout)
    ''')

m.sub('_btn_table.add_theme_color_override("font_color", COL_SLATE)',
      '_btn_table.add_theme_color_override("font_color", COL_DIM)')

m.replace(
    '_btn_spin = Button.new()',
    'head.add_child(_btn_spin)',
    '''
    _btn_spin = Button.new()
    _btn_spin.text = "Spin (2 charms)"
    _btn_spin.add_theme_font_size_override("font_size", 15)
    # The one warm call to action, so it gets the ochre fill with dark ink.
    _btn_spin.add_theme_stylebox_override("normal", _box_style(COL_GOLD, COL_K))
    _btn_spin.add_theme_stylebox_override("hover", _box_style(COL_GOLD_INK, COL_K))
    _btn_spin.add_theme_stylebox_override("pressed", _box_style(COL_GOLD, COL_K))
    _btn_spin.add_theme_color_override("font_color", COL_K)
    _btn_spin.add_theme_color_override("font_hover_color", COL_K)
    _btn_spin.add_theme_color_override("font_pressed_color", COL_K)
    # The charm sprite, drawn, never a font glyph.
    var charm_tex_path := SPRITE_DIR + "icon_charm.png"
    if ResourceLoader.exists(charm_tex_path):
        _btn_spin.icon = load(charm_tex_path)
        _btn_spin.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    _btn_spin.pressed.connect(_on_spin_pressed)
    head.add_child(_btn_spin)
    ''')

# --- 7. status line: chip beside dark text -------------------------------
m.replace(
    '_lbl_status = Label.new()',
    'col.add_child(_lbl_status)',
    '''
    # Status is a single line of dark text with a chip beside it. The chip
    # carries good news (moss) or bad news (rust); the words carry the fact.
    var status_row := HBoxContainer.new()
    status_row.add_theme_constant_override("separation", 6)
    col.add_child(status_row)

    _chip_status = _chip(COL_MOSS)
    _chip_status.visible = false
    status_row.add_child(_chip_status)

    _lbl_status = Label.new()
    _lbl_status.text = ""
    _lbl_status.add_theme_color_override("font_color", COL_TEXT)
    _lbl_status.add_theme_font_size_override("font_size", 13)
    _lbl_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    _lbl_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    status_row.add_child(_lbl_status)
    ''')

# --- 8. the odds table, rebuilt to match the web -------------------------
m.replace(
    'func _build_odds_table() -> PanelContainer:',
    'return panel',
    '''
func _build_odds_table() -> PanelContainer:
    var panel := PanelContainer.new()
    panel.add_theme_stylebox_override("panel", _panel_style(COL_PANEL))

    var col := VBoxContainer.new()
    col.add_theme_constant_override("separation", 6)
    panel.add_child(col)

    var head := Label.new()
    head.text = "What the wheel shows"
    head.add_theme_color_override("font_color", COL_TEXT)
    head.add_theme_font_size_override("font_size", 14)
    col.add_child(head)

    # The rows are rebuilt whenever the state refreshes, because the weights
    # move with luck and a stale percentage is worse than no percentage.
    _odds_body = VBoxContainer.new()
    _odds_body.add_theme_constant_override("separation", 5)
    col.add_child(_odds_body)
    _rebuild_odds_body()

    var ev := Label.new()
    ev.text = "EV now %.3f   ·   a miss still pays ×1.00" % state.sim.reel.expected_value()
    ev.add_theme_color_override("font_color", COL_DIM_P)
    ev.add_theme_font_size_override("font_size", 12)
    ev.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    col.add_child(ev)
    return panel


## One row of the odds table: the drawn motif, the name, the multiplier,
## the weight-derived percentage, and a bar whose fill is the share.
##
## The bar is a FILL, so the symbol colour is legal there. The numbers stay
## in dark ink, because a coloured number on cream is not.
func _rebuild_odds_body() -> void:
    if _odds_body == null:
        return
    for c in _odds_body.get_children():
        _odds_body.remove_child(c)
        c.queue_free()

    var weights: Dictionary = state.sim.reel.weights()
    var total := 0.0
    for s in SYMBOL_ORDER:
        total += float(weights.get(s, 0.0))

    for s in SYMBOL_ORDER:
        var st: Dictionary = SYMBOL_STYLE[s]
        var sym_col: Color = st["col"]
        var share := 0.0
        if total > 0.0:
            share = float(weights.get(s, 0.0)) / total

        var row := VBoxContainer.new()
        row.add_theme_constant_override("separation", 2)
        _odds_body.add_child(row)

        var line := HBoxContainer.new()
        line.add_theme_constant_override("separation", 8)
        row.add_child(line)

        line.add_child(_icon(SYMBOL_SPRITE[s], 16))

        var nm := Label.new()
        nm.text = str(st["name"])
        nm.add_theme_color_override("font_color", COL_TEXT)
        nm.add_theme_font_size_override("font_size", 13)
        nm.custom_minimum_size = Vector2(74, 0)
        line.add_child(nm)

        var mult := Label.new()
        mult.text = "×%.2f" % float(ReelCore.SYMBOLS[s]["mult"])
        mult.add_theme_color_override("font_color", COL_TEXT)
        mult.add_theme_font_size_override("font_size", 13)
        mult.custom_minimum_size = Vector2(48, 0)
        line.add_child(mult)

        var pct := Label.new()
        pct.text = "%.1f%%" % (share * 100.0)
        pct.add_theme_color_override("font_color", COL_DIM_P)
        pct.add_theme_font_size_override("font_size", 13)
        pct.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
        pct.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        line.add_child(pct)

        # The probability bar. The fill is the symbol's own colour.
        var bar := ProgressBar.new()
        bar.show_percentage = false
        bar.custom_minimum_size = Vector2(0, 7)
        bar.max_value = 1.0
        bar.value = share
        bar.add_theme_stylebox_override("background", _flat_style(COL_X))
        bar.add_theme_stylebox_override("fill", _flat_style(sym_col))
        row.add_child(bar)
    ''')

# --- 9. footer: New Game carries its meaning in the outline --------------
m.sub('_btn_new.add_theme_color_override("font_color", COL_RUST)',
      '_outlined(_btn_new, COL_RUST)')

# --- 10. refresh: money, charms, payout, spin ----------------------------
m.replace(
    '_lbl_day.text = "Day %d" % (state.day() + 1)',
    '_btn_spin.text = "Spin (%d☘)" % state.charm_cost()',
    '''
    _lbl_day.text = "Day %d" % (state.day() + 1)
    _lbl_money.text = "£%d" % state.money()
    _lbl_money.add_theme_color_override("font_color", COL_TEXT)
    _chip_money.visible = state.money() < 0
    _lbl_charms.text = "%d" % state.charms()
    _lbl_luck.text = "Luck %.1f" % state.luck()

    var pending := state.pending_payout()
    if pending > 1.0:
        _lbl_payout.text = "×%.2f today" % pending
        _set_chip(_chip_payout, COL_MOSS, true)
    else:
        _lbl_payout.text = "×1.00 today"
        _set_chip(_chip_payout, COL_MOSS, false)

    _btn_spin.disabled = not state.can_spin() or _spin_active
    _btn_spin.text = "Spin (%d charms)" % state.charm_cost()
    ''')

# --- 11. the goal strip: dark text + a chip for "all earned" ------------
m.replace(
    'var ng := state.next_goal()',
    '_bar_goal.value = clampf(float(ng["progress"]) / maxf(1.0, float(ng["target"])), 0.0, 1.0)',
    '''
    var ng := state.next_goal()
    if ng.is_empty():
        _lbl_goal.text = "Every milestone earned. The gallery is yours."
        _lbl_goal.add_theme_color_override("font_color", COL_TEXT)
        _lbl_goal_sub.text = ""
        _bar_goal.value = 1.0
        _chip_goal.visible = true
    else:
        var g: Dictionary = ng["goal"]
        _lbl_goal.text = str(g["title"])
        _lbl_goal.add_theme_color_override("font_color", COL_TEXT)
        _lbl_goal_sub.text = "%s   (%d/%d)" % [str(g["body"]),
            int(ng["progress"]), int(ng["target"])]
        _bar_goal.value = clampf(float(ng["progress"]) / maxf(1.0, float(ng["target"])), 0.0, 1.0)
        _chip_goal.visible = false
    ''')

# --- 12. the gallery: visitors, demand icon, legal ink -------------------
m.replace(
    'var case_row := HBoxContainer.new()',
    '_content.add_child(case_row)',
    '''
    var case_row := HBoxContainer.new()
    case_row.add_theme_constant_override("separation", 8)
    case_row.add_child(_icon("gallery_case", 44))
    case_row.add_child(_label("Exhibits on display bring visitors through the door.",
        COL_DIM_P, 13))
    _content.add_child(case_row)

    # The people in the museum. Three DIFFERENT visitors, so the gallery
    # reads as a place with people in it rather than a row of display cases.
    var visitor_row := HBoxContainer.new()
    visitor_row.add_theme_constant_override("separation", 4)
    visitor_row.add_child(_icon("visitor_a", 28))
    visitor_row.add_child(_icon("visitor_b", 28))
    visitor_row.add_child(_icon("visitor_c", 28))
    visitor_row.add_child(_label("Visitors in today: %d" % state.demand(), COL_DIM_P, 13))
    _content.add_child(visitor_row)
    ''')

m.replace(
    'var card := _card(GRADE_COL[grade])',
    'row.add_child(b)',
    '''
        var card := _card(GRADE_COL[grade])
        var col := _card_col(card)
        var row := HBoxContainer.new()
        row.add_theme_constant_override("separation", 8)
        col.add_child(row)
        row.add_child(_icon(GRADE_SPRITE[grade], 34))
        # The grade colour lives in the sprite and in the card's outline.
        # The NAME is written out, so colour is never the only meaning.
        row.add_child(_label("%s  %s" % [grade.capitalize(), "×%d" % n],
            COL_TEXT, 17))
        row.add_child(_spacer(8, 0))
        row.add_child(_label("£%d/day each" % state.exhibit_value(grade), COL_DIM, 13))
        var sp := Control.new()
        sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        row.add_child(sp)
        var b := _button("To Vault", func(): state.vault_one(grade))
        row.add_child(b)
    ''')

m.replace(
    'col.add_child(_label(" · ".join(bits),',
    'COL_RUST if (earning < n or risk > 0.07) else COL_DIM, 12))',
    '''
        # Risk is good-or-bad news, so it gets a CHIP, not coloured text.
        var warned: bool = earning < n or risk > 0.07
        var risk_row := HBoxContainer.new()
        risk_row.add_theme_constant_override("separation", 6)
        if warned:
            risk_row.add_child(_chip(COL_RUST))
        risk_row.add_child(_label(" · ".join(bits),
            COL_TEXT if warned else COL_DIM, 12))
        col.add_child(risk_row)
    ''')

m.replace(
    'var slots := _label("%d of %d slots in use  ·  %d slot(s) free"',
    '% state.raw_count(), COL_DIM, 13))',
    '''
    var slots := _label("%d of %d slots in use  ·  %d slot(s) free"
        % [state.on_display(), state.gallery_slots(), state.slots_free()], COL_DIM_P, 13)
    _content.add_child(slots)

    _content.add_child(_spacer(0, 8))
    _content.add_child(_section_title("Today"))

    # Demand wears the drawn demand icon, and the number stays in text.
    var demand_row := HBoxContainer.new()
    demand_row.add_theme_constant_override("separation", 6)
    demand_row.add_child(_icon("icon_demand", 16))
    demand_row.add_child(_label("Demand: %d exhibit(s)  ·  Upkeep: £%d/day"
        % [state.demand(), state.upkeep()], COL_DIM_P, 13))
    _content.add_child(demand_row)

    _content.add_child(_label("Storeroom: %d raw find(s) waiting to be catalogued"
        % state.raw_count(), COL_DIM_P, 13))
    ''')

# --- 13. the vault: legal grade ink, outlined Sell -----------------------
m.replace(
    'var card := _card(GRADE_COL[grade])',
    'row.add_child(sell)',
    '''
        var card := _card(GRADE_COL[grade])
        var row := _card_row(card)
        row.add_child(_icon(GRADE_SPRITE[grade], 34))
        # The grade colour is in the sprite and the card outline; the name is
        # written out. Colour supplements, it never carries the meaning alone.
        row.add_child(_label("%s  ×%d" % [grade.capitalize(), n], COL_TEXT, 17))
        row.add_child(_spacer(8, 0))
        row.add_child(_label("£%d/day each" % state.exhibit_value(grade), COL_DIM, 13))
        var sp := Control.new()
        sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        row.add_child(sp)

        var can_show := state.slots_free() > 0
        var show_btn := _button("Display", func(): state.display_one(grade))
        show_btn.disabled = not can_show
        row.add_child(show_btn)

        var sell := _button("Sell", func(): state.sell_one(grade))
        _outlined(sell, COL_RUST)
        row.add_child(sell)
    ''', s_occ=2)

# --- 14. the digs: chips for progress and identity -----------------------
m.replace(
    'row.add_child(_label("%s — %d day(s) left" % [_dig_name(dig), maxi(0, left)],',
    'COL_MOSS, 15))',
    '''
            # Progress is good news: a moss chip beside dark text.
            row.add_child(_chip_label(COL_MOSS,
                "%s — %d day(s) left" % [_dig_name(dig), maxi(0, left)], 15))
        ''')

m.replace(
    'if state.money() < state.dig_cost(dig):',
    'b.add_theme_color_override("font_color", COL_RUST)',
    '''
                if state.money() < state.dig_cost(dig):
                    # Unaffordable dig: the OUTLINE says so, not coloured text.
                    _outlined(b, COL_RUST)
                ''')

m.sub('row.add_child(_label("Assigned: %s" % _dig_name(pending), COL_TEXT, 13))',
      'row.add_child(_chip_label(DIG_COL.get(pending, COL_DIM),\n'
      '\t\t\t\t\t"Assigned: %s" % _dig_name(pending), 13))')

# --- 15. the dig panel shows demand, with its drawn icon ----------------
m.insert_before(
    'for i in state.sites():',
    '''
    var dig_demand_row := HBoxContainer.new()
    dig_demand_row.add_theme_constant_override("separation", 6)
    dig_demand_row.add_child(_icon("icon_demand", 16))
    dig_demand_row.add_child(_label("Visitors today: %d  ·  demand %d exhibit(s)"
        % [state.demand(), state.demand()], COL_DIM_P, 13))
    _content.add_child(dig_demand_row)

''')

# --- 16. the day report: chips beside dark numbers ----------------------
m.replace(
    'col.add_child(_report_line("Takings", "£%d" % revenue,',
    'COL_MOSS if delta >= 0 else COL_RUST))',
    '''
    col.add_child(_report_line("Takings", "£%d" % revenue, COL_GOLD, revenue > 0))
    if opex > 0:
        col.add_child(_report_line("Upkeep & dig costs", "-£%d" % opex, COL_DIM))
    if int(s["capex"]) > 0:
        col.add_child(_report_line("Invested", "-£%d" % int(s["capex"]), COL_SLATE, true))
    col.add_child(_report_line("Net", "%s£%d" % ["+" if delta >= 0 else "-", absi(delta)],
        COL_MOSS if delta >= 0 else COL_RUST, true))
    ''')

m.replace(
    'if absf(payout - 1.0) > 0.001:',
    'col.add_child(_report_line("Catalogued", "%d find(s)" % curated, COL_TEXT))',
    '''
    if absf(payout - 1.0) > 0.001:
        col.add_child(_report_line("Fate Reel", "×%.2f" % payout,
            COL_MOSS if payout > 1.0 else COL_RUST, true))

    var curated := int(s["curated"])
    if curated > 0:
        col.add_child(_report_line("Catalogued", "%d find(s)" % curated, COL_TEXT))
    ''')

m.sub('col.add_child(_report_line("STOLEN", ", ".join(named), COL_RUST))',
      'col.add_child(_report_line("STOLEN", ", ".join(named), COL_RUST, true))')

m.replace(
    'func _report_line(key: String, value: String, col: Color) -> Control:',
    'return row',
    '''
func _report_line(key: String, value: String, col: Color, chip: bool = false) -> Control:
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 8)
    row.add_child(_label(key, COL_DIM_P, 15))
    var sp := Control.new()
    sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    row.add_child(sp)
    if chip:
        row.add_child(_chip(col))
    var value_label := Label.new()
    value_label.text = value
    value_label.add_theme_color_override("font_color", COL_TEXT)
    value_label.add_theme_font_size_override("font_size", 16)
    row.add_child(value_label)
    return row
    ''')

# --- 17. the goals ladder: EARNED as a chip + dark text ------------------
m.sub('title_col.add_child(_label(str(g["title"]), COL_TEXT if not done else COL_MOSS, 15))',
      'title_col.add_child(_label(str(g["title"]), COL_TEXT, 15))')

m.sub('row.add_child(_label("✓ EARNED", COL_MOSS, 13))',
      'row.add_child(_chip_label(COL_MOSS, "EARNED", 13))')

m.sub('_content.add_child(_label(t.to_upper(), COL_DIM, 13))',
      '_content.add_child(_label(t.to_upper(), COL_DIM_P, 13))')

# --- 18. the ledger: chips, dark numbers, legal dim ink ------------------
m.replace(
    'head.add_child(_label("Day", COL_DIM, 13))',
    'head.add_child(_label("Stol", COL_DIM, 13))',
    '''
        head.add_child(_label("Day", COL_DIM_P, 13))
        head.add_child(_label("Takings", COL_DIM_P, 13))
        head.add_child(_label("Costs", COL_DIM_P, 13))
        head.add_child(_label("Net", COL_DIM_P, 13))
        head.add_child(_label("Cur", COL_DIM_P, 13))
        head.add_child(_label("Stol", COL_DIM_P, 13))
    ''')

m.replace(
    'row.add_child(_label("%d" % (i + 1), COL_TEXT, 13))',
    'COL_RUST if (i < stol.size() and int(stol[i]) > 0) else COL_DIM, 13))',
    '''
                row.add_child(_label("%d" % (i + 1), COL_TEXT, 13))
                row.add_child(_label("%d" % int(rev[i]), COL_TEXT, 13))
                row.add_child(_label("%d" % (int(opx[i]) if i < opx.size() else 0), COL_DIM_P, 13))
                # Net: the sign carries the meaning, the chip carries the mood.
                row.add_child(_chip(COL_MOSS if net >= 0 else COL_RUST))
                row.add_child(_label("%s%d" % ["+" if net >= 0 else "-", absi(net)],
                    COL_TEXT, 13))
                row.add_child(_label("%d" % (int(cur[i]) if i < cur.size() else 0), COL_TEXT, 13))
                if i < stol.size() and int(stol[i]) > 0:
                    row.add_child(_chip(COL_RUST))
                row.add_child(_label("%d" % (int(stol[i]) if i < stol.size() else 0),
                    COL_TEXT, 13))
    ''')

m.replace(
    'var tint := COL_TEXT',
    '"dig": tint = COL_DIM',
    '''
        var chip_col := COL_TEXT
        match kind:
            "day": chip_col = COL_GOLD
            "display": chip_col = COL_MOSS
            "upgrade": chip_col = COL_SLATE
            "sale": chip_col = COL_RUST
            "dig": chip_col = COL_DIM
        var ev_row := HBoxContainer.new()
        ev_row.add_theme_constant_override("separation", 6)
        ev_row.add_child(_chip(chip_col))
        ev_row.add_child(_label("Day %d — %s" % [int(e.get("day", 0)),
            str(e.get("text", ""))], COL_TEXT, 13))
        _content.add_child(ev_row)
    ''')

# --- 19. status lines: chip + dark text ----------------------------------
m.replace(
    '_lbl_status.text = "Saved."',
    '_lbl_status.add_theme_color_override("font_color", COL_RUST)',
    '''
        _set_status("Saved.", COL_MOSS, true)
    else:
        _set_status("Could not save.", COL_RUST, true)
    ''')

m.replace(
    '_lbl_status.text = "Loaded."',
    '_lbl_status.add_theme_color_override("font_color", COL_RUST)',
    '''
        _set_status("Loaded.", COL_MOSS, true)
        _clear_overlay()
        _refresh()
    else:
        _set_status("No save found.", COL_RUST, true)
    ''')

m.sub('_btn_new.add_theme_color_override("font_color", COL_RUST)',
      '_outlined(_btn_new, COL_RUST)')

m.replace(
    '_lbl_status.text = "A fresh outfit. Good luck."',
    '_lbl_status.add_theme_color_override("font_color", COL_TEXT)',
    '''
    _set_status("A fresh outfit. Good luck.", COL_MOSS, true)
    ''')

m.replace(
    '_lbl_status.text = msg',
    'COL_MOSS if payout > 1.0 else (COL_RUST if payout < 1.0 else COL_DIM))',
    '''
    _set_status(msg, COL_MOSS if payout > 1.0 else COL_RUST, payout != 1.0)
    ''')

m.replace(
    '_lbl_status.text = "  ·  ".join(bits)',
    '_lbl_status.add_theme_color_override("font_color", COL_TEXT)',
    '''
    _set_status("  ·  ".join(bits), COL_TEXT, false)
    ''')

# --- 20. the event banner effects line ----------------------------------
m.sub('col.add_child(_label("· ".join(effects), COL_SLATE, 12))',
      'col.add_child(_label("· ".join(effects), COL_DIM, 12))')

# --- 21. the tutorial skip button ----------------------------------------
m.sub('skip.add_theme_color_override("font_color", COL_DIM)',
      'skip.add_theme_color_override("font_color", COL_TEXT)')

# --- 22. hints live on parchment: N is not legal there -------------------
m.replace(
    'func _hint(text: String) -> Control:',
    'var l := _label(text, COL_DIM, 13)',
    '''
func _hint(text: String) -> Control:
    # Hints sit on the parchment page, where N is not a legal text colour.
    var l := _label(text, COL_DIM_P, 13)
    return l
    ''')

# --- 23. the new widget helpers ------------------------------------------
m.insert_before(
    'func _spacer(w: float, h: float) -> Control:',
    '''
## A small solid colour chip.
##
## The palette rule forbids accent colours as TEXT on cream, but allows them
## as fills, bars, chips and outlines. This is the chip: a small square of a
## palette colour that sits beside a line of dark text and carries the
## meaning - good news, bad news, money, identity - without colouring the
## words themselves.
func _chip(col: Color, px: int = 8) -> ColorRect:
    var c := ColorRect.new()
    c.color = col
    c.custom_minimum_size = Vector2(px, px)
    c.size_flags_vertical = Control.SIZE_SHRINK_CENTER
    c.mouse_filter = Control.MOUSE_FILTER_IGNORE
    return c


## A chip beside a line of dark text.
func _chip_label(col: Color, text: String, size: int = 13) -> HBoxContainer:
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 5)
    row.add_child(_chip(col))
    var l := Label.new()
    l.text = text
    l.add_theme_color_override("font_color", COL_TEXT)
    l.add_theme_font_size_override("font_size", size)
    row.add_child(l)
    return row


## Show or hide a chip, and set its colour.
func _set_chip(c: ColorRect, col: Color, on: bool) -> void:
    if c == null:
        return
    c.visible = on
    if on:
        c.color = col


## Set the status line: dark text, with a chip for good or bad news.
func _set_status(text: String, col: Color, chip: bool) -> void:
    _lbl_status.text = text
    _lbl_status.add_theme_color_override("font_color", COL_TEXT)
    _set_chip(_chip_status, col, chip)


## A button whose meaning is carried by its OUTLINE rather than by coloured
## text. Dark ink on the cream button, a coloured border for the emphasis.
func _outlined(b: Button, col: Color) -> void:
    b.add_theme_color_override("font_color", COL_TEXT)
    b.add_theme_color_override("font_hover_color", COL_TEXT)
    b.add_theme_color_override("font_pressed_color", COL_TEXT)
    b.add_theme_stylebox_override("normal", _box_style(COL_C, col))
    b.add_theme_stylebox_override("hover", _box_style(COL_W, col))
    b.add_theme_stylebox_override("pressed", _box_style(COL_C, col))
    b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())


''')

# --- 24. stylebox helpers -------------------------------------------------
m.insert_before(
    'func _panel_style(col: Color) -> StyleBoxFlat:',
    '''
## A flat filled box with a border and no corner radius: the house style.
func _box_style(fill: Color, border: Color) -> StyleBoxFlat:
    var s := StyleBoxFlat.new()
    s.bg_color = fill
    s.border_color = border
    s.set_border_width_all(2)
    s.set_corner_radius_all(0)
    s.content_margin_left = 8
    s.content_margin_right = 8
    s.content_margin_top = 4
    s.content_margin_bottom = 4
    return s


## A flat filled box with no border.
func _flat_style(fill: Color) -> StyleBoxFlat:
    var s := StyleBoxFlat.new()
    s.bg_color = fill
    s.set_corner_radius_all(0)
    return s


''')

# --- 25. keep the odds table in step with the luck stat ------------------
m.insert_before(
    '_rebuild_content()',
    '''
    # The odds table shows live weights, so it is rebuilt on every refresh.
    if _odds_body != null:
        _rebuild_odds_body()

''')

m.save()
print("main.gd: %d operations" % m.ops)

# ---------------------------------------------------------------- goals.gd

g = Editor(os.path.join(REPO, "src", "goals.gd"))
g.sub('bits.append("%d☘" % int(r["charms"]))',
      'bits.append("%d charm(s)" % int(r["charms"]))')
g.save()
print("goals.gd: %d operations" % g.ops)
