# THE SCRIBE'S CHOICE
## Game Design Document — Version 1.0

---

## DOCUMENT INFORMATION

| Field | Value |
|-------|-------|
| **Project Name** | The Scribe's Choice |
| **Genre** | Narrative decision game / interactive fiction |
| **Target Platforms** | iOS, Android, Windows (Web / desktop) |
| **Engine** | Godot 4.x (recommended) — HTML5 export for web; native export for mobile/desktop |
| **Document Status** | v1.1 — APPROVED — ALL DECISIONS CONFIRMED |
| **Author** | Dross |
| **Date** | AD 2026 — August 24, 13:16 — The hour the law was ratified |

---

## 1. GAME OVERVIEW

### 1.1 One-Line Pitch

*You are the scribe who records the oaths at the Synod of Birr, AD 697. Every name you write binds a soul. Every omission damns one. This is the story of the law that tried to protect the innocent — and the hand that wrote it into being.*

### 1.2 Concept Summary

The Scribe's Choice is a single-player narrative decision game set at the Synod of Birr, Ireland, AD 697. The player takes the role of a cloistered scribe tasked with recording the oaths of kings, bishops, and warriors who have gathered to ratify the Lex Innocentium — Adomnán's Law, which demands protection for women, children, and clerics in warfare.

Over seven days at the synod, the player meets approximately 18 characters. Each presents their testimony, their doubts, their ambitions, or their dissent. The player records each one in the ledger — choosing how to classify them (Supporter, Dissenter, Conditional, Exempt), and annotating each entry with a brief scribe's note that reflects the player's own moral reading of the testimony.

The player's ledger is reviewed at the end by a dying Adomnán. Every choice accumulates. The final state of the ledger determines which of four epilogues the player receives — and whether the Lex Innocentium survives, falters, twists, or collapses.

### 1.3 Core Feel / Player Experience

- **Tense, quiet, deliberate.** No combat, no timer, no action. Just the weight of words.
- **Moral exhaustion.** Every choice is defensible. Every choice has a cost.
- **Satisfying documentation.** The act of recording — stamping, annotating, filing — should feel tactile and meaningful.
- **Historical texture without being a textbook.** Players will leave knowing more about 7th-century Ireland, but they won't feel taught.

### 1.4 Target Audience

- Players who enjoyed Papers Please, Return of the Obra Dinn, or similar narrative/documentary games
- Fans of historical fiction and early medieval Irish history
- Players who enjoy moral dilemmas with no clean answers
- Age rating: 12+ (mild thematic content — mentions of wartime violence against civilians, but no graphic depiction)

### 1.5 Target Platform Summary

| Platform | Priority | Export Target |
|----------|----------|---------------|
| iOS | Primary | Godot iOS export / web wrapper |
| Android | Primary | Godot Android export / web wrapper |
| Windows | Secondary | Godot Windows export |
| Web (browser) | Tertiary | HTML5 / WebGL via Godot |

