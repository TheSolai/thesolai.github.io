#!/usr/bin/env python3
"""Generate valid Godot 4 .tscn scene files for The Scribe's Choice."""
import os

SCENES = [
    ("uid://day1scene1",  "Day1Scene1",  "I",   "The King Who Cannot",     "day_1", "scene_1.tscn"),
    ("uid://day1scene2",  "Day1Scene2",  "I",   "Bishop Ronan",           "day_1", "scene_2.tscn"),
    ("uid://day1scene3",  "Day1Scene3",  "I",   "Queen Eormen",           "day_1", "scene_3.tscn"),
    ("uid://day2scene4",  "Day2Scene4",  "II",  "King Diarmait of Mide",  "day_2", "scene_4.tscn"),
    ("uid://day2scene5",  "Day2Scene5",  "II",  "Selbach's Son",          "day_2", "scene_5.tscn"),
    ("uid://day2scene6",  "Day2Scene6",  "II",  "The Pictish Champion",   "day_2", "scene_6.tscn"),
    ("uid://day3scene7",  "Day3Scene7",  "III", "King Selbach",           "day_3", "scene_7.tscn"),
    ("uid://day3scene8",  "Day3Scene8",  "III", "Brother Cairneach",      "day_3", "scene_8.tscn"),
    ("uid://day3scene9",  "Day3Scene9",  "III", "The Midwife",            "day_3", "scene_9.tscn"),
    ("uid://day4scene10", "Day4Scene10", "IV",  "Adomnan Reviews",        "day_4", "scene_10.tscn"),
    ("uid://day4scene11", "Day4Scene11", "IV",  "The Gift",               "day_4", "scene_11.tscn"),
    ("uid://day5scene12", "Day5Scene12", "V",   "The Curse Moves",         "day_5", "scene_12.tscn"),
    ("uid://day5scene13", "Day5Scene13", "V",   "King Fergal",            "day_5", "scene_13.tscn"),
    ("uid://day6scene14", "Day6Scene14", "VI",  "Brother Tireach",        "day_6", "scene_14.tscn"),
    ("uid://day6scene15", "Day6Scene15", "VI",  "The Widow",              "day_6", "scene_15.tscn"),
    ("uid://day6scene16", "Day6Scene16", "VI",  "Final Vote",             "day_6", "scene_16.tscn"),
    ("uid://day7scene17", "Day7Scene17", "VII", "Adomnan Final Review",   "day_7", "scene_17.tscn"),
    ("uid://day7scene18", "Day7Scene18", "VII", "The Last Entry",         "day_7", "scene_18.tscn"),
]

# All nodes use anchors_preset=0 (no anchors, use offset) for the root and anchors_preset=15 (full rect) for children
# This is the safest compatible format

def tscn(uid, node_name, day_roman, scene_title):
    return f"""[gd_scene format=3 uid="{uid}"]

[ext_resource type="Script" path="res://scripts/scenes/game_scene.gd" id="1"]

[node name="{node_name}" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
color = Color(0.101961, 0.082353, 0.0627451, 1)

[node name="DayHeader" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 10
anchor_right = 1.0
offset_bottom = 52.0
grow_horizontal = 2
color = Color(0.176471, 0.352941, 0.290196, 0.4)

[node name="DayLabel" type="Label" parent="DayHeader"]
layout_mode = 1
anchors_preset = 10
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
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
offset_right = 624.0
offset_bottom = 48.0
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 16
text = "{scene_title}"

[node name="NarrativePanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 10
anchor_right = 1.0
anchor_bottom = 0.45
grow_horizontal = 2
size_flags_vertical = 4

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

[node name="RecordPanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 10
anchor_right = 1.0
anchor_bottom = 0.91
grow_horizontal = 2
size_flags_vertical = 6

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

[node name="DecisionPanel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -344.0
offset_top = -280.0
offset_right = -16.0
offset_bottom = 0.0
grow_horizontal = 0
grow_vertical = 0

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
custom_minimum_size.y = 12.0

[node name="ConfirmBtn" type="Button" parent="DecisionPanel/Margin/VBox"]
layout_mode = 2
size_flags_horizontal = 4
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 16
text = "CONFIRM ENTRY"

[node name="StatusBar" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 0.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_top = -28.0
grow_horizontal = 2
grow_vertical = 0
color = Color(0.0588235, 0.0509804, 0.0392157, 1)

[node name="StatusLabel" type="Label" parent="StatusBar"]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
theme_override_colors/font_color = Color(0.627451, 0.568627, 0.439216, 1)
theme_override_font_sizes/font_size = 13
text = "Day 1"
horizontal_alignment = 1
vertical_alignment = 1
"""

BASE = "/Users/amre/Projects/TheScribesChoice/scenes"
count = 0

for uid, node_name, day_roman, title, folder, fname in SCENES:
    path = os.path.join(BASE, folder, fname)
    content = tscn(uid, node_name, day_roman, title)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Written: {path}")
    count += 1

print(f"\nTotal: {count} scene files written.")
