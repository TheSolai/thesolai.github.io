#!/usr/bin/env godot-script
# Generates all game scene .tscn files programmatically
# Run with: godot --headless --script gen_scenes_godot.gd --quit
extends SceneTree

const SCENES := [
    ["uid://day1scene1",  "Day1Scene1",  "I",   "The King Who Cannot",     "day_1", "scene_1.tscn"],
    ["uid://day1scene2",  "Day1Scene2",  "I",   "Bishop Ronan",           "day_1", "scene_2.tscn"],
    ["uid://day1scene3",  "Day1Scene3",  "I",   "Queen Eormen",           "day_1", "scene_3.tscn"],
    ["uid://day2scene4",  "Day2Scene4",  "II",  "King Diarmait of Mide",  "day_2", "scene_4.tscn"],
    ["uid://day2scene5",  "Day2Scene5",  "II",  "Selbach's Son",          "day_2", "scene_5.tscn"],
    ["uid://day2scene6",  "Day2Scene6",  "II",  "The Pictish Champion",   "day_2", "scene_6.tscn"],
    ["uid://day3scene7",  "Day3Scene7",  "III", "King Selbach",           "day_3", "scene_7.tscn"],
    ["uid://day3scene8",  "Day3Scene8",  "III", "Brother Cairneach",      "day_3", "scene_8.tscn"],
    ["uid://day3scene9",  "Day3Scene9",  "III", "The Midwife",            "day_3", "scene_9.tscn"],
    ["uid://day4scene10", "Day4Scene10", "IV",  "Adomnan Reviews",        "day_4", "scene_10.tscn"],
    ["uid://day4scene11", "Day4Scene11", "IV",  "The Gift",                "day_4", "scene_11.tscn"],
    ["uid://day5scene12", "Day5Scene12", "V",   "The Curse Moves",         "day_5", "scene_12.tscn"],
    ["uid://day5scene13", "Day5Scene13", "V",   "King Fergal",             "day_5", "scene_13.tscn"],
    ["uid://day6scene14", "Day6Scene14", "VI",  "Brother Tireach",         "day_6", "scene_14.tscn"],
    ["uid://day6scene15", "Day6Scene15", "VI",  "The Widow",               "day_6", "scene_15.tscn"],
    ["uid://day6scene16", "Day6Scene16", "VI",  "Final Vote",              "day_6", "scene_16.tscn"],
    ["uid://day7scene17", "Day7Scene17", "VII", "Adomnan Final Review",    "day_7", "scene_17.tscn"],
    ["uid://day7scene18", "Day7Scene18", "VII", "The Last Entry",          "day_7", "scene_18.tscn"],
]

const GAME_SCRIPT := "res://scripts/scenes/game_scene.gd"

const C_BG       := Color(0.101961, 0.082353, 0.0627451, 1)
const C_HEADER    := Color(0.176471, 0.352941, 0.290196, 0.4)
const C_GOLD      := Color(0.788235, 0.627451, 0.188235, 1)
const C_GOLD_MID  := Color(0.627451, 0.568627, 0.439216, 1)
const C_TEXT      := Color(0.831373, 0.768627, 0.658824, 1)
const C_STATUSBAR := Color(0.0588235, 0.0509804, 0.0392157, 1)

func _init() -> void:
    var base_path := "res://scenes/"
    for data in SCENES:
        var uid: String = data[0]
        var node_name: String = data[1]
        var day_roman: String = data[2]
        var title: String = data[3]
        var folder: String = data[4]
        var fname: String = data[5]

        var scene := _create_scene(node_name, title, day_roman)
        var packed := PackedScene.new()
        packed._bundled["uid"] = uid
        packed._bundled["(connections"] = []
        packed._bundled["node_count"] = scene.get_child_count() + 1  # +1 for root
        packed._bundled["nodes"] = _flatten_scene(scene, uid)
        packed._bundled["variants"] = []
        packed._bundled["virtual_dependencies"] = []
        packed._bundled["editable_instances"] = []
        packed._bundled["gen_path"] = ""

        var out_path := base_path + folder + "/" + fname
        var err := ResourceSaver.save(packed, out_path)
        if err == OK:
            print("Saved: ", out_path)
        else:
            printerr("Failed to save: ", out_path, " error=", err)

    quit()