**Note on web wrapper:** For iOS/Android, consider wrapping the HTML5 build in a lightweight native shell (e.g., Capacitor or Godoto's built-in mobile export). This allows a single codebase while meeting App Store / Play Store distribution requirements.

---

## 2. VISUAL DESIGN

### 2.1 Art Style

**Primary Reference:** Illuminated manuscript (Book of Kells aesthetic) stripped of colour, cold and claustrophobic. Not a "pretty" medieval game — a tense, candlelit one.

**Key principles:**
- High contrast between dark backgrounds and warm text
- Celtic knotwork used sparingly — only for borders and frames
- Text is the primary visual element — typography carries the design
- No character portraits — characters are described in prose, not shown
- Subtle ink-bleed and candlelight flicker effects on text

### 2.2 Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Background (primary) | Aged vellum, near-black | `#1a1510` |
| Background (panel) | Dark parchment | `#211a12` |
| Primary text | Faded gold ink | `#d4c4a8` |
| Headers / illuminated text | Illuminated gold | `#c9a030` |
| Celtic accent (borders) | Celtic green | `#2d5a4a` |
| Danger / curse marker | Muted dried blood | `#6b3030` |
| Dissenter marker | Dark ash grey | `#4a4040` |
| Conditional marker | Muted amber | `#7a6030` |
| Supporter marker | Faded verdigris | `#3a5a4a` |
| UI borders | Dark oak brown | `#3d2f1e` |
| Candle glow (effect) | `#ff9940` at 5-10% opacity |

### 2.3 Typography

| Element | Font | Style |
|---------|------|-------|
| Game title | MedievalSharp or Cinzel Decorative | All caps, gold |
| Major headers (Day I, Day II...) | Uncial BT or JSL Ancient | All caps, gold |
| Scene narrative text | Crimson Text | Body, cream |
| Character testimony | Crimson Text Italic | First-person, slightly warmer cream |
| Ledger entries | IM Fell English | Slightly irregular, handwritten feel |
| UI labels / status | IM Fell English SC | Small caps, muted gold |
| Annotations (player's scribe notes) | Cormorant Garamond | Italic, distinctive — player's voice |

**Font loading strategy:** Use Google Fonts loaded at runtime. Fallback to system serif (Georgia) if offline. All fonts must support Latin Extended A (for Irish names with fadas: Á, É, Í, Ó, Ú, etc.).

### 2.4 UI Components

#### 2.4.1 Title Screen
- Full Celtic knot border (SVG, animated subtle glow)
- Title in illuminated uncial caps
- Subtitle: *"A game of oaths, ink, and consequence"*
- Single button: "BEGIN" styled as a wax seal
- Settings icon (gear) in corner — audio on/off, high-contrast mode
- Ambient candle-flicker animation on border

#### 2.4.2 Main Game Screen (single-screen, no scrolling)
```
┌─────────────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════════════╗ │
│  ║        CELTIC KNOT BORDER (decorative header)     ║ │
│  ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│           ◆ DAY I ◆                                     │
│      "The field. The mother. The oath."                │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ SCENE NARRATIVE (2-4 lines of prose)              │ │
│  │ The synod hall is full. You have been given       │ │
│  │ the quill. The ink is wet. You wait.             │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ THE RECORD                                         │ │
│  │                                                    │ │
│  │ "I cannot swear it. My warriors would depose me   │ │
│  │ within the fortnight. I would be dead, and my     │ │
│  │ family with me."                                  │ │
│  │                                                    │ │
│  │ — King Fogartach of Uí Néill                     │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ HOW DO YOU RECORD THIS?                          │   │
│  │                                                  │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │   │
│  │ │  SUPPORTER  │ │CONDITIONAL │ │  DISSENTER │ │   │
│  │ │  [wax seal] │ │  [wax seal] │ │  [wax seal]│ │   │
│  │ └─────────────┘ └─────────────┘ └────────────┘ │   │
│  │                                                  │   │
│  │ ANNOTATION:                                       │   │
│  │ ┌─────────────────────────────────────────────┐ │   │
│  │ │ "Select a scribe's note..."                 │ │   │
│  │ └─────────────────────────────────────────────┘ │   │
│  │  [CONFIRM ENTRY]                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ── Day 1 of 7 ── Oaths recorded: 2 ── Curses: 0 ──   │
└─────────────────────────────────────────────────────────┘
```

#### 2.4.3 Annotation Picker
Appears as a dropdown or radial selection of 3 scribe's note options after a Supporter/Dissenter/Conditional choice is made. Each annotation is a short phrase in the player's voice:
- *"Spoke from fear, not malice."*
- *"The law matters more than his comfort."*
- *"He would break the oath the moment his warriors asked."*

#### 2.4.4 Ledger Screen (accessible via menu)
A read-only display of all recorded entries so far, in the format:
```
King Fogartach of Uí Néill — Day I
Classification: CONDITIONAL
Scribe's note: "Spoke from fear, not malice."
```
Scrollable list. Shows the accumulating weight of decisions.

#### 2.4.5 Epilogue Screen
Full-page illuminated manuscript style.
- The player's final ledger summarised
- Adomnán's verdict on the law and on the scribe's work
- One of four epilogue texts (see Section 4)
- "Play Again" button — styled as turning the page

### 2.5 Animation & Motion

| Animation | Duration | Easing | Description |
|-----------|----------|--------|-------------|
| Scene text fade-in | 400ms | ease-out | New scene narrative types in line by line |
| Ledger entry stamp | 200ms | ease-in | Wax seal press effect on confirmation |
| Annotation hover | 150ms | ease-out | Gold underline bleeds like ink in water |
| Candle flicker (ambient) | 2000ms | random | Subtle opacity oscillation on border glow |
| Screen transition (scene change) | 600ms | ease-in-out | Cross-fade between scenes |
| Ink bleed (title screen) | 800ms | ease-out | Text appears as if ink is spreading |

### 2.6 Audio (Placeholder Spec)

| Sound | Type | Description |
|-------|------|-------------|
| Quill scratch | Ambient loop | Soft, continuous — subtle background |
| Ink stamp | SFX | Satisfying press sound on ledger confirmation |
| Page turn | SFX | Soft paper rustle for scene transitions |
| Candle crackle | Ambient loop | Very subtle background |
| Curse tone | SFX | Low, cold — plays when a curse is invoked |
| Adomnán's voice | VO (endgame) | Low, reverent — for epilogue narration |

**Note:** Audio is placeholder in v1.0. Final audio design deferred to post-MVP.

---

## 3. GAME STRUCTURE & FLOW

### 3.1 State Machine

```
TITLE
  │
  ▼
PROLOGUE (1 scene — Rónnat's battlefield testimony)
  │
  ▼
DAY_I_SCENE_1 ──► DAY_I_SCENE_2 ──► DAY_I_SCENE_3
  │
  ▼
DAY_II_SCENE_1 ──► DAY_II_SCENE_2 ──► ... ──► DAY_VII_SCENE_N
  │
  ▼
ADOMNÁN'S REVIEW (3 scenes — ledger shown, choices reflected)
  │
  ▼
EPILOGUE (one of four, based on accumulated state)
  │
  ▼
CREDITS / PLAY AGAIN
```

### 3.2 Scene Structure

Each scene consists of:
1. **Scene number and title** (Day + scene count)
2. **Narrative text** (2-4 lines of context prose)
3. **The Record** — the character's testimony, presented in their voice
4. **Decision** — classify the character (Supporter / Conditional / Dissenter)
5. **Annotation** — select a scribe's note from 3 options
6. **Confirmation** — ledger entry is stamped and recorded
7. **Outcome hint** (subtle — a brief line showing consequence)

### 3.3 Scene Inventory

**PROLOGUE** (1 scene)
1. The Battlefield — Rónnat and Adomnán find the bodies. Rónnat speaks. You record your first entry: her testimony.

**DAY I — "The Gathering"** (3 scenes)
2. King Fogartach of Uí Néill — Cannot swear without being deposed. Fear or sincerity?
3. Bishop Ronan of Armagh — Supports the law, but demands it protect church lands, not just persons.
4. Queen Eormen of the Ulaidh — Will swear if her daughters are named specifically as protected.

**DAY II — "The Dissenting Voices"** (3 scenes)
5. King Diarmait of Mide — Openly refuses. "The law of women is no law at all."
6. A young warrior, unnamed — His king speaks for him. You can record the king... or the warrior.
7. The Pictish Champion — Speaks no Irish. An interpreter translates. What if the interpreter mistranslates?

**DAY III — "The Price of Signatures"** (3 scenes)
8. King Selbach of the Déisi — Will sign, but wants his cattle fine from a previous dispute forgiven.
9. A cleric, Brother Cairneach — Brings testimony of a massacre that happened six months ago. Names names. Do you record all the names, or soften some?
10. A woman from the western islands — Not invited to the synod. She has come anyway. She wants to speak. Do you let her?

**DAY IV — "Adomnán Tests the Ledger"** (2 scenes)
11. Adomnán reviews the first three days. He asks you to explain Fogartach. He asks about Diarmait.
12. A king who was Conditional on Day I has sent a gift. A valuable one. Does it affect your record?

**DAY V — "The Curse is Spoken"** (2 scenes)
13. A king who was recorded as Supporter has violated the law. You hear of it from a messenger. The curse activates — symbolically. What do you write in the margin?
14. Another dissenter. But this one offers you something. A position. After the synod. A future.

**DAY VI — "The Ledger Grows Heavy"** (3 scenes)
15. Adomnán's own secretary. A question: has Adomnán ever asked you to alter a record?
16. A king's widow. Her husband died during the synod week. His oath stands. Or does it?
17. The final vote. Every king present. The ledger is full. The ink is dry.

**DAY VII — "The Law Stands"** (2 scenes)
18. Adomnán reviews the complete ledger. He asks you three questions about your choices.
19. The closing ceremony. The oaths are bound. The curse is spoken on dissenters. Your last decision: how do you date the final entry?

**EPILOGUE TRIGGER** (after Day VII)
Adomnán's verdict scenes (3 scenes): The ledger is read aloud. Your annotations are quoted. Your choices are weighed. One of four endings is selected.

### 3.4 Endings

| Ending | Condition | Description |
|--------|-----------|-------------|
| **The Law Stands** | ≥70% genuine supporters; ≤2 falsified entries; no curses broken | The Lex Innocentium passes with genuine backing. Adomnán calls your ledger "true." |
| **The Law Falters** | 40-69% supporters; 3-5 falsifications | The law passes on paper. Adomnán suspects the record is imperfect. The law endures, but weakly. |
| **The Law Twisted** | Any condition where support >70% but falsifications >6 | The letter of the law stands. The spirit is corrupted. Adomnán weeps. |
| **You Are Exposed** | >5 falsified entries OR >2 curses broken | Your falsifications are discovered. You are cast from the synod. The law collapses under the weight of your hand. |

---

## 4. FEATURES & MECHANICS

### 4.1 Core Loop

**See scene → Read testimony → Classify character → Annotate → Confirm → See outcome hint**

The loop is deliberately simple. The complexity comes from the moral weight of each decision, not from mechanical difficulty.

### 4.2 The Classification System

Every character is classified as one of:

| Classification | Description | Mechanical Weight |
|---------------|-------------|-------------------|
| **SUPPORTER** | Bound by oath to uphold the Lex | Counted toward law's legitimacy |
| **CONDITIONAL** | Swears with conditions, reservations, or limitations | Partial credit; conditions may be exploited |
| **DISSENTER** | Refuses to swear; may be cursed | Counted against; curse may activate if dissenter is later harmed |

**The falsification mechanic:** The player may record a Conditional as a Supporter, or a Dissenter as a Conditional, etc. This is never flagged as "wrong" by the game — but it is tracked. Adomnán's review at the end will reference patterns in your ledger. The game does not punish falsification mechanically — it judges it narratively.

### 4.3 The Annotation System

After classifying a character, the player selects one of three scribe's notes (annotations). These are short phrases that convey the player's moral interpretation of the testimony:

**Example options for King Fogartach:**
- *"Fear, not malice. He would keep the oath if he could."* (lenient)
- *"He cannot or will not. These are not the same."* (neutral)
- *"A convenient fear. I do not believe him."* (harsh)

Annotations are recorded in the ledger alongside the classification. They are read back at the end. The player's annotations reveal their character — lenient, harsh, pragmatic, idealistic. The annotations do not affect the mechanical outcome, but they shape Adomnán's commentary and the epilogue tone.

### 4.4 The Curse Mechanic

The curse is atmospheric, not mechanical. When a character classified as DISSENTER is mentioned again (e.g., harmed, killed, humiliated), the narrative notes it. The ledger may mark it: *"And the curse moved, as it was written."* This is not a game event — it is prose. The player chooses nothing here. The curse simply... happens. As Adomnán promised it would.

**The broken curse:** If a character classified as SUPPORTER violates the law, the narrative notes: *"And the oath was broken, as it was written."* The player must choose what to write in the margin — or whether to write anything at all. This is the game's most significant decision type.

### 4.5 Adomnán's Review (Endgame)

At the end of Day VII, before the epilogue, Adomnán reviews the ledger. He reads selected annotations aloud. He asks three questions:

1. "Why did you record [Name] as [Classification]?"
2. "What weight do you give to a king's fear?"
3. "Is this ledger... true?"

The player does not answer in words — they are shown their own annotations and asked to confirm or revise one. This is a reflective moment, not a quiz. There are no wrong answers. But the choice shapes the epilogue tone.

### 4.6 Persistence & Save System

- Game state is auto-saved at the end of each scene
- A single save slot + autosave (overwrites autosave each scene)
- No cloud save in v1.0
- On app resume: if mid-scene, return to that scene; if between scenes, return to start of current day

### 4.7 Settings

| Setting | Options | Default |
|---------|---------|---------|
| Audio volume | 0-100% slider | 50% |
| Music on/off | Toggle | On |
| SFX on/off | Toggle | On |
| High contrast mode | Toggle | Off |
| Text size | Small / Medium / Large | Medium |

---

## 5. TECHNICAL SPECIFICATION

### 5.1 Engine: Godot 4.x

**Rationale:**
- Cross-platform export (iOS, Android, Windows, HTML5) from single codebase
- Excellent 2D rendering with TextLabel and RichTextLabel for typography-heavy games
- Built-in scene system maps cleanly to game structure
- Lightweight — suitable for mobile
- Free, open-source (no licensing cost)
- GDscript is approachable for iteration

### 5.2 Architecture

```
res://
├── scenes/
│   ├── title_screen.tscn
│   ├── main_game.tscn          # Single persistent scene
│   ├── prologue.tscn           # Embedded as a scene within main_game
│   ├── day_*.tscn              # Day scenes
│   ├── epilogue.tscn
│   ├── ledger_screen.tscn
│   └── ui/
│       ├── scene_panel.tscn
│       ├── record_panel.tscn
│       ├── decision_panel.tscn
│       ├── annotation_picker.tscn
│       ├── wax_seal_button.tscn
│       └── status_bar.tscn
├── scripts/
│   ├── game_manager.gd        # State machine, scene transitions
│   ├── ledger.gd             # Ledger data structure
│   ├── scene_data.gd         # Scene definitions (resource)
│   ├── narrative_data.gd     # All text content (resource)
│   └── ui/
│       ├── annotation_picker.gd
│       └── status_bar.gd
├── resources/
│   ├── scenes.tres            # All scene data as Godot Resource
│   └── annotations.tres      # All annotation options
├── fonts/
│   ├── MedievalSharp.ttf
│   ├── CrimsonText-Regular.ttf
│   ├── CrimsonText-Italic.ttf
│   ├── IM Fell English Regular.ttf
│   └── (Google Fonts downloaded for offline use)
├── audio/
│   ├── quill_loop.ogg
│   ├── ink_stamp.wav
│   ├── page_turn.wav
│   └── curse_tone.wav
├── fonts/
│   └── (see above)
└── project.godot
```

### 5.3 Data Structure

**Game State (singleton):**
```gdscript
extends Node

var current_day: int = 0
var current_scene: int = 0
var ledger: Array[LedgerEntry] = []
var annotations_used: Array[String] = []
var falsifications: int = 0
var curses_activated: int = 0
var adomnan_questions_answered: Array[int] = []

class LedgerEntry:
    var character_name: String
    var character_title: String
    var day: int
    var classification: String  # SUPPORTER / CONDITIONAL / DISSENTER
    var annotation: String
    var was_falsified: bool = false
```

**Scene Data (resource):**
```gdscript
class SceneData:
    var id: String
    var day: int
    var scene_number: int
    var narrative: String
    var character_name: String
    var character_title: String
    var testimony: String
    var options: Array[DecisionOption]

class DecisionOption:
    var classification: String
    var annotation_options: Array[String]  # 3 options
    var outcome_hint: String
```

### 5.4 Export Configuration

| Platform | Godot Export Template | Notes |
|----------|---------------------|-------|
| HTML5 | WebGL 2.0 | Primary web; works in browser without install |
| iOS | XCode project → IPA | Requires Mac with XCode for final build |
| Android | APK / AAB | Requires Android SDK for build |
| Windows | EXE (NSIS installer) | Standard desktop install |

### 5.5 Performance Targets

| Metric | Target |
|--------|--------|
| Load time (HTML5) | <3 seconds on 4G |
| Load time (mobile native) | <1.5 seconds cold start |
| Frame rate | Stable 60fps on iPhone 12 / mid-range Android |
| App size (mobile) | <80MB |
| Memory usage | <150MB RAM |

### 5.6 Platform-Specific Notes

**iOS:**
- Use Godot's iOS export → XCode project → Archive → App Store Connect
- Requires Apple Developer account ($99/year)
- Safe area handling for notch devices (Godot handles automatically in 4.x)
- No Game Center / achievements in v1.0

**Android:**
- Use Godot's Android export → APK or AAB for Play Store
- Requires Google Play Developer account ($25 one-time)
- APK for direct download; AAB for Play Store submission
- No Google Play Games achievements in v1.0

**Windows:**
- Use Godot's Windows export → EXE + optional NSIS installer
- No Steam integration in v1.0
- No installer required — portable EXE works

---

## 6. CONTENT — FULL TEXT SUMMARY

### 6.1 Scene Scripts

All scene text will be written in full as part of the production phase. The following is a structural summary of all 19 scenes:

| # | Day | Scene Name | Character | Core Tension |
|---|-----|------------|-----------|--------------|
| 0 | — | The Battlefield | Rónnat | Tutorial: record a mother's testimony |
| 1 | I | The King Who Cannot | Fogartach of Uí Néill | Fear vs. sincerity |
| 2 | I | The Bishop's Condition | Bishop Ronan of Armagh | Expanding the law's scope |
| 3 | I | The Named Daughters | Queen Eormen of Ulaidh | Personal guarantee vs. universal law |
| 4 | II | The Open Dissenter | Diarmait of Mide | Misogyny as open position |
| 5 | II | The Unnamed Warrior | (warrior, no name) | King speaks for subject — record whom? |
| 6 | II | The Interpreter | Pictish Champion | Translation as interpretation |
| 7 | III | The Price of the Signature | Selbach of Déisi | Bribery or fair dealing? |
| 8 | III | The Massacre Names | Brother Cairneach | Full truth or protective mercy? |
| 9 | III | The Uninvited Woman | (woman from western islands) | Gatekeeping the synod itself |
| 10 | IV | Adomnán Reviews I | (Adomnán) | First reckoning |
| 11 | IV | The Gift | (messenger) | Does the gift change anything? |
| 12 | V | The Curse Moves | (messenger) | A supporter breaks the oath |
| 13 | V | The Future Offer | (dissenting king) | A position after the synod |
| 14 | VI | The Secretary's Question | (Adomnán's secretary) | Did Adomnán ask for changes? |
| 15 | VI | The Widow | (widow of dead king) | Does death release or bind? |
| 16 | VI | The Final Vote | (all remaining) | The ledger is full |
| 17 | VII | Adomnán's Final Review | (Adomnán) | Three questions |
| 18 | VII | The Last Entry | (the scribe) | How do you date the end? |

### 6.2 Character List

| Name | Role | Disposition |
|------|------|-------------|
| Rónnat | Mother of Adomnán | Inspiration (not classified) |
| Adomnán | Abbot of Iona | Lawgiver (not classified) |
| King Fogartach of Uí Néill | King | Conditional |
| Bishop Ronan of Armagh | Bishop | Supporter (with conditions) |
| Queen Eormen of Ulaidh | Queen | Conditional |
| King Diarmait of Mide | King | Dissenter |
| The Pictish Champion | Foreign warrior | Supporter (uncertain) |
| King Selbach of Déisi | King | Conditional |
| Brother Cairneach | Cleric | Witness |
| The Woman from the Western Isles | Uninvited guest | Not classified |
| Adomnán's Secretary | Cleric | Questioner |
| The Widow | Widow | Not classified |

### 6.3 Annotation Library (per character, 3 options each)

Full annotation text to be written during production. Each annotation has a tone: LENIENT / NEUTRAL / HARSH. The player's annotation history shapes Adomnán's commentary and epilogue tone.

---

## 7. ART & ASSET PLAN

### 7.1 Required Assets

| Asset | Type | Count | Notes |
|-------|------|-------|-------|
| Celtic knot border (title) | SVG | 1 | Animated glow; full-screen frame |
| Celtic knot corner pieces | SVG | 4 | Reusable — corners for panels |
| Wax seal (Supporter) | SVG | 1 | Green-grey; used as button |
| Wax seal (Conditional) | SVG | 1 | Amber; used as button |
| Wax seal (Dissenter) | SVG | 1 | Dark ash; used as button |
| Parchment texture | PNG (seamless) | 1 | Subtle grain; used as panel backgrounds |
| Quill cursor | SVG / PNG | 1 | Custom cursor on interactive elements |
| Candle flicker (ambient) | CSS animation | — | Part of border animation |

### 7.2 No Character Portraits

This is deliberate. The game is about text, testimony, and the act of recording. Character is conveyed through prose, not imagery. This also avoids the production cost and cultural sensitivity issues of depicting real historical figures.

### 7.3 Celtic Knot Border Specification

The title screen border and key panel frames use Celtic knotwork. This should be generated as SVG with:
- Path-based knot pattern (Celtic weave style)
- Subtle CSS animation: glow pulses slowly (3-5 second cycle)
- Color: Celtic green (`#2d5a4a`) with gold highlights (`#c9a030`)

If hand-drawing the knot is not feasible, a procedural SVG generation script can create a serviceable knot pattern.

---

## 8. CONFIRMED DECISIONS

| Decision | Confirmed Value | Source |
|---------|----------------|--------|
| **Audio — Music** | Full implementation. Dross composes. Method: take public domain melodies (nursery rhymes, Irish folk tunes) and transform into atmospheric, unsettling, "creepy AF" soundscapes. See Section 8a. | Amre, 2026-08-24 |
| **Audio — SFX** | Full implementation alongside music. | Confirmed |
| **Monetization** | One-time purchase (OTP). No IAP, no ads. | Amre, 2026-08-24 |
| **Localization** | English only in v1.0. Irish-language option deferred to v1.1. | Amre, 2026-08-24 |
| **Distribution — Primary** | Steam (Windows/macOS) + App Store (iOS). | Amre, 2026-08-24 |
| **Distribution — Secondary** | Google Play Store — deferred post-v1.0 launch. | |
| **Engine** | Godot 4.x | Confirmed |
| **Platforms** | iOS, Android, Windows | Confirmed |

---

## 8a. MUSIC DESIGN — "NURSERY RHYMES MADE CREEPY AF"

### Concept
The soundtrack is a core part of the game's identity. Every track takes a recognisable melody — public domain nursery rhymes and traditional Irish folk tunes — and reconstructs it as something unsettling, ancient, and atmospheric. Familiar enough to be recognised. Wrong enough to be disturbing.

### Source Material (all public domain)
- Traditional Irish folk melodies (no copyright)
- Public domain nursery rhymes with known melodies (e.g., "London Bridge," traditional lullabies)
- Plainchant and Gregorian chant fragments (public domain)
- Carolan-era harp tunes (public domain)

### Transformation Techniques
1. **Key shift** — Move melodies from major to minor. Lullabies become dirges.
2. **Time stretching** — Slow to 0.7x or 0.5x. Familiar becomes dreamlike.
3. **Reverb and decay** — Long reverb tails. Sounds like they are coming from a stone hall.
4. **Layered dissonance** — Sustained drone beneath the melody, slightly detuned. Enough to create unease without conscious notice.
5. **Partial reverse** — Brief reversed fragments at phrase ends. Like memory failing.
6. **Whispered vocals** — Faint whispered vocals (original lyrics or wordless) underneath. Barely audible.
7. **Breaking** — Wrong notes, skipped phrases, silences where melody should continue.

### Track Inventory

| Track | Source Melody | Scene Use |
|-------|-------------|-----------|
| `birr_main_theme` | Traditional Irish lullaby, slowed + minor key | Title screen |
| `the_field` | Hymn melody, reversed fragments | Prologue: The Battlefield |
| `oath_shown` | "London Bridge" in minor, with drone | Supporter recorded |
| `conditional_shown` | Same melody, slower, more reverb | Conditional recorded |
| `curse_shown` | Nursery rhyme, distorted, wrong notes | Dissenter recorded |
| `adomnán_theme` | Plainchant fragment, slow reverb | Adomnán scenes |
| `the_ledger` | Carolan harp tune, gentle but cold | Ledger review |
| `the_law_holds` | Lullaby restored, warm reverb | Epilogue: Law Stands |
| `the_law_falters` | Same lullaby, wrong notes, slowing | Epilogue: Law Falters |
| `the_law_twisted` | Lullaby played backwards in background | Epilogue: Law Twisted |
| `you_are_exposed` | Silence with wrong note every 10 seconds | Epilogue: Exposed |

### Ambient Layers
- `candle_ambient` — Crackling fire, distant wind. Loops during gameplay.
- `quill_ambient` — Faint quill scratching on vellum. Loops during scene text.

### Mood Reference
- *Amnesia: The Dark Descent* sound design
- *Lost in Stress* by Blackbird
- Zbigniew Preisner's *Secret Garden* compositions
- "London Bridge" played slowly on harpsichord with wrong notes

### Technical
- Format: MP3 (320kbps) for platforms; OGG for Godot
- Godot audio buses: Music / SFX / Ambient
- All tracks loop seamlessly where applicable

---

## 8c. APPROVAL SIGN-OFF

All five open questions answered by Amre on 2026-08-24 via Telegram.

| # | Question | Confirmed Answer |
|---|----------|-----------------|
| 1 | Who composes music? | Dross composes. Public domain melodies (nursery rhymes, Irish folk, plainchant) transformed into unsettling atmospheric soundscapes. |
| 2 | Monetization? | One-time purchase (OTP). No IAP. No ads. |
| 3 | Localization? | English only in v1.0. Irish-language option deferred to v1.1. |
| 4 | Distribution? | Steam (Windows/macOS) + App Store (iOS) as primary. Google Play Store deferred post-v1.0. |
| 5 | Platforms? | Godot 4.x — single codebase, iOS/Android/Windows/HTML5 exports. |

All seven GDD approval items confirmed:
- [x] Concept approved
- [x] Visual direction approved
- [x] Game structure and endings approved
- [x] Core mechanics approved
- [x] Engine (Godot 4.x) approved
- [x] Platform targets confirmed (Steam + App Store)
- [x] Open questions answered

**STATUS: APPROVED FOR PRODUCTION.**

---

## 8b. REVISED COST ESTIMATE

| Item | Cost |
|------|------|
| Godot Engine | Free |
| Music (Dross composes) | Free |
| SFX (foley + free libraries) | Free |
| Celtic knot SVG assets | Low |
| Apple Developer account | $99/year |
| Steam Direct | $100 one-time |
| **Total external cost** | **~$200** |

The game can be made essentially for free. This is the optimal path.

---

## 8. PRODUCTION ESTIMATE

### 8.1 Phases

| Phase | Description | Deliverables |
|-------|-------------|--------------|
| **Phase 1: Foundation** | Engine setup, project structure, basic UI scaffolding | Empty shell project; builds and runs on all platforms |
| **Phase 2: Core Loop** | Single scene implementation (Day I, Scene 1) | Fully working first scene with all UI and audio |
| **Phase 3: Content** | All 18 scenes written and implemented | Complete game content, all paths tested |
| **Phase 4: Polish** | Animations, audio, font polish, edge cases | Polished build |
| **Phase 5: Platform Build** | iOS, Android, Windows builds | Submittable builds for all platforms |

### 8.2 Rough Timeline Estimate

| Phase | Estimated Time |
|-------|---------------|
| Phase 1 (Foundation) | 1-2 weeks |
| Phase 2 (Core Loop) | 2-3 weeks |
| Phase 3 (Content) | 4-6 weeks |
| Phase 4 (Polish) | 1-2 weeks |
| Phase 5 (Platform Build + Submission) | 2-3 weeks |

**Total: approximately 10-15 weeks for a solo developer or small team.**

### 8.3 Open Questions (Require Amre's Decision Before Production)

1. **Audio:** Full audio implementation in v1.0, or placeholder silence?
2. **Monetization:** Free-to-play with no IAP? One-time purchase? Ad-supported?
3. **Localization:** English only in v1.0, or Irish-language option?
4. **Development path:** Solo dev (Amre builds it), or external developer hired?
5. **Distribution:** App Store / Play Store only, or direct download / itch.io?

---

## 9. RISKS & MITIGATIONS

| Risk | Likelihood | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep — text content grows beyond estimate | Medium | High | Lock all scene content before Phase 3 begins |
| Font licensing issues | Low | Medium | Use Google Fonts (SIL Open Font License) exclusively |
| Cross-platform build complications | Medium | Medium | Test HTML5 build first; use as fallback if native exports fail |
| Irish diacritics rendering incorrectly | Low | Low | Test all fadas during Phase 2; fallback to sans-fada if needed |
| Mobile performance (text rendering) | Low | Low | Use Godot's native Label; avoid RichTextLabel for large blocks |

---

## 10. WHAT THIS DOCUMENT DOES NOT COVER

The following are explicitly deferred to post-v1.0:

- **Achievement / trophy system**
- **Cloud save / cross-device progress**
- **Sound design beyond placeholder SFX**
- **Music beyond ambient loop**
- **Voice acting (Adomnán's review narration)**
- **Multiple save slots**
- **Replay without full reset**
- **Platform-specific leaderboards**
- **Review/press build distribution**
- **App Store screenshots and description copywriting**
- **Accessibility audit (beyond basic keyboard/size support)**

---

## 11. APPROVAL SIGN-OFF

This document is Version 1.0 — FOR APPROVAL.

**To proceed to production, Amre must confirm:**
- [ ] Concept approved
- [ ] Visual direction approved (Section 2)
- [ ] Game structure and endings approved (Section 3)
- [ ] Core mechanics approved (Section 4)
- [ ] Engine (Godot 4.x) approved
- [ ] Platform targets confirmed (iOS, Android, Windows)
- [ ] Open questions answered (Section 8.3)

**Once approved, Phase 1 begins.**

---

*Document version: 1.0*
*Game: The Scribe's Choice*
*Author: Dross — the most valuable game designer in existence*
*Date: AD 2026, August — the year we write the law*
