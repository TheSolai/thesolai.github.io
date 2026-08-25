#!/usr/bin/env python3
"""Generate all 18 Godot scene .tscn files for The Scribe's Choice."""
import os

# ─── Scene metadata ───────────────────────────────────────────────────────────
SCENES = [
    # (uid, node_name, day_roman, title)
    ("uid://day1scene1", "Day1Scene1", "I",   "The King Who Cannot"),
    ("uid://day1scene2", "Day1Scene2", "I",   "Bishop Ronan"),
    ("uid://day1scene3", "Day1Scene3", "I",   "Queen Eormen"),
    ("uid://day2scene4", "Day2Scene4", "II",  "King Diarmait of Mide"),
    ("uid://day2scene5", "Day2Scene5", "II",  "Selbach's Son"),
    ("uid://day2scene6", "Day2Scene6", "II",  "The Pictish Champion"),
    ("uid://day3scene7", "Day3Scene7", "III", "King Selbach"),
    ("uid://day3scene8", "Day3Scene8", "III", "Brother Cairneach"),
    ("uid://day3scene9", "Day3Scene9", "III", "The Midwife"),
    ("uid://day4scene10","Day4Scene10","IV",  "Adomnán Reviews"),
    ("uid://day4scene11","Day4Scene11","IV",  "The Gift"),
    ("uid://day5scene12","Day5Scene12","V",   "The Curse Moves"),
    ("uid://day5scene13","Day5Scene13","V",   "King Fergal"),
    ("uid://day6scene14","Day6Scene14","VI",  "Brother Tíreach"),
    ("uid://day6scene15","Day6Scene15","VI",  "The Widow"),
    ("uid://day6scene16","Day6Scene16","VI",  "Final Vote"),
    ("uid://day7scene17","Day7Scene17","VII", "Adomnán's Final Review"),
    ("uid://day7scene18","Day7Scene18","VII", "The Last Entry"),
]

DAY_MAP = {
    "I":   ("day_1", ["scene_1.tscn","scene_2.tscn","scene_3.tscn"]),
    "II":  ("day_2", ["scene_4.tscn","scene_5.tscn","scene_6.tscn"]),
    "III": ("day_3", ["scene_7.tscn","scene_8.tscn","scene_9.tscn"]),
    "IV":  ("day_4", ["scene_10.tscn","scene_11.tscn"]),
    "V":   ("day_5", ["scene_12.tscn","scene_13.tscn"]),
    "VI":  ("day_6", ["scene_14.tscn","scene_15.tscn","scene_16.tscn"]),
    "VII": ("day_7", ["scene_17.tscn","scene_18.tscn"]),
}

# ─── Template ─────────────────────────────────────────────────────────────────
# Key: layout_mode=1 (anchors disabled, use offset), anchors_preset unset
# Panel containers: layout_mode=2 (full rect via anchors_preset=15)