func _create_scene(node_name: String, title: String, day_roman: String) -> Control:
    var root := Control.new()
    root.name = node_name
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
    root.script = load(GAME_SCRIPT)

    # Background
    var bg := ColorRect.new()
    bg.name = "BG"
    bg.color = C_BG
    bg.set_anchors_preset(Control.PRESET_FULL_RECT)
    root.add_child(bg)

    # Day header
    var header := ColorRect.new()
    header.name = "DayHeader"
    header.color = C_HEADER
    header.set_anchors_preset(Control.PRESET_TOP_WIDE)
    header.size.y = 52
    root.add_child(header)

    var day_label := Label.new()
    day_label.name = "DayLabel"
    day_label.text = "DAY " + day_roman
    day_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    day_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    day_label.set_anchors_preset(Control.PRESET_FULL_RECT)
    day_label.add_theme_color_override("font_color", C_GOLD)
    day_label.add_theme_font_size_override("font_size", 22)
    header.add_child(day_label)

    var scene_title_label := Label.new()
    scene_title_label.name = "SceneTitleLabel"
    scene_title_label.text = title
    scene_title_label.set_anchors_preset(Control.PRESET_LEFT_WIDE)
    scene_title_label.offset_top = 4
    scene_title_label.size.y = 44
    scene_title_label.size.x = 576
    scene_title_label.add_theme_color_override("font_color", C_GOLD_MID)
    scene_title_label.add_theme_font_size_override("font_size", 16)
    header.add_child(scene_title_label)

    # Narrative panel
    var np := _make_panel("NarrativePanel")
    np.set_anchors_preset(Control.PRESET_TOP_WIDE)
    np.offset_bottom = 324
    root.add_child(np)

    var np_margin := _make_margin(np, 36, 20, 36, 16)
    var narrative_label := Label.new()
    narrative_label.name = "NarrativeLabel"
    narrative_label.text = "Loading..."
    narrative_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    narrative_label.add_theme_color_override("font_color", C_TEXT)
    narrative_label.add_theme_font_size_override("font_size", 21)
    np_margin.add_child(narrative_label)

    # Record panel (testimony)
    var rp := _make_panel("RecordPanel")
    rp.set_anchors_preset(Control.PRESET_CENTER_WIDE)
    rp.anchor_top = 0.0
    rp.anchor_bottom = 0.9
    root.add_child(rp)

    var rp_margin := _make_margin(rp, 36, 0, 36, 0)
    var testimony_label := RichTextLabel.new()
    testimony_label.name = "TestimonyLabel"
    testimony_label.text = "Loading testimony..."
    testimony_label.fit_content = true
    testimony_label.bbcode_enabled = false
    testimony_label.add_theme_color_override("default_color", C_TEXT)
    testimony_label.add_theme_font_size_override("normal_font_size", 21)
    testimony_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
    testimony_label.set_anchors_preset(Control.PRESET_FULL_RECT)
    testimony_label.content_size = Vector2(800, 200)
    rp_margin.add_child(testimony_label)

    var attribution_label := Label.new()
    attribution_label.name = "AttributionLabel"
    attribution_label.text = "— Character, Title"
    attribution_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
    attribution_label.add_theme_color_override("font_color", C_GOLD_MID)
    attribution_label.add_theme_font_size_override("font_size", 15)
    attribution_label.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
    rp_margin.add_child(attribution_label)

    # Decision panel (right side)
    var dp := _make_panel("DecisionPanel")
    dp.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
    dp.anchor_top = 0.9
    dp.anchor_bottom = 1.0
    dp.offset_top = 0
    root.add_child(dp)

    var dp_margin := _make_margin(dp, 24, 16, 24, 16)
    var vbox := VBoxContainer.new()
    vbox.name = "VBox"
    dp_margin.add_child(vbox)

    var classify_label := Label.new()
    classify_label.name = "ClassifyLabel"
    classify_label.text = "HOW DO YOU RECORD THIS?"
    classify_label.add_theme_color_override("font_color", C_GOLD_MID)
    classify_label.add_theme_font_size_override("font_size", 14)
    vbox.add_child(classify_label)

    var class_section := HBoxContainer.new()
    class_section.name = "ClassificationSection"
    class_section.size_flags_vertical = Control.SIZE_EXPAND_FILL
    vbox.add_child(class_section)

    var annot_section := VBoxContainer.new()
    annot_section.name = "AnnotationSection"
    annot_section.size_flags_vertical = Control.SIZE_EXPAND_FILL
    vbox.add_child(annot_section)

    var spacer := Control.new()
    spacer.name = "Spacer"
    spacer.custom_minimum_size.y = 12
    spacer.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
    vbox.add_child(spacer)

    var confirm_btn := Button.new()
    confirm_btn.name = "ConfirmBtn"
    confirm_btn.text = "CONFIRM ENTRY"
    confirm_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    confirm_btn.add_theme_color_override("font_color", C_GOLD_MID)
    confirm_btn.add_theme_font_size_override("font_size", 16)
    vbox.add_child(confirm_btn)

    # Status bar
    var sb := ColorRect.new()
    sb.name = "StatusBar"
    sb.color = C_STATUSBAR
    sb.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
    sb.offset_top = -28
    sb.size.y = 28
    root.add_child(sb)

    var status_label := Label.new()
    status_label.name = "StatusLabel"
    status_label.text = "Day 1"
    status_label.set_anchors_preset(Control.PRESET_FULL_RECT)
    status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    status_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    status_label.add_theme_color_override("font_color", C_GOLD_MID)
    status_label.add_theme_font_size_override("font_size", 13)
    sb.add_child(status_label)

    return root

func _make_panel(node_name: String) -> PanelContainer:
    var panel := PanelContainer.new()
    panel.name = node_name
    return panel

func _make_margin(parent: Node, left: int, top: int, right: int, bottom: int) -> MarginContainer:
    var m := MarginContainer.new()
    m.name = "Margin"
    m.add_theme_constant_override("margin_left", left)
    m.add_theme_constant_override("margin_top", top)
    m.add_theme_constant_override("margin_right", right)
    m.add_theme_constant_override("margin_bottom", bottom)
    parent.add_child(m)
    return m

func _flatten_scene(root: Control, uid: String) -> Array:
    # Returns array of node dicts compatible with PackedScene._bundled format
    var nodes := []
    # Root node
    nodes.append({
        "name": root.name,
        "type": root.get_class(),
        "parent": "",
        "index": 0,
        "instance_options": 0,
        "propery_list": [],
        "owner_path": uid,
        "owner": NodePath("."),
    })
    var idx := 1
    for child in root.get_children():
        idx = _flatten_child_nodes(child, root, nodes, idx)
    return nodes

func _flatten_child_nodes(node: Node, parent: Node, nodes: Array, idx: int) -> int:
    nodes.append({
        "name": node.name,
        "type": node.get_class(),
        "parent": NodePath("../" + parent.name),
        "index": idx,
        "instance_options": 0,
        "propery_list": [],
        "owner_path": "",
        "owner": NodePath("."),
    })
    idx += 1
    if node is Control:
        for child in node.get_children():
            idx = _flatten_child_nodes(child, node, nodes, idx)
    return idx