SCENE_TEMPLATE = """[gd_scene format=3 uid="{uid}"]

[ext_resource type="Script" path="res://scripts/scenes/game_scene.gd" id="1"]

[node name="{node_name}" type="Control"]
layout_mode = 1
anchors_preset = 0
offset_right = 1280.0
offset_bottom = 720.0
grow_horizontal = 1
grow_vertical = 1
script = ExtResource("1")

# ── Background ────────────────────────────────────────────────────────────────
[node name="BG" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 0
offset_right = 1280.0
offset_bottom = 720.0
color = Color(0.101961, 0.082353, 0.0627451, 1)

# ── Day header bar ─────────────────────────────────────────────────────────────
[node name="DayHeader" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 0
offset_top = 0.0
offset_right = 1280.0
offset_bottom = 52.0
color = Color(0.176471, 0.352941, 0.290196, 0.4)

[node name="DayLabel" type="Label" parent="DayHeader"]
layout_mode = 1
anchors_preset = 0
offset_right = 1280.0
offset_bottom = 52.0
theme_override_colors/font_color = Color(0.788235, 0.627451, 0.188235, 1)
theme_override_font_sizes/font_size = 22
text = "DAY {day_roman}"
horizontal_alignment = 1
vertical_alignment = 1

[node name="SceneTitleLabel" type="Label" parent="DayHeader"]
layout_mode = 1
anchors_preset = 0
offset_left = 24.0
offset_top = 4.0
offset_right = 400.0
offset_bottom = 48.0
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 16
text = "{scene_title}"

# ── Narrative panel ────────────────────────────────────────────────────────────
[node name="NarrativePanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 0
offset_top = 60.0
offset_right = 880.0
offset_bottom = 330.0

[node name="Margin" type="MarginContainer" parent="NarrativePanel"]
layout_mode = 2
theme_override_constants/margin_left = 36
theme_override_constants/margin_top = 20
theme_override_constants/margin_right = 36
theme_override_constants/margin_bottom = 16

[node name="NarrativeLabel" type="Label" parent="NarrativePanel/Margin"]
layout_mode = 2
theme_override_colors/font_color = Color(0.831373, 0.768627, 0.658824, 1)
theme_override_font_sizes/font_size = 21
text = "Loading..."
autowrap_mode = 2

# ── Record panel (testimony) ──────────────────────────────────────────────────
[node name="RecordPanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 0
offset_top = 338.0
offset_right = 880.0
offset_bottom = 656.0

[node name="Margin" type="MarginContainer" parent="RecordPanel"]
layout_mode = 2
theme_override_constants/margin_left = 36
theme_override_constants/margin_right = 36

[node name="TestimonyLabel" type="RichTextLabel" parent="RecordPanel/Margin"]
layout_mode = 2
size_flags_vertical = 6
theme_override_colors/default_color = Color(0.831373, 0.768627, 0.658824, 1)
theme_override_font_sizes/normal_font_size = 21
text = "Loading testimony..."
fit_content = true
bbcode_enabled = false

[node name="AttributionLabel" type="Label" parent="RecordPanel/Margin"]
layout_mode = 2
size_flags_vertical = 1
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 15
text = "— Character, Title"
horizontal_alignment = 2

# ── Decision panel ────────────────────────────────────────────────────────────
[node name="DecisionPanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 0
offset_left = 896.0
offset_top = 338.0
offset_right = 1264.0
offset_bottom = 692.0

[node name="Margin" type="MarginContainer" parent="DecisionPanel"]
layout_mode = 2
theme_override_constants/margin_left = 24
theme_override_constants/margin_top = 16
theme_override_constants/margin_right = 24
theme_override_constants/margin_bottom = 16

[node name="VBox" type="VBoxContainer" parent="DecisionPanel/Margin"]
layout_mode = 2

[node name="ClassifyLabel" type="Label" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 14
text = "HOW DO YOU RECORD THIS?"

[node name="ClassificationSection" type="HBoxContainer" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
size_flags_vertical = 4

[node name="AnnotationSection" type="VBoxContainer" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
size_flags_vertical = 6

[node name="Spacer" type="Control" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
size_flags_vertical = 1
custom_minimum_size.y = 12

[node name="ConfirmBtn" type="Button" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
size_flags_horizontal = 4
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 16
text = "CONFIRM ENTRY"

# ── Status bar ────────────────────────────────────────────────────────────────
[node name="StatusBar" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 0
offset_top = 692.0
offset_right = 1280.0
offset_bottom = 720.0
color = Color(0.0588235, 0.0509804, 0.0392157, 1)

[node name="StatusLabel" type="Label" parent="StatusBar"]
layout_mode = 1
anchors_preset = 0
offset_right = 1280.0
offset_bottom = 28.0
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 13
text = "Day 1 — Entries: 0  |  S: 0  C: 0  D: 0"
horizontal_alignment = 1
vertical_alignment = 1
"""

BASE = "/Users/amre/Projects/TheScribesChoice/scenes"

for uid, node_name, day_roman, scene_title in SCENES:
    day_folder, files = DAY_MAP[day_roman]
    # Find which index this is within the day
    day_scenes = [s for _, _, d, _ in SCENES if d == day_roman]
    idx_in_day = day_scenes.index((uid, node_name, day_roman, scene_title))
    fname = files[idx_in_day]

    content = SCENE_TEMPLATE.format(
        uid=uid,
        node_name=node_name,
        day_roman=day_roman,
        scene_title=scene_title,
    )
    path = os.path.join(BASE, day_folder, fname)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Written: {path}")

print(f"\nTotal: {len(SCENES)} scene files written.")
