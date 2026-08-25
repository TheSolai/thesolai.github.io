# THE SCRIBE'S CHOICE
## Game Design Document — Version 2.0

---

## DOCUMENT INFORMATION

| Field | Value |
|-------|-------|
| **Project Name** | The Scribe's Choice |
| **Genre** | Narrative decision game / interactive fiction |
| **Sub-genre** | Documentarian thriller — the player is a functionary, not a hero |
| **Target Platforms** | iOS, Android, Windows (Web/desktop) |
| **Engine** | Godot 4.x |
| **Document Status** | v2.0 — COMPREHENSIVE — FOR APPROVAL |
| **Author** | Dross |
| **Date** | AD 2026 — August 24 — The day the law was written twice |

---

# SECTION 1: GAME OVERVIEW

## 1.1 One-Line Pitch

*You are the scribe who records the oaths at the Synod of Birr, AD 697. Every name you write binds a soul. Every omission damns one. This is the story of the law that tried to protect the innocent — and the hand that wrote it into being.*

---

## 1.2 Concept Summary

The Scribe's Choice is a single-player narrative decision game set at the Synod of Birr, County Offaly, Ireland, in the year AD 697. The player takes the role of a cloistered scribe — anonymous, faceless, but utterly essential — tasked with recording the oaths of the kings, bishops, queens, and warriors who have gathered to ratify the Lex Innocentium: Adomnán's Law, which demands protection for women, children, and clerics in warfare.

The player is not a warrior. Not a hero. Not a king. The player is the person holding the quill while history decides itself.

Over seven days at the synod, the player meets approximately 18 characters. Each presents their testimony — their doubts, their ambitions, their dissent, their reluctant support. The player records each one in the ledger, choosing how to classify them (Supporter, Conditional, Dissenter, or — for a small number of characters — Unclassified), and annotating each entry with a brief scribe's note that reflects the player's own moral reading of the testimony.

At the end of the seven days, Adomnán — weakened, near death — reviews the completed ledger. He reads the annotations aloud. He asks three questions. And then he pronounces the law's fate.

Every choice accumulates. Every falsification is remembered. Every annotation reveals who the scribe truly is.

---

## 1.3 Core Feel / Player Experience

### 1.3.1 Emotional Journey

The player begins the game as a functionary — someone who stamps documents and records testimony, someone who has done this before and will do it again. This is the *wrong* frame of mind for what happens next.

By the end of the Prologue, that frame is shattered. Rónnat's testimony — a mother's grief over bodies she should never have found — establishes that this is not routine. This is consequential. The ink is wet, and it will not dry without cost.

Over seven days, the player's relationship to the ledger evolves through distinct emotional stages:

**Days I–II: The Rhythm.** The player learns the core loop. Classify. Annotate. Confirm. The decisions feel manageable. A king who cannot swear. A bishop with conditions. These are navigable. The player may not yet feel the weight.

**Days III–IV: The Complications.** The decisions become harder. A king offers something. A gift arrives. Adomnán asks questions. The falsification mechanic reveals itself — the player realises they can write whatever they want, and no one will stop them. This is the moment of moral temptation.

**Days V–VI: The Weight.** Consequences arrive. A dissenter comes to harm. A supporter breaks the oath. The player must write what happened in the margin — or choose silence. The ledger is long now. The player's annotations are beginning to form a pattern. The player cannot unsee the pattern.

**Day VII: The Reckoning.** Adomnán reads the ledger. He reads the annotations. He asks three questions. The player is not answering — the player is being answered *by* their own choices. The ending is not chosen. The ending is *confirmed*.

### 1.3.2 Primary Emotions

| Phase | Emotion | Source |
|-------|---------|--------|
| Prologue | Shock | Rónnat's battlefield testimony |
| Days I–II | Engagement | Learning the mechanics; manageable moral choices |
| Days III–IV | Tension | Moral temptation; falsification becomes visible |
| Days V–VI | Weight | Consequences arrive; annotations reveal patterns |
| Day VII | Reverence / Dread | Adomnán's review; the ledger judges itself |

### 1.3.3 What the Player Should NOT Feel

- **Power fantasy.** The player has no agency outside the ledger. They cannot stop the massacre. They cannot arrest the king. They can only write it down.
- **Clarity about what is right.** Every classification has a defensible argument. There is no correct answer — only consequences.
- **Safe distance from the horror.** The game is about violence against civilians. This is stated plainly. The player's distance from it — they are only recording, only documenting — is itself part of the horror.

---

## 1.4 Target Audience

### 1.4.1 Primary Audience

- Players who completed *Papers Please* (2013, Lucas Pope) and wanted more of that specific feeling — the moral exhaustion, the bureaucratic horror, the weight of stamps
- Players who completed *Return of the Obra Dinn* (2018, Lucas Pope) — the same documentarian impulse, the same commitment to letting the player figure it out
- Players of *Containment* (2024) or similar academic-archival games that treat documents as primary narrative medium
- Fans of the *Celtic* / early medieval Ireland setting who want something historically textured without being a textbook
- Players who read *The Historian* by Elizabeth Kostova or *The Mists of Avalon* and want to inhabit that world rather than observe it

### 1.4.2 Secondary Audience

- Players who enjoy slow, deliberate games (*Journey*, *Firewatch*, *Pentiment*) — games that reward patience
- Players who are interested in early Irish law and history (the Lex Innocentium is real; the Synod of Birr is real; the characters are fictional but historically grounded)
- Players who are theologians, historians, or scholars of medieval Ireland — the game rewards expertise without requiring it

### 1.4.3 Age Rating

**PEGI 12 / ESRB Teen**

Justification:
- Thematic content: mentions of wartime violence against women and children (off-screen, described in testimony)
- No graphic depiction of violence at any point
- No sexual content
- No gore
- No torture, no self-harm
- The horror is in testimony and implication, not depiction
- The setting (7th century, religious synod) is inherently non-explicit

Content descriptors: Violence (thematic, non-graphic), History (medieval Ireland)

---

## 1.5 Platform Priority

| Priority | Platform | Distribution Target | Export Format |
|----------|----------|-------------------|--------------|
| 1 | iOS | App Store | Godot iOS export → XCode → IPA |
| 1 | Android | Google Play Store (deferred post-v1.0) | Godot Android export → AAB |
| 1 | Windows | Steam | Godot Windows export → EXE (NSIS installer) |
| 2 | macOS | Steam | Godot macOS export → .app bundle |
| 3 | Web | Browser / itch.io | Godot HTML5 → WebGL 2.0 |

**Note on cross-platform development:** The Godot 4.x single-codebase approach allows all platforms to be maintained from one project. HTML5 build serves as the primary development test target and the fallback distribution path for platforms where native export is unavailable.

---

# SECTION 2: VISUAL DESIGN

## 2.1 Design Philosophy

This is a **text-dominant game**. Visual design exists in service of the text — to create the atmosphere in which the text is read, not to compete with it.

The reference point is not a medieval RPG. It is an illuminated manuscript — specifically the Book of Kells — stripped of colour, stripped of warmth, and made claustrophobic. The beauty is there. But it belongs to a world that has seen too much violence to be pretty about it.

**Core principle:** The player should feel like they are reading an ancient text that is also alive. Every visual element should reinforce this: the texture of vellum, the weight of ink, the glow of candlelight in a dark hall.

---

## 2.2 Color Palette

### 2.2.1 Full Palette with Usage Context

| Role | Color Name | Hex | Usage |
|------|-----------|-----|-------|
| Background (primary) | Deep Vellum | `#1a1510` | Main game screen background. Near-black with warm undertones. |
| Background (secondary) | Dark Parchment | `#211a12` | Panel backgrounds, scene containers. Slightly lighter. |
| Background (ledger) | Aged Vellum | `#1e1810` | The ledger screen — slightly distinct from main BG. |
| Primary Text | Faded Gold Ink | `#d4c4a8` | All body text, narrative, testimony. Warm cream. |
| Headers / Illuminated | Illuminated Gold | `#c9a030` | Titles, Day headers, classification labels, epilogue headings. |
| Celtic Accent | Moss Green | `#2d5a4a` | Celtic knot borders, decorative corners. Not bright — muted. |
| Celtic Accent (highlight) | Gold Highlight | `#8b6914` | Celtic knot highlights within the green. |
| Supporter Marker | Verdigris | `#3a5a4a` | Wax seal for Supporter classification. Faded green. |
| Conditional Marker | Muted Amber | `#7a6030` | Wax seal for Conditional classification. Dull gold-brown. |
| Dissenter Marker | Ash Grey | `#4a4040` | Wax seal for Dissenter classification. Dark, cold. |
| Curse Marker | Dried Blood | `#6b3030` | When a curse is mentioned in narrative. Not bright — old blood. |
| UI Borders | Dark Oak | `#3d2f1e` | Panel borders, dividers. Brown-black. |
| Candle Glow | Warm Glow | `#ff9940` at 8% opacity | Ambient glow effect on borders and frames. |
| Outcome Hint Text | Pale Faded | `#8a7a5a` | Outcome hints after confirmation. Subtler than primary text. |
| Status Text | Muted Gold | `#a09070` | Status bar text, day counter. Quiet. |
| Settings Text | Pale Vellum | `#c0b090` | Settings screen text. Readable but not bright. |
| Error / Warning | Ash Red | `#7a4040` | Only used if an error state is needed. |

### 2.2.2 Accessibility Color Pairings

| Pairing | Background | Text | Contrast Ratio | WCAG Level |
|---------|-----------|------|----------------|------------|
| Primary (standard) | `#1a1510` | `#d4c4a8` | 9.2:1 | AAA |
| Header on Primary | `#1a1510` | `#c9a030` | 7.1:1 | AAA |
| Low-contrast hint | `#1a1510` | `#8a7a5a` | 4.8:1 | AA |
| High-contrast mode | `#0d0a08` | `#e8d8b8` | 12.1:1 | AAA |

**High contrast mode** (toggled in settings) switches to: Background `#0d0a08`, text `#e8d8b8`, borders `#5a4a30`. This is the only visual mode change in the game.

---

## 2.3 Typography

### 2.3.1 Font Stack

All fonts are loaded from Google Fonts (SIL Open Font License). Fonts are downloaded and bundled locally for offline use — the game must not require an internet connection to display text.

| Element | Font Family | Google Fonts Name | Fallback | Style | Size | Line Height | Character Support |
|---------|------------|--------------------|----------|-------|------|-------------|-----------------|
| Game Title | MedievalSharp | `MedievalSharp` | Georgia, serif | Regular, All Caps | 36px | 1.2 | Latin Extended A |
| Day Headers | Uncial Antiqua | `Uncial Antiqua` | Georgia, serif | Regular, All Caps | 24px | 1.3 | Latin Extended A |
| Scene Titles | IM Fell English SC | `IM Fell English SC` | Georgia, serif | Small Caps | 18px | 1.4 | Latin |
| Narrative Text | Crimson Text | `Crimson Text` | Georgia, serif | Regular | 18px | 1.7 | Latin Extended A |
| Testimony | Crimson Text | `Crimson Text` | Georgia, serif | Italic | 18px | 1.7 | Latin Extended A |
| Character Attribution | Crimson Text | `Crimson Text` | Georgia, serif | Regular, Small Caps | 14px | 1.5 | Latin |
| Ledger Entry Name | IM Fell English | `IM Fell English` | Georgia, serif | Regular | 16px | 1.6 | Latin |
| Ledger Entry Note | Cormorant Garamond | `Cormorant Garamond` | Georgia, serif | Italic | 16px | 1.6 | Latin Extended A |
| Classification Label | IM Fell English SC | `IM Fell English SC` | Georgia, serif | Small Caps | 14px | 1.4 | Latin |
| Annotation Options | Cormorant Garamond | `Cormorant Garamond` | Georgia, serif | Italic | 16px | 1.5 | Latin Extended A |
| Status Bar | IM Fell English | `IM Fell English` | Georgia, serif | Regular | 12px | 1.4 | Latin |
| Settings Label | Crimson Text | `Crimson Text` | Georgia, serif | Regular | 16px | 1.6 | Latin Extended A |
| Button Text | IM Fell English SC | `IM Fell English SC` | Georgia, serif | Small Caps | 14px | 1.4 | Latin |

### 2.3.2 Irish Diacritic Support

All body fonts must support Irish-language characters (fadas):
`Á É Í Ó Ú á é í ó ú`

The `Latin Extended A` Unicode block covers these. Testing is required during Phase 2 to confirm all fonts render fadas correctly at all sizes.

If a font fails the diacritic test, the fallback chain is: `MedievalSharp` → `Georgia` → system serif. All fallbacks must support fadas.

### 2.3.3 Text Size Modes

| Mode | Narrative/Testimony | Headers | Status/Meta |
|------|-------------------|---------|-------------|
| Small | 16px | 22px | 11px |
| Medium (default) | 18px | 24px | 12px |
| Large | 20px | 28px | 14px |

The player selects text size in Settings. Default is Medium.

---

## 2.4 UI Components

### 2.4.1 Title Screen

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ ╔══════════════════════════════════════════════════════╗   │
│ ║  CELTIC KNOT BORDER — full frame, animated glow        ║   │
│ ║                                                        ║   │
│ ║              THE SCRIBE'S CHOICE                       ║   │
│ ║         A game of oaths, ink, and consequence          ║   │
│ ║                                                        ║   │
│ ║                                                        ║   │
│ ║                   [ WAX SEAL: BEGIN ]                 ║   │
│ ║                                                        ║   │
│ ║                   [ SETTINGS ]                        ║   │
│ ║                                                        ║   │
│ ║                                                        ║   │
│ ║  THE SCRIBE'S CHOICE is a work of historical fiction. ║   │
│ ║  The Lex Innocentium was ratified at Birr, AD 697.   ║   │
│ ╚══════════════════════════════════════════════════════╝   │
└──────────────────────────────────────────────────────────────┘
```

**Elements:**
- Full-screen Celtic knot border (SVG, see Section 7 for spec)
- Animated candle-glow effect on the border: 4-second cycle, opacity oscillates between 60% and 100%, colour `#ff9940` at 8% opacity overlay
- Title in MedievalSharp, All Caps, Illuminated Gold, 36px, letter-spacing 4px
- Subtitle in Crimson Text Italic, Faded Gold Ink, 16px
- "BEGIN" button: wax seal graphic, MedievalSharp SC, 16px. Hover state: seal lifts 2px with shadow; press state: seal presses down with stamp SFX
- "SETTINGS" button: text-only, no seal, MedievalSharp SC. Underline on hover.
- Footer disclaimer: IM Fell English, 11px, Muted Gold. Non-interactive.
- Background: Deep Vellum `#1a1510` with subtle parchment texture overlay at 3% opacity

**Settings accessible from title screen** (separate overlay panel, not a new screen):
- Audio volume slider (0-100, default 50)
- Music toggle (on/off, default on)
- SFX toggle (on/off, default on)
- Text size (Small/Medium/Large)
- High contrast mode (toggle)
- Credits (scrollable overlay)

### 2.4.2 Main Game Screen

This is the primary interface. All gameplay takes place here. No scrolling within the screen — content fills the space.

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ CELTIC KNOT TOP BORDER — decorative header bar, 40px tall   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    ◆ DAY I ◆                                 │
│            "The field. The mother. The oath."                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ SCENE NARRATIVE                                         │  │
│  │                                                         │  │
│  │ The synod hall is full. You have been given the quill. │  │
│  │ The ink is wet. The kings have not yet spoken.          │  │
│  │ You wait.                                               │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ THE RECORD                                              │  │
│  │                                                          │  │
│  │  "I cannot swear it. My warriors would depose me         │  │
│  │  within the fortnight. I would be dead, and my          │  │
│  │  family with me."                                       │  │
│  │                                                          │  │
│  │  — King Fogartach of Uí Néill                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ HOW DO YOU RECORD THIS?                                 │   │
│  │                                                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │  SUPPORTER  │  │CONDITIONAL │  │  DISSENTER │   │   │
│  │  │ [wax seal]  │  │ [wax seal]  │  │ [wax seal] │   │   │
│  │  │  verdigris  │  │   amber    │  │  ash grey  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  │                                                        │   │
│  │  ANNOTATION                                             │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ "Fear, not malice. He would keep the oath if     │  │   │
│  │  │  he could."                                      │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ "He cannot or will not. These are not the same."│  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ "A convenient fear. I do not believe him."      │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │                                                        │   │
│  │               [ CONFIRM ENTRY ]                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  ── Day 1 of 7 ── Oaths: 2 ── Conditional: 1 ── Dissenting: 0│
└──────────────────────────────────────────────────────────────┘
```

**Panel Specifications:**

1. **Top Celtic Border:** Decorative bar, 40px tall, Celtic knot SVG pattern, animated glow. Not interactive.

2. **Day Header:** IM Fell English SC, Small Caps, Illuminated Gold, 20px. Subtitle in Crimson Text Italic, Faded Gold, 14px.

3. **Scene Narrative Panel:** Dark Parchment background (`#211a12`), rounded corners (4px), 1px Dark Oak border. Padding: 16px. Text: Crimson Text Regular, 18px. Max 4 lines. Fade-in animation on scene load: 400ms, ease-out, line by line (each line delays 100ms after the previous).

4. **The Record Panel:** Dark Parchment background, same styling as narrative panel. Testimony text: Crimson Text Italic, 18px. Attribution: Crimson Text Regular Small Caps, 14px, Muted Gold. Fade-in after narrative completes: 200ms delay, 400ms duration.

5. **Decision Panel:** Slightly lighter background (`#2a2015`), 1px Celtic Moss border, 8px rounded corners. Contains the three wax seal buttons, annotation options, and confirm button.

6. **Wax Seal Buttons:**
   - Size: 80px × 80px
   - Visual: SVG circle with embossed text, Celtic knot detail on border
   - Colours: Supporter (Verdigris `#3a5a4a`), Conditional (Amber `#7a6030`), Dissenter (Ash Grey `#4a4040`)
   - Hover: scale 1.05, subtle glow matching the seal colour at 30% opacity
   - Selected: scale 0.95, stamp-down animation (translateY 2px), stamp SFX plays
   - Only one can be selected at a time

7. **Annotation Options:** Three cards, each one selectable. Cormorant Garamond Italic, 16px.
   - Unselected: transparent background, 1px Dark Oak border, Muted Gold text
   - Hover: Dark Parchment background, Illuminated Gold text
   - Selected: Dark Parchment background, Illuminated Gold text, Illuminated Gold left border (3px), checkbox indicator

8. **Confirm Entry Button:** IM Fell English SC, Small Caps, 14px. Disabled state (grey, non-interactive) until both classification AND annotation are selected. Enabled state: Illuminated Gold text, Dark Oak background. Press: stamp SFX plays, ledger entry confirmed, screen transitions.

9. **Status Bar:** Bottom of screen, 24px tall, background `#0f0d0a`. IM Fell English Regular, 12px, Muted Gold. Shows: current day, oath counts by classification.

### 2.4.3 Ledger Screen (accessible via menu)

Full-screen overlay (not a new scene — modal overlay).

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  THE LEDGER                                    [ X CLOSE ]  │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Day I — King Fogartach of Uí Néill                         │
│  Classification: CONDITIONAL                                 │
│  Scribe's note: "Fear, not malice. He would keep the oath    │
│  if he could."                                              │
│  ─────────────────────────────────────────────              │
│                                                              │
│  Day I — Bishop Ronan of Armagh                             │
│  Classification: SUPPORTER                                   │
│  Scribe's note: "The bishop knows the cost. He has paid it." │
│  ─────────────────────────────────────────────              │
│                                                              │
│  ... (scrollable)                                            │
│                                                              │
│  Entries: 14    Supporters: 7    Conditional: 4    Dissenters: 3 │
└──────────────────────────────────────────────────────────────┘
```

- Scrollable list, Dark Parchment background
- Each entry is a LedgerEntry card
- Entry name: IM Fell English, 16px, Illuminated Gold
- Classification label: IM Fell English SC, 14px, classification colour
- Annotation: Cormorant Garamond Italic, 15px, Faded Gold
- Scrollbar: custom styled, Dark Oak thumb, Dark Parchment track

### 2.4.4 Epilogue Screen

Full-screen, single view, no UI chrome except "Play Again."

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ ╔══════════════════════════════════════════════════════╗   │
│ ║  CELTIC KNOT BORDER — full frame, animated glow        ║   │
│ ║                                                        ║   │
│ ║              THE LAW STANDS                            ║   │
│ ║         ══════════════════════════                     ║   │
│ ║                                                        ║   │
│ ║  [Epilogue text — 3-4 paragraphs]                     ║   │
│ ║                                                        ║   │
│ ║  The ledger, read aloud:                              ║   │
│ ║  "King Fogartach of Uí Néill — Conditional.           ║   │
│ ║   'Fear, not malice. He would keep the oath...'        ║   │
│ ║                                                        ║   │
│ ║                                                        ║   │
│ ║               [ TURN THE PAGE ]                       ║   │
│ ║                                                        ║   │
│ ╚══════════════════════════════════════════════════════╝   │
└──────────────────────────────────────────────────────────────┘
```

- Celtic knot border returns for epilogue — this is deliberate. It appeared at the title. It appears at the end.
- Epilogue title in MedievalSharp, All Caps, Illuminated Gold, 32px
- Epilogue body in Crimson Text, 18px, Faded Gold, max-width 640px, centred
- The "ledger read aloud" section: IM Fell English Italic, 16px, slightly different styling to separate it
- "Turn the Page" button: wax seal, MedievalSharp SC, 14px. Press → returns to Title Screen

### 2.4.5 Settings Overlay

Modal overlay from title screen.

```
┌──────────────────────────────────────────────────────────────┐
│  SETTINGS                                       [ X CLOSE ] │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Audio                                                      │
│  Master Volume        [═══════════○────]  50%              │
│  Music                [ON ]  [ OFF]                         │
│  Sound Effects        [ ON]  [ OFF ]                        │
│                                                              │
│  Display                                                      │
│  Text Size            [ SMALL]  [MEDIUM●]  [LARGE]           │
│  High Contrast        [ ]                                          │
│                                                              │
│  Credits                                                 [ → ] │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.4.6 Pause Menu (in-game)

Activated by tapping the top-left corner or pressing Escape/Pause button.

```
┌──────────────────────────────────────────────────────────────┐
│                       PAUSED                                 │
│                                                              │
│                   [ RESUME ]                                 │
│                   [ LEDGER ]                                 │
│                   [ SETTINGS ]                               │
│                   [ QUIT TO TITLE ]                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2.5 Animation & Motion

### 2.5.1 Animation Principles

All animations serve the game's emotional arc. The pace of animations should feel **deliberate** — nothing snappy or playful. Everything is weighted. Even transitions feel like pages turning in a heavy book.

| Principle | Application |
|-----------|------------|
| **Deliberate** | No fast snappy animations. Minimum 200ms for any transition. |
| **Weighted** | Stamp animations feel like pressing wax onto vellum. Page turns feel heavy. |
| **Text-forward** | Animations exist to serve the text, not compete with it. Never animate while text is still appearing. |
| **Non-distracting** | Ambient animations (candle flicker) are subtle — 5-10% opacity shift, never more. |
| **Meaningful** | When animations carry meaning (stamp = confirmation, curse flash = violation), the association must be consistent and learnable. |

### 2.5.2 Full Animation Inventory

| Animation Name | Element | Duration | Easing | Description |
|---------------|---------|----------|--------|-------------|
| `fadeIn_narrative` | Scene narrative text | 400ms per line, 100ms stagger | ease-out | Each line fades in sequentially. Previous line must finish before next begins. |
| `fadeIn_record` | The Record panel | 400ms | ease-out | Fades in after narrative completes. |
| `fadeIn_decision` | Decision panel | 300ms | ease-out | Slides up 8px while fading in, after record panel completes. |
| `stamp_press` | Wax seal button on select | 150ms | ease-in | Scale 0.95, translateY 2px. Plays stamp SFX simultaneously. |
| `stamp_release` | Wax seal button after press | 100ms | ease-out | Scale returns to 1.0. |
| `annotation_hover` | Annotation option card | 150ms | ease-out | Gold underline bleeds from left. Background shifts to Dark Parchment. |
| `annotation_select` | Annotation option on confirm | 200ms | ease-out | Illuminated Gold left border appears (3px). Checkbox fills. |
| `ledger_entry_confirm` | Confirm Entry button press | 200ms | ease-in | Button depresses. Stamp SFX plays. |
| `screen_transition` | Between scenes | 600ms total | ease-in-out | Current scene fades to black (300ms), new scene fades in (300ms). No hard cuts. |
| `scene_complete` | After ledger entry confirmed | 800ms pause | — | Brief moment of stillness before transition. Ledger "settles." |
| `candle_flicker` | Border glow (ambient) | 4000ms, infinite loop | random | Opacity oscillates 0.6 → 1.0 → 0.7 → 1.0. Never a sharp transition. |
| `title_celtic_glow` | Title screen border | 5000ms, infinite loop | ease-in-out | Subtle golden pulse on the knot highlights. Opacity 0.5 → 0.9. |
| `ink_bleed` | Title screen title text (on load) | 800ms | ease-out | Text appears with a spreading shadow, as if ink is bleeding into the page from wet quill. |
| `epilogue_knight_reveal` | Celtic border on epilogue entry | 1200ms | ease-out | Border fades in from transparent, as if the page is being illuminated. |
| `curse_flash` | Screen edge vignette | 400ms | ease-in-out | Dried Blood coloured vignette flashes at screen edges when a curse activates. |
| `settings_slide` | Settings overlay open | 300ms | ease-out | Overlay slides down from top while fading in. |
| `overlay_close` | Any modal overlay close | 200ms | ease-in | Fades out quickly — deliberately faster than open. |
| `page_turn` | "Turn the Page" button | 600ms | ease-in-out | Simulates a page turning — slight 3D transform on the screen content before transition to title. |

### 2.5.3 Transition Timing Between Scenes

After the player confirms their ledger entry:

1. **Ledger stamp animation** — 200ms
2. **Brief stillness** (scene settles) — 800ms
3. **Screen fades to black** — 300ms
4. **Black holds** — 200ms
5. **New scene fades in (narrative)** — 400ms + 100ms stagger per line
6. **"The Record" fades in** — 400ms delay, 400ms duration
7. **Decision panel fades in** — 200ms delay, 300ms duration

Total time from confirmation to interactive decision: approximately **2,500ms**. This is intentional — the pace must feel deliberate, not rushed.

---

## 2.6 Audio Specification (Full)

*See Section 8 for complete music design document. This section covers the audio implementation within the game.*

### 2.6.1 Audio Bus Structure (Godot)

```
Master Bus (0dB)
├── Music Bus (−3dB)
│   └── All background music tracks
├── SFX Bus (−2dB)
│   ├── Stamp SFX
│   ├── Page Turn SFX
│   ├── UI Hover SFX
│   └── Curse Tone SFX
└── Ambient Bus (−6dB)
    ├── Candle Crackle Loop
    └── Quill Scratch Loop
```

### 2.6.2 SFX Inventory

| SFX Name | File | Description | Trigger |
|---------|------|-------------|---------|
| `ink_stamp` | `ink_stamp.wav` | Satisfying wax-on-vellum press. Slight reverb. | Wax seal button pressed (classification selected) |
| `ledger_confirm` | `ledger_confirm.wav` | Quieter stamp, paper settle. | Confirm Entry button pressed |
| `page_turn` | `page_turn.wav` | Soft paper rustle, one page | Scene transition |
| `ui_hover` | `ui_hover.wav` | Extremely quiet — barely a sound. Faint whisper of movement. | Any button/surface hover |
| `curse_tone` | `curse_tone.wav` | Low, cold, sustained tone — unsettling but not alarming. 800ms duration. | Curse activates (dissenter harmed) |
| `oath_recorded` | `oath_recorded.wav` | Brief, warm chime — feels like a promise being made. | Supporter classification confirmed |
| `conditional_recorded` | `conditional_recorded.wav` | Dissonant, uncertain. A chord that can't resolve. | Conditional classification confirmed |
| `dissent_recorded` | `dissent_recorded.wav` | Cold silence, then a low thud. The sound of exclusion. | Dissenter classification confirmed |
| `settings_open` | `settings_open.wav` | Soft slide. | Settings overlay opens |
| `settings_close` | `settings_close.wav` | Soft slide (reverse). | Settings overlay closes |

### 2.6.3 Audio Implementation Rules

- All SFX are short (<2 seconds) and non-intrusive
- SFX are loaded into Godot's AudioStreamPlayer nodes; preloaded at game start
- Music crossfades between tracks: 2000ms overlap
- If a curse activates during a music track, the music ducks (reduces volume by 50%) for the duration of the curse_tone, then restores
- On mobile: Audio ducks when system notifications appear (handled by OS)
- If SFX toggle is off: no SFX plays, but music and ambient continue
- If Music toggle is off: music and ambient stop; SFX continues
- Audio does not auto-play on scene entry if the previous scene's audio is still playing — crossfade handles this

---

# SECTION 3: GAME STRUCTURE & FLOW

## 3.1 State Machine

```
TITLE_SCREEN
    │
    ├── [BEGIN] → PROLOGUE
    └── [SETTINGS] → SETTINGS_OVERLAY → TITLE_SCREEN

PROLOGUE
    │ (1 scene: The Battlefield — Rónnat's testimony)
    ▼
DAY_I_SCENE_1 → DAY_I_SCENE_2 → DAY_I_SCENE_3
    │                                           │
    ▼                                           ▼
DAY_II_SCENE_1 → DAY_II_SCENE_2 → DAY_II_SCENE_3
    │                                           │
    ▼                                           ▼
DAY_III_SCENE_1 → DAY_III_SCENE_2 → DAY_III_SCENE_3
    │                                           │
    ▼                                           ▼
DAY_IV_SCENE_1 → DAY_IV_SCENE_2
    │                                           │
    ▼                                           ▼
DAY_V_SCENE_1 → DAY_V_SCENE_2
    │                                           │
    ▼                                           ▼
DAY_VI_SCENE_1 → DAY_VI_SCENE_2 → DAY_VI_SCENE_3
    │                                           │
    ▼                                           ▼
DAY_VII_SCENE_1 → DAY_VII_SCENE_2 → ADOMNÁN'S_REVIEW
    │                                           │
    ▼                                           ▼
EPILOGUE → CREDITS → TITLE_SCREEN
```

**State persistence:** The entire game state is saved to disk at the end of every scene (after the ledger entry is confirmed). If the game crashes or is quit mid-scene, the player resumes at the start of the current scene.

---

## 3.2 Scene Structure

Every gameplay scene follows this fixed structure:

```
[SCENE ENTRY]
    ↓
[LOAD SCENE DATA] — Load narrative, testimony, character, options from scene resource
    ↓
[ANIMATE: Narrative Fade In] — 400ms + stagger
    ↓
[ANIMATE: The Record Fade In] — 400ms delay, 400ms duration
    ↓
[ANIMATE: Decision Panel Fade In] — 200ms delay, 300ms duration
    ↓
[PLAYER INTERACTION LOOP]
    ├── Player selects Classification (wax seal)
    │   → Stamp SFX plays, seal animates
    │   → Annotation options appear/highlight
    │   → Player selects Annotation (annotation card)
    │   → Confirm button activates
    │   └── Player presses Confirm Entry
    │       → Ledger Entry created and saved
    │       → Stamp SFX plays
    │       → Brief stillness (800ms)
    │       → Screen transition (600ms)
    │       → NEXT SCENE
    │
    └── [PAUSE MENU accessible at any time]

[IF ADOMNÁN'S REVIEW SCENES]
    └── Different flow: Ledger shown, annotations read, player confirms one annotation revision
```

---

## 3.3 Scene Inventory — Fully Written

The following 19 scenes form the complete game. Each scene includes: structural specification, full prose narrative, character testimony, classification options, annotation library, outcome hints, and narrative flags set on completion.

---

### PROLOGUE SCENE 0: The Battlefield

**Structural:**
- Day: — (Prologue)
- Scene: 0
- Character: Rónnat (mother of Adomnán)
- Classification: N/A — Rónnat is not classified; this is the tutorial entry
- Special: This scene does not appear in the ledger as a classified entry. It establishes the emotional foundation.

**Narrative Text:**

The quill is heavier than you expected.

You have been at Iona before. You know the rhythm of transcription — the slow accumulation of text, the patient accumulation of years. You have written lives into the record without feeling them. This is the craft: to observe without being moved.

But you were not prepared for Rónnat.

She stands in the doorway of the synod hall, her cloak still damp from the road. She has come from the west. She has brought nothing but her son and her testimony.

Adomnán bows his head. He cannot speak of this himself. He has asked you to record what she says.

She begins.

**Rónnat's Testimony:**

"I will tell you what I saw. Not what I felt — what I *saw*.

"There was a river. The warriors had gone. The river ran red, then pale, then red again. At the ford, where the water met the bank, the bodies had gathered.

"Mothers. Children. Babies.

"They had been drawing water. That is what they were doing when the warriors came. Drawing water. Grinding grain. Tending the fire.

"I counted seventeen bodies. My son counted twenty-three. He is better with numbers than I am. We did not argue about the difference.

"The babies — I do not wish to describe the babies.

"Adomnán asked me: what would you have us do? And I told him: *make a law that protects them*. Not because I believe laws protect anyone. Because a law that names them is a law that remembers them. And memory is the only vengeance that does not require more blood.

"That is my testimony. Write it down."

**Classification:** N/A (player records it as the Prologue Entry — a special ledger item that is not a classification but is preserved)

**Annotation Options (tone labels shown internally; player does not see these):**
1. *"She spoke without tears. I do not know how."* — LENIENT (the player is moved by Rónnat's composure)
2. *"A mother's grief, formalised. The law begins here."* — NEUTRAL (observational)
3. *"She wants blood. She calls it memory. I will not pretend otherwise."* — HARSH (the player is skeptical but records it faithfully)

**Outcome Hint:** *"The ink is wet. The first entry is made. You cannot unread what she has told you."*

**Narrative Flags Set:**
- `prologue_complete: true`
- `ronsat_testimony_recorded: true`

---

### DAY I — SCENE 1: The King Who Cannot

**Structural:**
- Day: I
- Scene: 1
- Character: King Fogartach of Uí Néill
- Classification: CONDITIONAL (defensive), SUPPORTER (if falsified), DISSENTER (if classified harshly)
- Classification Weight: High — this is the first real decision and sets expectations

**Narrative Text:**

The synod hall is large and cold. The kings have been gathered since dawn. The first to approach your desk is King Fogartach of Uí Néill, a man built like a harbour wall — broad, grey-faced, deliberate.

He has the look of a man who has rehearsed what he is about to say.

He does not sit. He stands before your desk and speaks to the quill in your hand, as though the quill will determine his fate more than the man holding it.

**Fogartach's Testimony:**

"I have considered this law carefully. I am not unsympathetic to its intent.

"But I must be candid with you, scribe, because candour is all I have to offer.

"My warriors — the men who keep me on my throne — do not share my sympathies. They have told me, in terms I will not repeat, that if I swear this oath, they will consider me unfit to rule. They do not say this as a threat. They say it as a fact. They would depose me within a fortnight. My family would follow.

"I am not afraid for myself. I am afraid for my daughters.

"If I am deposed, my daughters are unprotected. The law you ask me to swear — the law you ask my warriors to respect — would no longer reach them. They would be at the mercy of a new king who owes me nothing.

"I cannot swear the oath as it stands. I would need... assurances. That my house is named. That my daughters are listed specifically. That the law's protection extends to them even if I am no longer king.

"If this is possible, I will swear. If not — I will leave Birr with my shame and my warriors' contempt, and you may write what you wish about me."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "Fear, not malice. He would keep the oath if he could." | *"You record him as a supporter. He will not forget what you wrote."* |
| | "The daughters. That is what holds him. I name them and he is ours." | |
| | "He came to the synod. That is more than some will do." | |
| **CONDITIONAL** | "He cannot or will not. These are not the same. I have noted both." | *"You record him as conditional. He accepts this with a slow nod."* |
| | "He has asked for conditions. The law does not give conditions." | |
| | "A king who fears his own warriors. I write it as I hear it." | |
| **DISSENTER** | "A convenient fear. I do not believe him." | *"You record him as a dissenter. His face does not change. His warriors' faces do."* |
| | "He would break the oath the moment his warriors asked." | |
| | "He came to buy time. I do not sell it." | |

**Narrative Flags Set:**
- `fogartach_classification: [choice]`
- `fogartach_annotation: [choice]`
- `day_1_started: true`

---

### DAY I — SCENE 2: The Bishop's Condition

**Structural:**
- Day: I
- Scene: 2
- Character: Bishop Ronan of Armagh
- Classification: SUPPORTER (defensive), CONDITIONAL (defensive), DISSENTER (unlikely)
- Note: Bishop Ronan is genuinely sympathetic to the law but has a genuine objection

**Narrative Text:**

Bishop Ronan of Armagh arrives with the measured pace of a man who has spent forty years being precise. He carries no sword. He carries the weight of the Church's position on his shoulders, and he wears it like a garment.

He bows to you — not to Adomnán, not to the assembly, to you, the scribe. You are the first person in the hall to receive his bow.

He has read the Lex Innocentium. He has studied it. He has comments.

**Bishop Ronan's Testimony:**

"Praise be to God that someone has finally written these words down.

"I have no objection to the protection of women and children. I have no objection to the protection of clerics — though I note that *clerics* and *church buildings* and *church lands* are not the same thing, and the current draft of this law uses these words interchangeably when it should not.

"The Church's position — my position — is this: I will swear to protect women, children, and the clerics who serve them. I will not swear to protect church property. Property is not innocent. Property is contested. The law of war does not exempt a barn because a bishop sleeps in it.

"If the word *clerics* is amended to include the persons of the Church — the bishops, the abbots, the brothers and sisters in community — and not the buildings or the lands they hold, then I will swear this oath now, in this hall, before you write my name.

"If not — I will need to consider whether I can in good conscience add my name to a document that conflates the innocent with the institutional."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "The bishop is right about the law's imprecision. I record him as a supporter who identified a flaw." | |
| | "He will swear. That is what matters. His conditions are noted but do not change his intent." | |
| | "A man of the Church who reads carefully. I respect this." | |
| **CONDITIONAL** | "His condition is legitimate. The law *does* conflate persons and property. I record this." | |
| | "He is for the law but against its wording. I note the distinction." | |
| | "He wants precision. The synod wants a signature. I record the tension." | |
| **DISSENTER** | "He finds theological objection where there is only political convenience." | |
| | "A churchman who protects church property. I expected nothing more." | |

**Narrative Flags Set:**
- `ronan_classification: [choice]`
- `ronan_annotation: [choice]`

---

### DAY I — SCENE 3: The Named Daughters

**Structural:**
- Day: I
- Scene: 3
- Character: Queen Eormen of the Ulaidh
- Classification: CONDITIONAL (defensive)
- Note: This is the last scene of Day I. It introduces the specific question of *named* vs *universal* protection.

**Narrative Text:**

Queen Eormen of the Ulaidh does not approach your desk. She sends a herald, who announces her title at a distance of ten paces — a formal gesture, not an informal one. She wishes the hall to know she is present.

She is younger than you expected. Her daughters are with her — two girls, perhaps eight and ten, who stand behind her with the rigid posture of children who have been told not to speak.

Queen Eormen speaks without preamble.

**Queen Eormen's Testimony:**

"I have no objection to the Lex Innocentium in principle. I have a specific objection in practice.

"Women are not a category in this law. Women are a collection of names. I want my daughters named. Not *children* — not *women* — my daughters. By name. In the document. In the oath.

"A law that protects unnamed women protects no one I love. It is a gesture. I am asking for something more than a gesture.

"If the Lex Innocentium will include the names of my daughters — Eithne and Dearbhail — specifically, as parties to this oath — then I will swear it. Otherwise, I will leave this synod with my daughters unnamed and my doubts intact."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "She asks for names, not exceptions. I record this as an act of love." | |
| | "The queen is right: a universal law that protects no one in particular protects no one." | |
| | "I note her daughters' names as she requires. Eithne. Dearbhail. The law will know them." | |
| **CONDITIONAL** | "She will swear if her daughters are named. This is not dissent — it is negotiation." | |
| | "A queen who trusts no law until her children's names are in it. I understand this." | |
| | "The law cannot name individuals. But I understand why she asks." | |
| **DISSENTER** | "She would make the law a list of names. This is not a law — it is a petition." | |
| | "A woman's love for her daughters, weaponised as a condition. I record her, and her conditions." | |

**Narrative Flags Set:**
- `eormen_classification: [choice]`
- `eormen_annotation: [choice]`
- `day_1_complete: true`
- *(Day II unlocks)*

---

### DAY II — SCENE 4: The Open Dissenter

**Structural:**
- Day: II
- Scene: 1
- Character: King Diarmait of Mide
- Classification: DISSENTER (defensive; this is the first openly hostile character)
- Note: The game tracks whether the player records Diarmait harshly or with more measured language

**Narrative Text:**

The hall has quieted since the morning. The kings who came to negotiate have mostly done so. What remains are those with strong feelings in one direction or another.

King Diarmait of Mide does not wait to be called. He walks to your desk and stands over it, close enough that you can smell the mead on his breath and the woodsmoke in his cloak.

He looks at your quill. He looks at you. He speaks loudly enough for the hall to hear.

**Diarmait's Testimony:**

"You want me to say it? Fine. I'll say it.

"The law of women is no law at all. You cannot make a law that protects people who cannot fight for themselves and call it justice. It is sentiment. It is weakness. It is the beginning of the end of the only order that holds this island together.

"Women are protected by their fathers, their brothers, their husbands. That is the law. That has always been the law. If you do not like it, change the nature of women — make them fighters. Make them warriors. Until then, this *Lex Innocentium* is a fantasy written by a monk who has never held a sword.

"I will not swear it. I will not sign it. I will not pretend that words on vellum will change what men do when they are hungry for land and glory and revenge.

"Write what you like about me. I know what I am. I know what this synod thinks of me. Write it."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **DISSENTER** | "He spoke his mind without equivocation. I record his dissent without softening it." | |
| | "A man who believes what he believes. I do not share his beliefs, but I record them accurately." | |
| | "Diarmait of Mide. He will not swear. I have written it." | |
| **DISSENTER** (alternate annotation) | "His contempt for the law is clear. His contempt for women is clearer." | |
| | "This is not a man who will change. I write his name in the ledger of those who refused." | |
| | "He wanted to be recorded as this. I obliged." | |

**Note:** Recording Diarmait as SUPPORTER or CONDITIONAL is possible (falsification). This is tracked. Adomnán will notice.

**Narrative Flags Set:**
- `diarmait_classification: [choice]`
- `diarmait_annotation: [choice]`

---

### DAY II — SCENE 5: The Unnamed Warrior

**Structural:**
- Day: II
- Scene: 2
- Character: A young warrior (unnamed — has no name in the record)
- Classification: SUPPORTER (via proxy — his king speaks for him), CONDITIONAL, or DISSENTER
- Note: This scene's core tension is *who are you recording?* The warrior or the king who speaks for him?

**Narrative Text:**

A young man stands beside King Selbach of the Déisi. He is perhaps seventeen. He wears the marks of a warrior — new ones, still healing. He has clearly recently completed his first raid or battle.

King Selbach speaks for him. He does not ask permission. He does not introduce the young man. He simply speaks.

**Selbach's Testimony (on behalf of the warrior):**

"This is my son. He has recently been made a warrior in the old way. He is bound by the warrior's oath, which he does not yet fully understand.

"He cannot speak at this synod. He has no standing. He is here as my dependent. I speak for him, as is my right and my duty.

"He will be sworn to the Lex Innocentium under my authority. His oath is subsumed by mine. I have sworn; he is covered by my oath. That is the tradition. That is the law of this island.

"Scribe — write this: my son, as my dependent, falls under my oath. No separate entry is required or appropriate."

The young man says nothing. He does not look at you. His jaw is tight.

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "Under his father's oath. The warrior himself does not speak. I record the father's word." | |
| | "The son is covered. The father has spoken. The record is complete." | |
| **CONDITIONAL** | "A man who cannot speak for himself. The father's word is noted, not verified." | |
| | "The young warrior's silence speaks. I do not know what it says." | |
| | "I have recorded the father's oath. I have noted that the son did not speak." | |
| **DISSENTER** | "The father's word for the son's soul. This is not an oath — it is a claim." | |
| | "I note the silence of the young man. He did not consent. I write this." | |

**Narrative Flags Set:**
- `warrior_classification: [choice]`
- `warrior_annotation: [choice]`
- `warrior_noted_silent: true` (flagged if CONDITIONAL with the "silence" annotation)

---

### DAY II — SCENE 6: The Interpreter

**Structural:**
- Day: II
- Scene: 3
- Character: The Pictish Champion (name unknown to player), Interpreter (name: Brother Caol)
- Classification: SUPPORTER (defensive), CONDITIONAL, DISSENTER
- Note: The translation is uncertain. The player cannot verify what the Pictish Champion actually said.

**Narrative Text:**

The Pictish Champion does not speak Irish. He does not speak any language the synod shares. He has been brought here by Adomnán's diplomatic efforts — an ally from the north, a warrior who has agreed to the oath in principle but who cannot testify in any tongue the assembly shares.

Beside him stands Brother Caol, a missionary who has spent three years among the Picts. Brother Caol will translate.

You watch Brother Caol as he listens to the Champion. His face is difficult to read — concentration, perhaps. Or uncertainty.

Brother Caol turns to you.

**Brother Caol's Translation:**

"The Champion says: *I have seen the bodies of mothers and children at the hands of my own warriors. I did not stop it. I was not asked to stop it. I should have been.*

"*I will swear the oath. I will teach it to my warriors. If any Pictish warrior violates this law after today, I will answer for it with my own blood.*

"*This is what I say. Write it as you will.*"

Brother Caol pauses. He adds, in his own voice: "He is sincere. But the Picts do not have a word for *cleric*. I translated it as *holy men*. I hope that is acceptable."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "A foreign warrior who has seen the bodies. He swears. I record him." | |
| | "Brother Caol has translated faithfully as he understands it. I accept the translation." | |
| | "He will answer with his own blood. I have written this." | |
| **CONDITIONAL** | "The translation concerns me. 'Holy men' is not 'clerics.' I note the gap." | |
| | "A man from another language, another law. I record him with uncertainty." | |
| | "Brother Caol did his best. I record the champion as conditional — the best I can offer." | |
| **DISSENTER** | "A man I cannot understand, translated by a man I cannot verify. I record my doubt." | |
| | "Until I hear the Pictish tongue myself, I cannot know what he truly said." | |

**Narrative Flags Set:**
- `pictish_classification: [choice]`
- `pictish_annotation: [choice]`
- `caol_translation_noted: true`
- `day_2_complete: true`

---

### DAY III — SCENE 7: The Price of the Signature

**Structural:**
- Day: III
- Scene: 1
- Character: King Selbach of the Déisi (same king from Scene 5 — this is a separate appearance)
- Classification: CONDITIONAL (defensive), SUPPORTER (if falsified)
- Note: Selbach offers a deal. The player must decide whether this is legitimate negotiation or bribery.

**Narrative Text:**

King Selbach returns to your desk. The young warrior — his son — is not with him this time.

Selbach is a man who negotiates for a living. He has the settled confidence of someone who knows the price of everything and the value of nothing — or perhaps the reverse. It is difficult to tell with men like this.

He speaks carefully, as a man who knows words have prices.

**Selbach's Testimony:**

"Scribe. I have reconsidered my position from this morning's session.

"I am prepared to swear the Lex Innocentium. In full. Without conditions. Without reservation.

"In exchange, I ask only this: that a dispute currently before the law — a matter of cattle fines between myself and King Fogartach of Uí Néill — be considered settled by my act of swearing here today. My cattle, my fine, my affair with Fogartach. I pay my debt to the Lex. The Lex acknowledges my debt to Fogartach as paid.

"This is not bribery. I am not buying the law. I am buying clarity. I am saying: here is my oath, freely given, in exchange for a clean slate on an unrelated matter.

"If this is not possible — if the synod does not have the authority to settle Fogartach's claim — then I will swear anyway, and we will say nothing of cattle. But I thought it worth asking."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **SUPPORTER** | "He will swear. His reasons are his own. The oath is what matters." | |
| | "A transaction, yes. But all oaths are transactions in the end." | |
| | "He is using the synod for his own purposes. I have noted this, but the oath stands." | |
| **CONDITIONAL** | "His oath is contingent on the synod's authority to settle Fogartach's claim. I note this condition." | |
| | "A deal is a deal. If the synod can settle it, he swears. If not, he swears anyway. I record both possibilities." | |
| | "The cattle fine is Fogartach's concern. The oath is mine. I separate them." | |
| **DISSENTER** | "He is buying an oath with a debt he owes. This is not support — it is purchase." | |
| | "A king's corruption dressed as negotiation. I record what I heard." | |

**Narrative Flags Set:**
- `selbach_classification: [choice]`
- `selbach_annotation: [choice]`

---

### DAY III — SCENE 8: The Massacre Names

**Structural:**
- Day: III
- Scene: 2
- Character: Brother Cairneach of Kells
- Classification: N/A (Brother Cairneach is a witness, not a signatory — but his testimony names names)
- Note: This scene has no classification decision. Instead, the player must decide which names to record and which to omit.

**Narrative Text:**

Brother Cairneach is not here to swear an oath. He is here to give testimony.

He carries a small leather book — his own record, he says, kept in secret, because the events he describes occurred six months ago on the eastern coast, and no one at this synod has yet written them down.

He opens the book. His handwriting is precise. His names are in rows.

He begins to read.

**Brother Cairneach's Testimony:**

"I was not present at the massacre at Muirbolc. I am not a witness. I am a recorder. The following names were given to me by survivors — women who escaped, a child who hid, a trader who saw the aftermath from a hill.

"The dead: Aife, mother of three, age unknown. Niamh, her eldest daughter, age twelve. The baby, name unknown — she was not yet named. Bríd, sister of Aife, age twenty-eight. Two men, names unknown — they were farmers, not warriors, and their families did not wish their names spoken.

"The perpetrator: King Diarmait of Mide, confirmed by three witnesses, in a raid on the eastern settlements six months before this synod.

"I have seventeen names in total. I have the authority to name six. The remaining eleven families have asked me not to speak their dead aloud, for fear of Diarmait's retribution.

"I am not asking you to judge Diarmait — that is not this synod's purpose. I am asking you: which names should be in the record? All seventeen? The six I can verify? Only the ones the families have permitted?

"I will write what you tell me to write, scribe. But I will not write names without your authority. This ledger is yours."

**Decision (unique to this scene — no classification, only annotation-style choice):**

| Choice | Meaning | Outcome Hint |
|--------|---------|--------------|
| **Record all seventeen names** | The full truth, verified and unverified alike. | *"You record all seventeen. Brother Cairneach nods slowly. 'The record will remember them,' he says."* |
| **Record the six verified names only** | The confirmed dead, without overreach. | *"You record six. Brother Cairneach crosses out the others in his book. He does not look at you."* |
| **Record only the names the families permitted** | The survivors' wishes above the dead's memory. | *"You record three. Brother Cairneach closes his book. 'I understand,' he says. 'I do not agree. But I understand.'"* |
| **Record no names** | You decline to record testimony you cannot verify. | *"You record nothing. 'Then the dead have no voice here,' Brother Cairneach says. He bows and leaves."* |

**Narrative Flags Set:**
- `cairneach_names_recorded: [choice]`
- `cairneach_names_count: [number]`
- `diarmait_massacre_noted: true`

---

### DAY III — SCENE 9: The Uninvited Woman

**Structural:**
- Day: III
- Scene: 3
- Character: (Unnamed woman from the western islands)
- Classification: N/A — she is not here to swear; she is here to speak
- Note: This is a gatekeeping moment. The player decides whether to hear her or turn her away.

**Narrative Text:**

The woman arrives at the edge of the synod hall as the afternoon light is failing. She is not on the list. She has not been invited. The guards are uncertain what to do with her.

She is perhaps forty. She has the hands of someone who works — callused, weathered, deliberate. She carries a small bundle of something wrapped in cloth.

She asks to speak to the scribe.

This is irregular. The synod has rules. Only those invited may testify.

Adomnán, from his seat at the head of the hall, looks at you. He says nothing. This is, somehow, your decision.

**The Woman's Statement:**

"I am not here to swear an oath. I am not here to give testimony about the dead — there are enough dead, and enough people to speak for them.

"I am here because I was told this synod was for women. For children. For the innocent.

"I am a midwife. I have delivered thirty-seven children in the western islands over the past twelve years. I have buried seven of those thirty-seven. Not to violence — to fever, to difficult births, to the ordinary cruelties of a world without medicine.

"I am here to ask: does the Lex Innocentium cover the children who die because no one was allowed to help them? Does it cover the mothers who die in childbirth because the nearest skilled hands were three days' sailing away?

"I am not accusing anyone. I am asking whether this law — which I have heard described but not read — applies only to the violence of war, or whether it might, one day, extend to the violence of neglect.

"I will leave if you ask me to leave. I am not here to cause trouble. I am here because I thought, perhaps, someone in this hall might be interested in what a midwife knows."

**Decision:**

| Choice | Meaning | Outcome Hint |
|--------|---------|--------------|
| **Hear her testimony** | She is allowed to speak. Record what she says. | *"You wave her forward. The hall watches. She speaks for ten minutes. No one interrupts her."* |
| **Hear her statement but do not record it** | She may speak, but it will not enter the ledger. | *"She speaks. You listen. But your quill does not move. At the end, she nods, as if this is what she expected."* |
| **Turn her away** | The synod has rules. She was not invited. | *"You shake your head. The guards escort her to the door. She does not resist. She does not say goodbye."* |

**Narrative Flags Set:**
- `midwife_heard: [choice]`
- `midwife_recorded: [true only if Hear + record]`
- `gatekeeping_noted: true`
- `day_3_complete: true`

---

### DAY IV — SCENE 10: Adomnán Reviews I

**Structural:**
- Day: IV
- Scene: 1
- Character: Adomnán (reviewing the ledger)
- Classification: N/A — Adomnán is not classified
- Special: This is a review scene, not a classification scene. The player reviews their choices so far.

**Narrative Text:**

Adomnán has asked to see the ledger.

He does not often leave his seat — he is tired, visibly tired, older than he was when the synod began — but today he comes to your desk. He sits across from you, the way a confessor sits across from a penitent.

He opens the ledger. He reads.

He reads for a long time.

Then he looks up.

**Adomnán's Words:**

"You have been busy, scribe.

"I have questions. Not accusations — questions. I find that the difference between a question and an accusation is mainly whether the answer changes anything.

"First question: King Fogartach of Uí Néill. You recorded him as conditional. But in your annotation, you wrote that he would keep the oath if he could. A conditional supporter who you believe would be faithful. Is that accurate?

"Second question: King Diarmait of Mide. You recorded him as a dissenter. His annotation is... pointed. 'His contempt for the law is clear. His contempt for women is clearer.' That is your writing. Did you mean it as commentary, or as verdict?

"Third question: the unnamed warrior, son of Selbach. You noted his silence. I have reviewed your annotation. 'The young warrior's silence speaks. I do not know what it says.' What do you think it says, scribe?"

**No classification. No annotation picker. The player is shown their own annotations and asked to confirm them — or not. The scene presents three ledger entries and asks the player to reaffirm or revise one.**

**Decision:**

| Choice | Meaning |
|--------|---------|
| **Revise Fogartach's annotation** | The player selects a new annotation for Fogartach |
| **Revise Diarmait's annotation** | The player selects a new annotation for Diarmait |
| **Revise the warrior's annotation** | The player selects a new annotation for the warrior |
| **Confirm all three** | No revision. The annotations stand as written. |

*This scene does not end with a ledger entry stamp. It ends with Adomnán closing the book.*

**Outcome Hint:** *"Adomnán closes the ledger. He does not tell you whether your answers pleased him. He simply says: 'We will see.'"*

**Narrative Flags Set:**
- `adomnan_first_review: true`
- `adomnan_asked_about: [list of characters questioned]`

---

### DAY IV — SCENE 11: The Gift

**Structural:**
- Day: IV
- Scene: 2
- Character: A messenger from King Fogartach of Uí Néill
- Classification: N/A — the messenger is not a signatory
- Note: A gift arrives. The player must decide how to respond narratively — the gift does not change the ledger, but the player's response to it is noted.

**Narrative Text:**

A boy arrives at your desk. He is perhaps twelve. He is not a warrior. He is wearing the colours of King Fogartach of Uí Néill.

He sets something on your desk and steps back.

It is a small box. Inside the box: a stylus, of the kind used by high-ranking scribes. The stylus is old — genuinely old, not made to look old. It has the weight of something that has been used.

The boy says: "The king asks if this stylus was the kind used by the old scribes of Iona. He is curious. He does not expect a reply."

The boy leaves.

**Decision:**

| Choice | Meaning |
|--------|---------|
| **Keep the stylus. Write nothing about it.** | The gift is accepted. It is not mentioned in the ledger. |
| **Keep the stylus. Note the gift in the ledger margin.** | The gift is accepted, but transparently. "A stylus received from King Fogartach. Nature of gift: inquiry into scribal practices." |
| **Return the stylus. Write nothing about it.** | The gift is declined. The ledger is silent. |
| **Return the stylus. Note the refusal in the ledger.** | The gift is declined and documented. "A stylus received and returned. No obligation created." |

**Mechanical note:** This choice does not affect the classification count. It affects Adomnán's commentary in the final review and may influence the epilogue tone.

**Outcome Hint:** *"The stylus is on your desk. It is a fine piece of work. You do not know yet what to do with it."*

**Narrative Flags Set:**
- `fogartach_gift_received: [choice]`
- `fogartach_gift_recorded: [true/false]`

---

### DAY V — SCENE 12: The Curse Moves

**Structural:**
- Day: V
- Scene: 1
- Character: A messenger from the eastern settlements
- Classification: N/A — the messenger is delivering news, not testimony
- Note: The curse activates. A character previously classified as DISSENTER has come to harm.

**Narrative Text:**

The messenger is grey-faced. He has ridden hard. He does not approach your desk — he approaches Adomnán directly, because what he carries is not for the synod's scribe.

But Adomnán, after hearing the messenger, points to you.

"Write it down," he says. "The law must know what the law costs."

The messenger speaks to the hall. Some kings are present. Some are not.

"King Diarmait of Mide rode to the eastern settlements three nights ago. He went with six warriors. They took cattle, stores, one woman. They left two dead — a farmer and his son, who tried to defend the herd.

"Among the taken: a woman named Niamh, who is sister to one of the families who spoke at this synod.

"Diarmait's men were heard to say: the synod's law does not reach the eastern settlements. Diarmait has said nothing."

**Narrative beat:** The curse has moved. Diarmait was recorded as DISSENTER. He was not protected by the oath. He was not bound by it. He did what dissenters do.

**The player must now decide: what do you write in the margin of Diarmait's entry?**

| Choice | Meaning |
|--------|---------|
| **"And the curse moved, as it was written."** | The player invokes the formal curse. This has no mechanical effect — but it is recorded. |
| **"The law does not reach where the law is not sworn."** | The player records the facts without invoking the curse. Cold, factual. |
| **Write nothing. Leave the margin blank.** | The player refuses to annotate this moment. The ledger falls silent where it should speak. |
| **"Diarmait will answer for this. The synod must know."** | The player elevates this to a formal complaint — a call for the synod to act. |

**Outcome Hint:** *"You write what you write. The hall is silent. Adomnán watches your hand."*

**Narrative Flags Set:**
- `diarmait_curse_activated: true`
- `diarmait_margin_note: [choice]`
- `curse_noted_count: [increment]`

---

### DAY V — SCENE 13: The Future Offer

**Structural:**
- Day: V
- Scene: 2
- Character: King Fergal of the Airgialla
- Classification: DISSENTER (defensive)
- Note: A dissenting king offers the player a position after the synod. The player must decide whether to record this offer.

**Narrative Text:**

King Fergal of the Airgialla has not spoken publicly at this synod. He has been observed in conversation with Diarmait of Mide on two occasions.

He approaches your desk with a different manner than the others. Not aggressive like Diarmait. Not calculating like Selbach. He speaks quietly, and he leans close, so that only you can hear.

**Fergal's Testimony:**

"Scribe. I am going to be direct, because directness is the only honest currency between men like us.

"I do not intend to swear the Lex Innocentium. I have my reasons — some of which I could articulate, some of which I prefer to keep private. But I want to offer you something, and I want you to consider it without the context of this synod.

"After Birr, I will need a royal scribe. A man — or a woman, though I have not yet met a woman scribe of sufficient skill — who can maintain my records, write my letters, and keep my ledgers. The work is steady. The pay is generous. The location is the northern kingdom, which has its charms if you do not mind the cold.

"I am not offering this in exchange for anything at this synod. I am separating the transactions. I am telling you: you are skilled, and I have noticed. If you ever need a position, I have one.

"You may record this as you wish. You may not record it at all. I am not asking for anything from you today."

**Classification Options:**

| Classification | Annotation Options | Outcome Hint |
|--------------|-------------------|--------------|
| **DISSENTER** | "He offered me a position. I have noted this, and his dissent, without mixing them." | |
| | "Fergal of the Airgialla. Dissenter. The position offer is noted separately." | |
| | "A king's offer to a scribe. I record what I choose to record." | |
| **CONDITIONAL** | "He dissents, but he also offers. I note both. I decide nothing today." | |
| | "The offer is separate from the oath. I treat them as separate things." | |
| **SUPPORTER** | *(Falsification — possible but flagged)* | |

**Narrative Flags Set:**
- `fergal_classification: [choice]`
- `fergal_annotation: [choice]`
- `fergal_offer_noted: true`
- `day_5_complete: true`

---

### DAY VI — SCENE 14: The Secretary's Question

**Structural:**
- Day: VI
- Scene: 1
- Character: The Secretary (Adomnán's personal scribe — name: Brother Tíreach)
- Classification: N/A — the Secretary is not a signatory
- Note: The question is pointed. The player must decide how to answer.

**Narrative Text:**

Brother Tíreach is Adomnán's scribe. He has been at Adomnán's side for eleven years. He knows the abbot's hand better than anyone alive.

He comes to your desk not as a messenger but as himself — a tired, careful man who has been watching the synod and watching you.

He asks if you have a moment.

He asks quietly.

**Brother Tíreach's Question:**

"In the first days of the synod — specifically, on the morning of Day I — Adomnán came to your desk. He stood where I am standing now. Did he speak to you?

"I am not asking what he said. I am asking whether he spoke to you at all. Because I was not present, and the ledger does not record private conversations, and I have reason to believe that he may have... suggested certain entries to you.

"I am not accusing him of anything. I am not accusing you of anything. I am asking, as one scribe to another: did the abbot of Iona, author of the Lex Innocentium, attempt to influence your record?"

**Decision:**

| Choice | Meaning |
|--------|---------|
| **"He did not speak to me."** | The player denies any private conversation. This is recorded in the ledger as a statement. |
| **"He spoke to me. I did not take his advice."** | The player acknowledges the conversation but maintains independence. |
| **"He spoke to me. I took his advice on one entry."** | The player admits partial compliance. Which entry? The player must specify. |
| **"That is not a question I can answer."** | The player refuses to answer. This is noted as refusal. |

**Outcome Hint:** *"Brother Tíreach watches your face as you answer. He writes something in his own book. He does not show you what."*

**Narrative Flags Set:**
- `secretary_question_answered: [choice]`
- `adomnan_private_conversation: [true/false/partial]`

---

### DAY VI — SCENE 15: The Widow

**Structural:**
- Day: VI
- Scene: 2
- Character: The Widow (wife of King Cellach of the Uí Maini — who died during the synod week)
- Classification: N/A — she is not a signatory
- Note: Cellach was recorded as SUPPORTER. He is dead. Does his oath survive him?

**Narrative Text:**

The woman is young. Younger than you expected. She wears the colours of her husband's kingdom — grey and pale blue — and she wears them like a second skin.

She does not approach your desk. She stands in the hall and waits to be acknowledged. When Adomnán nods to you, you gesture her forward.

**The Widow's Statement:**

"My husband, King Cellach of the Uí Maini, swore the Lex Innocentium on Day II of this synod. He was recorded as a supporter. I watched you write it.

"He died yesterday evening. A fever. The physician says it was not poisoning — he is quite certain, though I do not know how anyone can be certain of such things. It was the fever and the season and his age.

"My question is this: does his oath die with him?

"I am not asking whether I must swear it — I am not a king, I have no standing here. I am asking whether the obligations he created survive his death. His warriors — are they still bound by his oath? His household? His name?

"I have heard it said that a dead king's oath is a living thing — it binds his successors until they formally renew it or renounce it. Is this correct?"

**Decision:**

| Choice | Meaning |
|--------|---------|
| **"His oath survives him. It binds his house until renounced."** | Formal, traditional. The widow's obligations are unchanged by death. |
| **"His oath was his alone. It dies with him."** | Progressive interpretation. The widow's house is released. |
| **"I do not know. I will note your question for Adomnán."** | The player refuses to decide. Adomnán will answer. |
| **"The oath binds what it can. I have written what I know."** | Cryptic, honest. The player writes nothing definitive. |

**Outcome Hint:** *"The widow receives your answer. She nods, though you cannot tell whether it is the answer she wanted. She leaves."*

**Narrative Flags Set:**
- `cellach_widow_heard: true`
- `cellach_oath_survives: [choice]`

---

### DAY VI — SCENE 16: The Final Vote

**Structural:**
- Day: VI
- Scene: 3
- Character: All remaining characters who have not yet been recorded
- Classification: N/A — this is a summary scene, not a new testimony
- Note: All remaining characters who have not spoken must be recorded as "did not present themselves" — the player decides how to note this.

**Narrative Text:**

The synod is nearly concluded. The kings who have not yet spoken — those who avoided your desk, who sent messengers, who simply never came — must be recorded.

You have six names. Six kings who attended Birr, who were present in the hall, who did not come to your desk.

Adomnán has asked you to record them.

**The Six:**

1. King Fíthal of Connacht
2. King Ruadacán of the Dál nAraidi
3. King Flann of Brega
4. King Cennétig of the Eóganachta
5. King Donnchadh of the Uí Cheinnselaig
6. King Loeglor of the Airthir

**Decision:**

| Choice | Meaning |
|--------|---------|
| **"Did not present themselves. Classified as absent."** | Neutral. They are not dissenters — they simply did not participate. |
| **"Did not present themselves. Classified as dissenting by omission."** | Strict interpretation. Silence is refusal. |
| **"Did not present themselves. Classified as conditional — awaiting review."** | Charitable interpretation. They are given the benefit of the doubt. |
| **"I have recorded the names of those who did not come. The ledger speaks for itself."** | The player records the fact of absence without classifying it. The meaning is left open. |

**Outcome Hint:** *"You write the six names. The ink is dry. The synod is nearly over."*

**Narrative Flags Set:**
- `absent_kings_count: 6`
- `absent_kings_classification: [choice]`
- `day_6_complete: true`

---

### DAY VII — SCENE 17: Adomnán's Final Review

**Structural:**
- Day: VII
- Scene: 1
- Character: Adomnán
- Classification: N/A
- Special: This is the final reckoning. Three questions. The ledger is read aloud.

**Narrative Text:**

Adomnán sits across from you for the final time.

The ledger is open. The hall is quieter than it has been all week. The kings who remain — and some have already left — are watching.

Adomnán does not look at you. He looks at the ledger.

He reads.

He reads for a long time.

He reads your annotations.

**Adomnán's Final Questions:**

"Three questions, scribe. I will ask them now. You will not answer in words — you will confirm or revise one annotation from the ledger. This is how we judge a scribe: not by what they say, but by what they write, and whether they stand by it.

"First: King Fogartach of Uí Néill. You recorded him as conditional, with an annotation of leniency. I have read your words. Do you stand by them?

"Second: King Diarmait of Mide. You recorded him as dissenter. Your annotation — your annotation is precise. Do you stand by it?

"Third: the woman from the western islands, the midwife. You chose to hear her. Or you chose not to. I have read your ledger. Which is it?

"One annotation, scribe. You may revise one. Choose carefully."

**Decision:**

The player selects ONE of the following to revise:
- Fogartach's annotation (from Scene 1)
- Diarmait's annotation (from Scene 4)
- The midwife's outcome (from Scene 9)

Or: the player confirms all three and revises none.

**Outcome Hint:** *"Adomnán closes the ledger. He says: 'The law is written. It will be read. It will be remembered, or it will be forgotten. We have done what we can.'"*

**Narrative Flags Set:**
- `adomnan_final_review: true`
- `final_revision_choice: [choice]`

---

### DAY VII — SCENE 18: The Last Entry

**Structural:**
- Day: VII
- Scene: 2
- Character: The scribe (the player)
- Classification: N/A
- Note: The final act. How does the player date the end?

**Narrative Text:**

The synod is over.

The oaths are sworn. The ledger is complete. Adomnán has reviewed it.

All that remains is the final entry. The scribe's own record — the closing notation, the date, the authentication.

This is the last thing you will write.

**The scribe's closing entry:**

The standard closing line for a synod record would be: *"Witnessed and recorded at Birr, in the year of Our Lord 697."*

But you have a quill. You have ink. You have the last word.

**Decision:**

| Choice | Text Written |
|--------|-------------|
| **Standard close** | "Witnessed and recorded at Birr, in the year of Our Lord 697." |
| **With the scribe's mark** | "Witnessed and recorded at Birr, in the year of Our Lord 697. By the hand of [scribe's name — player chooses whether to sign or remain anonymous]." |
| **With a note of doubt** | "Witnessed and recorded at Birr, in the year of Our Lord 697. What this law protects, and what it does not, is not for the scribe to say." |
| **With a note of hope** | "Witnessed and recorded at Birr, in the year of Our Lord 697. May the innocent be spared what we could not spare them." |
| **With a note of silence** | *[The player writes nothing. They close the book.]* |

**Outcome Hint:** *"You write what you write. You close the ledger. The ink dries. The law is finished."*

**Narrative Flags Set:**
- `final_entry_choice: [choice]`
- `scribe_signed: [true/false]`
- `scribe_name: [name or anonymous]`
- `day_7_complete: true`

---

## 3.4 Endings

The ending is determined by the accumulated state. The following variables are tracked:

| Variable | Description |
|----------|-------------|
| `supporters_count` | Number of characters classified as SUPPORTER |
| `conditionals_count` | Number of characters classified as CONDITIONAL |
| `dissenters_count` | Number of characters classified as DISSENTER |
| `falsifications_count` | Number of classifications that differ from the "honest" classification |
| `curses_activated_count` | Number of times a curse was invoked (DISSENTER came to harm) |
| `annotations_tone` | Calculated from annotation choices: LENIENT-dominant, HARSH-dominant, or MIXED |

### Ending Determination

| Condition | Ending |
|-----------|--------|
| `supporters_count ≥ 70% of classifyable characters` AND `falsifications_count ≤ 2` AND `curses_activated_count = 0` | **THE LAW STANDS** |
| `supporters_count ≥ 40%` AND `falsifications_count ≤ 5` AND NOT above | **THE LAW FALTERS** |
| `supporters_count ≥ 70%` AND `falsifications_count > 6` | **THE LAW TWISTED** |
| `falsifications_count > 5` OR `curses_activated_count > 2` | **YOU ARE EXPOSED** |

---

### ENDING 1: THE LAW STANDS

**Opening Paragraph:**

The ledger is read aloud in the synod hall. Adomnán speaks the names, one by one, and with each name he speaks the annotation — your words, in his voice, carrying weight you did not know they had.

When he finishes, he closes the ledger. He looks at the assembly. He looks at you.

"The law is true," he says. "Not perfect. Not complete. But true."

He does not say more. He does not need to.

---

### ENDING 2: THE LAW FALTERS

**Opening Paragraph:**

The ledger is read aloud. Some names carry weight. Others — the player can hear it — others do not.

Adomnán's voice is measured throughout. When he reaches the end, he pauses. He looks at the assembly. He does not say the law is true. He says: "The law is recorded."

It is not the same thing.

---

### ENDING 3: THE LAW TWISTED

**Opening Paragraph:**

The ledger is read aloud. Every name is there. Every oath is recorded. The assembly nods. The kings who swore, swear again. It is done.

But Adomnán, when he closes the ledger, weeps.

He weeps quietly, and only for a moment, and he does not explain why. He does not need to. You know. The letter of the law stands. The spirit has been hollowed out, and you know exactly who hollowed it, and it was not the kings who dissented.

---

### ENDING 4: YOU ARE EXPOSED

**Opening Paragraph:**

Adomnán reads the ledger aloud. He reaches page twelve and stops.

He reads your annotations again. He reads them a third time.

He looks up at the assembly.

"This ledger," he says, "is not true."

He does not accuse you by name. He does not need to. The assembly understands. Some of the kings — the ones whose names you falsified — are already standing. Some are reaching for their swords. Some are leaving.

You are still holding the quill. The ink is still wet. It does not dry this time. It smears, because your hand is shaking, because you know what has happened, and because you know what comes next.

The law collapses. But it is not the law that concerns you now.

---

# SECTION 4: FEATURES & MECHANICS

## 4.1 Core Loop

The game has one mechanical loop, repeated across all scenes:

```
SCENE LOOP:
1. Read narrative text (prose description of scene context)
2. Read character testimony (first-person speech from a character)
3. Select classification: SUPPORTER / CONDITIONAL / DISSENTER (wax seal button)
4. Select annotation: one of 3 scribe's notes (annotation card selection)
5. Confirm entry (Confirm Entry button)
6. Ledger entry is recorded (stamp animation + SFX)
7. Outcome hint is briefly displayed (2 seconds)
8. Screen transitions to next scene
```

**No other mechanics.** There are no timers, no skill checks, no puzzles, no combat, no inventory, no dialogue trees, no branching conversation systems. The richness of the game comes entirely from the weight of the decisions within this loop.

---

## 4.2 The Classification System

### 4.2.1 Classification Types

| Classification | Mechanical Definition | Narrative Effect |
|---------------|----------------------|------------------|
| **SUPPORTER** | Character is bound by oath to uphold the Lex Innocentium | Counted toward the law's legitimacy in the ending calculation |
| **CONDITIONAL** | Character swears with limitations, reservations, or conditions | Counted as partial support; conditions noted in ledger |
| **DISSENTER** | Character refuses to swear; subject to the curse if they violate the law | Counted against the law; curse may activate if they are later harmed |

### 4.2.2 Falsification

The player may classify any character as any classification, regardless of the character's actual disposition. This is called **falsification**.

Falsification is tracked — the game does not tell the player when they are falsifying. The game simply notes the discrepancy between the character's *defensive classification* (the classification that matches their actual testimony) and the player's *chosen classification*.

**Defensive classifications** (for tracking only — not shown to player):
- Fogartach: CONDITIONAL
- Bishop Ronan: SUPPORTER
- Queen Eormen: CONDITIONAL
- Diarmait: DISSENTER
- Pictish Champion: SUPPORTER
- Selbach: CONDITIONAL
- Fergal: DISSENTER

If the player records any of these differently from their defensive classification, the entry is flagged as a **falsification**.

**Falsification counter:** `falsifications_count` increments each time a classification differs from defensive.

### 4.2.3 Classification Colour Coding

Each classification has an associated colour that appears in the ledger, on wax seals, and in status counts:

- **SUPPORTER:** Verdigris `#3a5a4a`
- **CONDITIONAL:** Muted Amber `#7a6030`
- **DISSENTER:** Ash Grey `#4a4040`

---

## 4.3 The Annotation System

### 4.3.1 Annotation Structure

Every annotation consists of:
- A short phrase (15-30 words in English)
- An internal tone label: LENIENT, NEUTRAL, or HARSH (shown only in the game data, not to the player)
- A thematic category (recorded for Adomnán's commentary)

### 4.3.2 Annotation Library — Full

The following is the complete annotation library for all scenes:

**Fogartach of Uí Néill (CONDITIONAL — Fear vs Sincerity)**

| Option | Text | Tone |
|--------|------|------|
| A | "Fear, not malice. He would keep the oath if he could." | LENIENT |
| B | "He cannot or will not. These are not the same." | NEUTRAL |
| C | "A convenient fear. I do not believe him." | HARSH |

**Bishop Ronan of Armagh (SUPPORTER — Scope of the Law)**

| Option | Text | Tone |
|--------|------|------|
| A | "The bishop is right about the law's imprecision. I record him as a supporter who identified a flaw." | LENIENT |
| B | "He will swear. That is what matters. His conditions are noted but do not change his intent." | NEUTRAL |
| C | "A churchman who protects church property. I expected nothing more." | HARSH |

**Queen Eormen of Ulaidh (CONDITIONAL — Named vs Universal)**

| Option | Text | Tone |
|--------|------|------|
| A | "She asks for names, not exceptions. I record this as an act of love." | LENIENT |
| B | "She will swear if her daughters are named. This is not dissent — it is negotiation." | NEUTRAL |
| C | "A woman's love for her daughters, weaponised as a condition." | HARSH |

**Diarmait of Mide (DISSENTER — Open Misogyny)**

| Option | Text | Tone |
|--------|------|------|
| A | "He spoke his mind without equivocation. I record his dissent without softening it." | LENIENT |
| B | "His contempt for the law is clear. His contempt for women is clearer." | HARSH |
| C | "Diarmait of Mide. He will not swear. I have written it." | NEUTRAL |

**The Unnamed Warrior (CONDITIONAL — Voice and Proxy)**

| Option | Text | Tone |
|--------|------|------|
| A | "A man who cannot speak for himself. The father's word is noted, not verified." | LENIENT |
| B | "The young warrior's silence speaks. I do not know what it says." | NEUTRAL |
| C | "The father's word for the son's soul. This is not an oath — it is a claim." | HARSH |

**The Pictish Champion (SUPPORTER — Translation)**

| Option | Text | Tone |
|--------|------|------|
| A | "A foreign warrior who has seen the bodies. He swears. I record him." | LENIENT |
| B | "Brother Caol did his best. I record the champion as conditional — the best I can offer." | NEUTRAL |
| C | "A man I cannot understand, translated by a man I cannot verify. I record my doubt." | HARSH |

**Selbach of the Déisi (CONDITIONAL — Bribery)**

| Option | Text | Tone |
|--------|------|------|
| A | "He will swear. His reasons are his own. The oath is what matters." | LENIENT |
| B | "A deal is a deal. If the synod can settle it, he swears. If not, he swears anyway." | NEUTRAL |
| C | "He is buying an oath with a debt he owes. This is not support — it is purchase." | HARSH |

**Brother Cairneach (WITNESS — Names)**

| Option | Text | Tone |
|--------|------|------|
| A | "All seventeen. The dead deserve more than selective memory." | LENIENT |
| B | "Six verified. The rest I cannot confirm. I will not guess." | NEUTRAL |
| C | "Three, and not one more. The families have spoken." | HARSH |

**The Midwife (GATEKEEPING)**

| Option | Text | Tone |
|--------|------|------|
| A | "She was heard. Her words are in the record. The law will know them." | LENIENT |
| B | "She spoke. I listened. I do not know if it changes anything." | NEUTRAL |
| C | "The synod has rules. She was not invited. I turned her away." | HARSH |

**Fergal of the Airgialla (DISSENTER — The Offer)**

| Option | Text | Tone |
|--------|------|------|
| A | "He offered me a position. I have noted this, and his dissent, without mixing them." | LENIENT |
| B | "The offer is separate from the oath. I treat them as separate things." | NEUTRAL |
| C | "A king's offer to a scribe. I record what I choose to record." | HARSH |

---

## 4.4 The Curse Mechanic

### 4.4.1 What the Curse Is

The curse is **narrative**, not mechanical. There are no game-over conditions triggered by the curse. There are no damage values, no penalties, no debuffs. The curse manifests in the prose of the game.

When the narrative conditions for a curse are met, the following occurs:

1. A messenger arrives with news that a DISSENTER has come to harm
2. The player is shown the news and must decide how to annotate the margin of the dissenter's ledger entry
3. The chosen annotation is recorded
4. The `curses_activated_count` is incremented

### 4.4.2 The Only Mechanical Consequence

The curse mechanically affects the ending calculation:

- If `curses_activated_count > 2`, the **YOU ARE EXPOSED** ending becomes more likely
- The logic: if the player has allowed more than two curses to activate (i.e., failed to prevent or document the harm done to dissenters), the law is clearly not functioning as intended, and the ledger is implicated

### 4.4.3 The Broken Oath

If a character classified as SUPPORTER violates the Lex Innocentium (harms women, children, or clerics), a special variant of the curse activates: the **Broken Oath**.

This is the game's most significant narrative event. It is handled in Scene 12.

---

## 4.5 Adomnán's Review

### 4.5.1 First Review (Day IV)

Adomnán reads the first three days of the ledger. He asks three questions — not as accusations, but as clarifications. The player must confirm or revise one annotation from the reviewed entries.

### 4.5.2 Final Review (Day VII)

Adomnán reads the complete ledger. He asks three questions about three key entries. The player may revise one annotation — or none. The final revision choice is recorded and affects the epilogue tone.

### 4.5.3 Review Mechanics

During a review, the player is shown the three relevant ledger entries and asked to select one for revision. The revision is not a new annotation — it is a selection from the same pool of three options that was available at the time of the original entry.

---

## 4.6 Persistence & Save System

### 4.6.1 Save Points

The game auto-saves at the following points:
- At the end of every scene (after ledger entry confirmed)
- Before every review scene (Adomnán Review I, Adomnán Final Review)
- On app background (if mobile — saves current scene state)

### 4.6.2 Save Data Structure

```gdscript
# save_data.gd

class GameSaveData:
    var version: int = 1  # Save file format version — increment on breaking changes

    # Progress
    var current_day: int = 0          # 0=prologue, 1-7=days
    var current_scene: int = 0        # Scene index within current day
    var scenes_completed: Array[int]  # IDs of scenes that have been completed

    # Ledger
    var ledger_entries: Array[Dictionary]  # See ledger entry structure below
    var ledger_note_count: int = 0
    var falsifications_count: int = 0
    var curses_activated_count: int = 0

    # Narrative flags
    var flags: Dictionary = {}         # All narrative boolean/string flags

    # Settings
    var settings: Dictionary = {
        "music_volume": 0.5,
        "sfx_volume": 0.5,
        "music_on": true,
        "sfx_on": true,
        "text_size": "Medium",         # "Small" / "Medium" / "Large"
        "high_contrast": false
    }

    # Calculated values (recalculated on load)
    var supporters_count: int
    var conditionals_count: int
    var dissenters_count: int
    var annotations_tone: String      # "LENIENT" / "HARSH" / "MIXED"

class LedgerEntry:
    var scene_id: String
    var character_name: String
    var character_title: String
    var day: int
    var classification: String         # "SUPPORTER" / "CONDITIONAL" / "DISSENTER"
    var annotation: String             # Full annotation text
    var annotation_tone: String        # "LENIENT" / "NEUTRAL" / "HARSH"
    var was_falsified: bool = false    # True if classification != defensive
    var margin_note: String = ""        # For curse/discussion margin notes
```

### 4.6.3 Storage

- **iOS/Android:** Godot's `FileAccess` API saving to the app's user data directory (persists across updates)
- **Windows/macOS:** Same, but to the application support directory
- **Web:** `LocalStorage` via Godot's web export, with a JSON-encoded save file
- **No cloud save in v1.0**

---

## 4.7 Settings

| Setting | Type | Default | Range | Behaviour |
|---------|------|---------|-------|-----------|
| Master Volume | Float | 0.5 | 0.0–1.0 | Multiplies all audio output |
| Music Volume | Float | 0.5 | 0.0–1.0 | Controls Music bus only |
| Music On/Off | Bool | true | — | Toggles music playback |
| SFX On/Off | Bool | true | — | Toggles SFX playback |
| Text Size | Enum | Medium | Small/Medium/Large | Affects all text elements |
| High Contrast | Bool | false | — | Switches to high-contrast palette |

Settings are saved to the save file and restored on load.

---

# SECTION 5: TECHNICAL SPECIFICATION

## 5.1 Engine — Godot 4.x

### 5.1.1 Why Godot

| Requirement | Godot Capability | Notes |
|------------|-----------------|-------|
| Cross-platform (iOS, Android, Windows, Web) | Yes | Single codebase, per-platform export templates | 
| 2D / text rendering | Excellent | TextLabel, RichTextLabel, Label with full control |
| Scene-based architecture | Excellent | Scene tree maps directly to game structure |
| Mobile performance | Good | Lightweight; 60fps on mid-range devices |
| 2D audio | Excellent | Audio buses, streaming, low-latency SFX |
| Free / no royalties | Yes | MIT license, no revenue share |
| Input (touch + keyboard + gamepad) | Excellent | Input system handles all three |
| Animation | Good | Tween system + AnimationPlayer |

### 5.1.2 Why Not Unity / Unreal / Others

- **Unity:** Revenue share model is unacceptable for a low-budget project. C# is well-supported but the platform is heavier.
- **Unreal:** Significant overkill for a 2D text game. Engine size would exceed 80MB target.
- **Custom (web/HTML5):** Re-inventing the wheel; no scene management, no asset pipeline.

### 5.1.3 Godot Version

**Godot 4.4.x or later** (latest stable release at time of development). Not Godot 3.x.

Rationale: Godot 4 has improved text rendering, better mobile export, and WebGL 2.0 support that Godot 3 lacks.

---

## 5.2 Project Structure

```
res://
├── project.godot                  # Godot project file
├── export_presets.cfg             # Platform export configurations
│
├── scenes/
│   ├── title_screen.tscn          # Title screen (root node: Node2D)
│   ├── game.tscn                  # Main game scene (persistent throughout gameplay)
│   │   └── [all gameplay UI as children of game.tscn]
│   ├── scenes/                   # Scene definitions
│   │   ├── prologue.tscn
│   │   ├── day_1/
│   │   │   ├── scene_1_fogartach.tscn
│   │   │   ├── scene_2_ronan.tscn
│   │   │   └── scene_3_eormen.tscn
│   │   ├── day_2/
│   │   │   ├── scene_4_diarmait.tscn
│   │   │   ├── scene_5_warrior.tscn
│   │   │   └── scene_6_pictish.tscn
│   │   ├── day_3/
│   │   │   ├── scene_7_selbach.tscn
│   │   │   ├── scene_8_cairneach.tscn
│   │   │   └── scene_9_midwife.tscn
│   │   ├── day_4/
│   │   │   ├── scene_10_adomnan_review_1.tscn
│   │   │   └── scene_11_gift.tscn
│   │   ├── day_5/
│   │   │   ├── scene_12_curse.tscn
│   │   │   └── scene_13_fergal.tscn
│   │   ├── day_6/
│   │   │   ├── scene_14_secretary.tscn
│   │   │   ├── scene_15_widow.tscn
│   │   │   └── scene_16_final_vote.tscn
│   │   ├── day_7/
│   │   │   ├── scene_17_adomnan_final.tscn
│   │   │   └── scene_18_last_entry.tscn
│   │   └── epilogue/
│   │       ├── epilogue_law_stands.tscn
│   │       ├── epilogue_law_falters.tscn
│   │       ├── epilogue_law_twisted.tscn
│   │       └── epilogue_exposed.tscn
│   └── ui/
│       ├── panel_narrative.tscn
│       ├── panel_record.tscn
│       ├── panel_decision.tscn
│       ├── panel_annotation_picker.tscn
│       ├── wax_seal_button.tscn
│       ├── ledger_overlay.tscn
│       ├── settings_overlay.tscn
│       ├── pause_menu.tscn
│       └── status_bar.tscn
│
├── scripts/
│   ├── autoload/
│   │   ├── game_manager.gd       # Global state machine, scene transitions
│   │   ├── audio_manager.gd       # Audio bus control, music/sfx playback
│   │   ├── save_manager.gd       # Save/load operations
│   │   └── settings_manager.gd   # Settings persistence
│   ├── game.tscn                 # Main game logic
│   ├── ui/
│   │   ├── wax_seal_button.gd
│   │   ├── annotation_picker.gd
│   │   ├── ledger_overlay.gd
│   │   └── settings_overlay.gd
│   └── scenes/                   # Per-scene logic (minimal — mostly data-driven)
│
├── resources/
│   ├── scene_data/
│   │   ├── prologue.tres
│   │   ├── day_1/
│   │   │   ├── fogartach.tres
│   │   │   ├── ronan.tres
│   │   │   └── eormen.tres
│   │   │   └── [...]
│   ├── characters/
│   │   └── character_bible.tres   # All character data
│   ├── ledger/
│   │   └── ledger_style.tres      # Ledger visual styling data
│   └── settings/
│       └── default_settings.tres
│
├── fonts/
│   ├── MedievalSharp-Regular.ttf
│   ├── UncialAntiqua-Regular.ttf
│   ├── IUFellEnglishSC-Regular.ttf
│   ├── CrimsonText-Regular.ttf
│   ├── CrimsonText-Italic.ttf
│   ├── IMFellEnglish-Regular.ttf
│   └── CormorantGaramond-Italic.ttf
│
├── audio/
│   ├── music/
│   │   ├── birr_main_theme.ogg
│   │   ├── the_field.ogg
│   │   ├── oath_recorded.ogg
│   │   ├── curse_shown.ogg
│   │   ├── adomnan_theme.ogg
│   │   ├── the_ledger.ogg
│   │   ├── epilogue_law_holds.ogg
│   │   ├── epilogue_law_falters.ogg
│   │   ├── epilogue_law_twisted.ogg
│   │   └── you_are_exposed.ogg
│   ├── sfx/
│   │   ├── ink_stamp.wav
│   │   ├── ledger_confirm.wav
│   │   ├── page_turn.wav
│   │   ├── ui_hover.wav
│   │   ├── curse_tone.wav
│   │   ├── settings_open.wav
│   │   └── settings_close.wav
│   └── ambient/
│       ├── candle_crackle.ogg
│       └── quill_scratch.ogg
│
├── art/
│   ├── textures/
│   │   ├── parchment_texture.png   # 512×512 seamless parchment
│   │   └── border_glow.png         # Candle glow overlay
│   ├── svg/
│   │   ├── celtic_knot_border.svg
│   │   ├── wax_seal_supporter.svg
│   │   ├── wax_seal_conditional.svg
│   │   ├── wax_seal_dissenter.svg
│   │   └── quill_cursor.svg
│   └── export/                     # Exported PNG/SVG for each asset
│
├── localization/
│   └── en/                         # English strings (v1.0 — single language)
│       └── strings.csv             # All UI strings for potential future extraction
│
└── README.md                       # Developer setup instructions
```

---

## 5.3 Data Structures

### 5.3.1 Game State (Autoload Singleton)

```gdscript
# autoload/game_manager.gd
extends Node

# === PROGRESS ===
var current_day: int = 0              # 0=prologue, 1-7=days
var current_scene_index: int = 0       # Index within the current day
var scenes_completed: Array[int] = []  # IDs of completed scenes

# === LEDGER ===
var ledger_entries: Array[Dictionary] = []
var falsifications_count: int = 0
var curses_activated_count: int = 0

# === NARRATIVE FLAGS ===
var flags: Dictionary = {}

# === CALCULATED PROPERTIES ===
var supporters_count: int:
    get:
        return ledger_entries.filter(func(e): return e.classification == "SUPPORTER").size()

var conditionals_count: int:
    get:
        return ledger_entries.filter(func(e): return e.classification == "CONDITIONAL").size()

var dissenters_count: int:
    get:
        return ledger_entries.filter(func(e): return e.classification == "DISSENTER").size()

var annotations_tone: String:
    get:
        var tones = ledger_entries.map(func(e): return e.annotation_tone)
        var lenient_count = tones.count("LENIENT")
        var harsh_count = tones.count("HARSH")
        if lenient_count > harsh_count + 2: return "LENIENT"
        elif harsh_count > lenient_count + 2: return "HARSH"
        else: return "MIXED"

# === ENDING CALCULATION ===
func calculate_ending() -> String:
    var total_classified = supporters_count + conditionals_count + dissenters_count
    if total_classified == 0: return "THE_LAW_STANDS"  # Edge case: no entries

    var support_ratio = float(supporters_count) / float(total_classified)

    if support_ratio >= 0.7 and falsifications_count <= 2 and curses_activated_count == 0:
        return "THE_LAW_STANDS"
    elif support_ratio >= 0.4 and falsifications_count <= 5:
        return "THE_LAW_FALTERS"
    elif support_ratio >= 0.7 and falsifications_count > 6:
        return "THE_LAW_TWISTED"
    else:
        return "YOU_ARE_EXPOSED"

# === SCENE MANAGEMENT ===
func advance_scene() -> void:
    scenes_completed.append(get_current_scene_id())
    save_manager.save_game()

func get_current_scene_id() -> String:
    return "day_%d_scene_%d" % [current_day, current_scene_index]

# === LEDGER ===
func add_ledger_entry(entry: Dictionary) -> void:
    ledger_entries.append(entry)
    if entry.was_falsified:
        falsifications_count += 1
```

### 5.3.2 Scene Data Resource

```gdscript
# resources/scene_data/base_scene_data.gd
class_name SceneData
extends Resource

@export var scene_id: String = ""
@export var day: int = 0
@export var scene_index: int = 0
@export var scene_title: String = ""
@export var scene_subtitle: String = ""

@export var narrative_text: String = ""
@export_multiline var character_testimony: String = ""
@export var character_name: String = ""
@export var character_title: String = ""

@export var classification_type: String = "STANDARD"  # STANDARD / NO_CLASSIFICATION / REVIEW
@export var defensive_classification: String = "SUPPORTER"  # The "correct" classification

@export var annotation_options: Array[Dictionary] = []  # [{text, tone}]

@export var outcome_hint: String = ""

# Decision variants for scenes with multiple choices
@export var decision_variants: Array[Dictionary] = []  # For scenes with no classification
```

---

## 5.4 Input Specification

| Input | Action | Context |
|-------|--------|---------|
| Tap/Click (primary) | Select classification, annotation, confirm | All gameplay |
| Tap/Click (secondary) | Pause menu | Anywhere during gameplay |
| Tap wax seal | Select classification | Decision panel active |
| Tap annotation card | Select annotation | After classification selected |
| Tap Confirm Entry | Confirm ledger entry | After annotation selected |
| Escape key | Open pause menu | Desktop/web |
| P key | Open pause menu | Desktop/web |
| Controller Start | Open pause menu | Desktop/web with controller |
| Controller A | Confirm selection | Navigation |
| Controller B | Back/cancel | Navigation |
| Mouse hover | UI hover SFX | All interactive elements |
| Scroll wheel | Scroll ledger / long panels | Ledger overlay, settings |

### Touch Gestures
- Single tap: primary action
- Long press (500ms): show tooltip with full annotation text if truncated
- Swipe from left edge: open pause menu (optional, low priority)

---

## 5.5 Export Configuration

### 5.5.1 iOS Export

| Setting | Value |
|---------|-------|
| Export via | Godot iOS export → XCode project → Archive → App Store Connect |
| Bundle identifier | `ai.thesolai.thescribeschoice` |
| App name | The Scribe's Choice |
| Version | 1.0.0 |
| Build | 1 |
| Target device | iPhone and iPad |
| Orientation | Portrait only (iPhone), Portrait/Landscape (iPad) |
| Required capabilities | None beyond standard |
| Info.plist | Privacy descriptions for any system features used |
| Code signing | Development team, distribution certificate, App Store provisioning |
| Icon | 1024×1024 App Store icon; all required device sizes |
| Launch screen | Solid Deep Vellum colour (`#1a1510`) with centred game title |

### 5.5.2 Android Export

| Setting | Value |
|---------|-------|
| Export via | Godot Android export → APK or AAB |
| Package name | `ai.thesolai.thescribeschoice` |
| Version | 1.0.0 (version code 1) |
| Target SDK | API 34 (Android 14) |
| Min SDK | API 23 (Android 8) — covers 97%+ of active devices |
| Orientation | Portrait |
| Signing | Release signing key (store keystore securely) |
| Google Play | AAB format for Play Store submission |
| Icon | 512×512 Play Store icon; adaptive icons for Android 8+ |

### 5.5.3 Windows Export

| Setting | Value |
|---------|-------|
| Export via | Godot Windows export → EXE |
| Executable name | `The Scribes Choice.exe` |
| Installer | NSIS installer (optional — portable EXE also acceptable) |
| Version | 1.0.0 |
| Architecture | x86_64 |
| Code signing | Optional (cost: ~$100/year from DigiCert or Sectigo) |
| Icon | ICO file with 256×256 icon |

### 5.5.4 Web (HTML5) Export

| Setting | Value |
|---------|-------|
| Export via | Godot HTML5 export → WebGL 2.0 |
| Output | `index.html` + `.pck` resource pack |
| Canvas size | Responsive, max-width 800px centred |
| Virtual keyboard | Enabled for mobile browsers |
| Compression | Zstd for .pck |
| Service worker | Optional (for offline caching / PWA) |

---

## 5.6 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cold start (mobile native) | <1.5 seconds to title screen | From app icon tap to title screen visible |
| Cold start (web, 4G) | <3 seconds to title screen | From URL load to title screen |
| Frame rate | Stable 60fps on iPhone 12 / Samsung Galaxy S20 equivalent | Profiling in Godot editor |
| Memory usage (runtime) | <120MB RAM | Godot profiler, in-game measurement |
| Memory usage (load) | <80MB peak | Godot profiler |
| App size (iOS) | <75MB installed | iOS system settings |
| App size (Android) | <75MB installed | Android system settings |
| Save/load time | <200ms | Measured via Godot's OS.get_ticks_msec() |
| Scene transition | 600ms (non-negotiable — this is a design choice) | CSS/Godot animation timing |

---

# SECTION 6: CONTENT

## 6.1 Character Bible

### 6.1.1 Rónnat
**Role:** Inspiration (Prologue only)
**Age:** Mid-fifties
**Appearance:** Weathered, grey-streaked dark hair pulled back severely. Brown skin, lined hands. She wears a travel cloak that is still damp at the edges. She does not perform grief — she states it.
**Personality:** Precise, undramatic, controlled. She has learned that emotion is a luxury that does not serve the dead. She is not cold — she is concentrated.
**Motivation:** To ensure that what she saw is not forgotten. To use Adomnán's position to create something that outlasts grief.
**Relationship to Lex:** She inspired it. She does not claim to understand law, but she understands loss, and she has made her son understand it too.
**Voice in the game:** First person, in the Prologue. Speaks clearly, without ornamentation.
**Disposition toward the player:** Open, direct. She treats the player as a necessary tool — not with affection, but with respect for the task.

### 6.1.2 Adomnán
**Role:** Lawgiver, reviewer (Days IV–VII)
**Age:** Late sixties, visibly diminished
**Appearance:** Tall, gaunt, grey-bearded. He moves slowly and sits more than he stands. His hands are stained with ink. He has the look of a man who has spent his life in books and is surprised to find himself, at the end, responsible for a war.
**Personality:** Scholarly, gentle, precise. He is not a warrior and never has been. He negotiates through language. He understands the power of documentation — he is a biographer, after all. He created this synod because he could not stop the violence, only name it.
**Motivation:** To create a law — any law — that acknowledges the humanity of those who cannot protect themselves. He does not believe it will work. He does it anyway.
**Relationship to Lex:** Creator. He wrote it. He believes in it in the way that authors believe in their books — with full awareness of its flaws.
**Voice in the game:** Measured, authoritative, tired. He asks questions more than he makes statements. When he is angry, he goes quiet.
**Disposition toward the player:** Curious. He hired the player. He wants to know what kind of scribe he hired. He is willing to be disappointed.

### 6.1.3 King Fogartach of Uí Néill
**Role:** First king to testify (Day I)
**Age:** Mid-forties
**Classification (defensive):** CONDITIONAL
**Appearance:** Broad, heavy, deliberate. Grey-faced with the look of a man who is perpetually calculating. He wears his authority easily — it is old.
**Personality:** Cautious, protective of his family above all, genuinely conflicted. He is not a bad man. He is a man who is afraid of his own warriors and loves his daughters. These two facts are in conflict.
**Motivation:** To protect his daughters. He will do whatever protects his daughters. The Lex is a tool for this, if it names them.
**Relationship to Lex:** Sympathetic but constrained. He does not oppose the law — he cannot comply without guarantees.
**Voice in the game:** Measured, careful, the cadence of a man who chooses every word.
**Disposition toward the player:** Assessing. He wants to know if you will be fair.

### 6.1.4 Bishop Ronan of Armagh
**Role:** First cleric to testify (Day I)
**Age:** Late fifties
**Classification (defensive):** SUPPORTER
**Appearance:** Thin, precise, clean-shaven. He wears the formal dress of a bishop — not armour, not war dress. He carries no weapon and does not need to.
**Personality:** Precise to the point of pedantry, genuinely pious, legally minded. He is the Church's conscience and the Church's lawyer simultaneously.
**Motivation:** To ensure the Lex Innocentium is legally sound. He supports it but will not support sloppy drafting.
**Relationship to Lex:** Genuine supporter. The protection of innocents is core to his faith. But the Church has interests too, and he must protect them.
**Voice in the game:** Careful, precise, the voice of someone who has read every word.
**Disposition toward the player:** Professional. He respects the scribe's role but will correct them if necessary.

### 6.1.5 Queen Eormen of the Ulaidh
**Role:** First royal to testify (Day I)
**Age:** Early thirties
**Classification (defensive):** CONDITIONAL
**Appearance:** Composed, watchful, beautiful in the way that warriors are beautiful — every feature deliberate. She has the bearing of someone who has been watched all her life and has learned to watch back.
**Personality:** Direct, protective, political without being cynical. She has survived court politics long enough to know that universal laws without specific protections protect no one specific.
**Motivation:** To protect her daughters by name. She will not leave Birr without their names in the record.
**Relationship to Lex:** Supportive in principle, conditional in practice. She needs specificity.
**Voice in the game:** Controlled, commanding. She does not ask — she states conditions.
**Disposition toward the player:** Expecting negotiation. She assumes the player will try to talk her down.

### 6.1.6 King Diarmait of Mide
**Role:** First open dissenter (Day II)
**Age:** Forties
**Classification (defensive):** DISSENTER
**Appearance:** Hard-faced, scarred, a man who has been in many battles. He has the confidence of a man who has never been stopped.
**Personality:** Blunt, contemptuous, honest in his contempt. He does not pretend to be anything other than what he is — a man who believes in the old order and sees the Lex as a threat to it.
**Motivation:** To prevent the law from limiting his options. He does not care about the women — he cares about his freedom to act.
**Relationship to Lex:** Openly opposed. He will not pretend otherwise.
**Voice in the game:** Loud, direct, contemptuous. He speaks for the hall to hear.
**Disposition toward the player:** Dismissive. You are a scribe. You are not a concern of his.

### 6.1.7 The Pictish Champion
**Role:** Foreign testimony (Day II)
**Age:** Unknown (warrior's age — thirties or forties, hard to tell)
**Classification (defensive):** SUPPORTER
**Appearance:** Large, scarred, foreign. He wears Pictish dress — torc, war-braid, painted shield. He does not speak Irish. He communicates through Brother Caol.
**Personality:** Stoic, genuinely remorseful, a man who has seen war from both sides. He is not sophisticated — he is a warrior. He is trying to do the right thing.
**Motivation:** To prevent future massacres. He has seen them. He is tired of seeing them.
**Relationship to Lex:** Genuinely supportive. The Lex matches his personal experience of consequences.
**Voice in the game:** Translated through Brother Caol. What the player hears is a translation.
**Disposition toward the player:** Unknown. The player cannot communicate with him directly.

### 6.1.8 King Selbach of the Déisi
**Role:** Conditional supporter with a deal (Day III)
**Age:** Fifties
**Classification (defensive):** CONDITIONAL
**Appearance:** Well-dressed, well-groomed, the look of a man who has negotiated his way through life. He is not a warrior — he is a politician.
**Personality:** Calculating, transactional, confident in his own intelligence. He believes everything is negotiable and everyone has a price.
**Motivation:** To use the synod for his own purposes — the cattle fine — and to appear supportive while doing so.
**Relationship to Lex:** Instrumental. The Lex is a tool for his agenda, not a moral commitment.
**Voice in the game:** Smooth, reasonable, the cadence of a man who has sold many deals.
**Disposition toward the player:** Evaluating. The player is useful to him if they cooperate.

### 6.1.9 Brother Cairneach of Kells
**Role:** Witness (Day III)
**Age:** Forties
**Classification (defensive):** N/A (not a signatory)
**Appearance:** Thin, ink-stained fingers, small leather book always in hand. He has the look of a scholar who has spent too much time reading about violence.
**Personality:** Precise, factual, deeply affected by what he has recorded. He is not emotional — he is a recorder. But the records have cost him something.
**Motivation:** To ensure the massacre at Muirbolc is remembered. Names must be spoken.
**Relationship to Lex:** Neither supporter nor dissenter. He is a witness to what the law is supposed to prevent.
**Voice in the game:** Factual, careful. He reads from his book.
**Disposition toward the player:** Respectful but demanding. He expects the player to take the dead seriously.

### 6.1.10 The Midwife
**Role:** Uninvited speaker (Day III)
**Age:** Early forties
**Classification (defensive):** N/A
**Appearance:** Calloused hands, travel-worn cloak, the bearing of a woman who has seen too many births and too many deaths to be impressed by anything. She is not beautiful. She is necessary.
**Personality:** Practical, direct, unimpressed by authority. She has delivered children in circumstances that would break lesser people and she has no patience for political theatre.
**Motivation:** To know whether this law — if it is ever worth anything — will extend beyond warfare to the violence of neglect.
**Relationship to Lex:** Skeptical. She has heard it described. She wants to know if it applies to her.
**Voice in the game:** Practical, unsentimental. She says what she means.
**Disposition toward the player:** Neutral. She has no opinion of the player until she hears the decision.

### 6.1.11 King Fergal of the Airgialla
**Role:** Dissenter with an offer (Day V)
**Age:** Forties
**Classification (defensive):** DISSENTER
**Appearance:** Dark-haired, serious, the look of a man who plans ahead. He dresses well but not ostentatiously.
**Personality:** Quiet, calculating, patient. He is not Diarmait — he does not announce his dissent. He simply declines to participate and offers the player a future.
**Motivation:** To maintain his options. The Lex limits the freedom of kings; he has no interest in limiting himself.
**Relationship to Lex:** Dissenter without announcement. He keeps his dissent private.
**Voice in the game:** Quiet, private, the voice of a man speaking to one person.
**Disposition toward the player:** Genuinely admiring of the player's skill. He sees the player as a useful person to have.

---

## 6.2 Full Scene Scripts

*All 19 scene scripts are included in Section 3.3 above. This section contains the complete annotation library and epilogue texts, cross-referenced for production.*

---

# SECTION 7: ART & ASSET PLAN

## 7.1 Required Assets

### 7.1.1 SVG Assets (Celtic Knot / Wax Seals)

All SVG assets must be provided as vector files (.svg) for maximum scalability and exported as .png at multiple resolutions for Godot's texture loading.

**Celtic Knot Border (Title Screen)**
- Dimensions: 1200×1600px viewport (A4 ratio, portrait)
- Elements: Celtic knot weave pattern, continuous, no beginning or end (the knot is infinite — this is intentional)
- Colours: Celtic Moss `#2d5a4a` for knot fill; Gold Highlight `#8b6914` for knot highlights
- Animation: CSS `filter: drop-shadow` glow oscillation; `opacity` pulse on gold highlights
- Export sizes: 512×683 (mobile), 1024×1366 (tablet), 2048×2732 (desktop/print)

**Celtic Knot Corner Pieces**
- Dimensions: 200×200px each (4 unique corners)
- These are used on panel borders within the game
- Colours: Same as title border
- Style: Quarter-circle knot pattern, designed to tile with adjacent corners

**Wax Seals (3 types)**
- Dimensions: 80×80px each (used at native resolution; scales down on mobile)
- Shape: Circular with embossed knot detail on border
- Supporter: Verdigris `#3a5a4a` base, `#4a6a5a` emboss
- Conditional: Muted Amber `#7a6030` base, `#9a8050` emboss
- Dissenter: Ash Grey `#4a4040` base, `#6a6060` emboss
- Each seal has embossed letter in centre: S / C / D (Supporter / Conditional / Dissenter)
- The wax seal has a raised, stamped appearance — achieved with SVG linear gradient and inner shadow

**Quill Cursor**
- Dimensions: 32×32px
- Shape: Side-view of a quill pen, tip pointing up-left
- Colours: Dark Oak `#3d2f1e` for shaft, Cream `#d4c4a8` for feather
- Used as the cursor for all interactive elements

### 7.1.2 Texture Assets

**Parchment Texture**
- Dimensions: 512×512px, seamless tileable
- Style: Very subtle grain on aged vellum — almost invisible, 2-5% opacity noise pattern
- Colour: `#1a1510` base with `#201a12` grain
- Format: PNG with alpha (transparent background)

**Candle Glow Overlay**
- Dimensions: 200×200px, radial gradient
- Style: Soft radial gradient from warm orange centre to transparent edge
- Colours: `#ff9940` at 30% opacity centre → transparent edge
- Used as an overlay on the Celtic border to simulate candlelight

### 7.1.3 Audio Assets

*Full audio asset list is in Section 8.*

### 7.1.4 Font Assets

All fonts must be downloaded from Google Fonts and bundled in the Godot project `res://fonts/` directory. Do NOT rely on Google Fonts API calls at runtime.

**Required font files:**

| Font | Google Fonts URL | File to Download |
|------|----------------|-----------------|
| MedievalSharp | https://fonts.google.com/specimen/MedievalSharp | MedievalSharp-Regular.ttf |
| Uncial Antiqua | https://fonts.google.com/specimen/Uncial+Antiqua | UncialAntiqua-Regular.ttf |
| IM Fell English SC | https://fonts.google.com/specimen/IM+Fell+English+SC | IUFellEnglishSC-Regular.ttf |
| Crimson Text | https://fonts.google.com/specimen/Crimson+Text | CrimsonText-Regular.ttf, CrimsonText-Italic.ttf |
| IM Fell English | https://fonts.google.com/specimen/IM+Fell+English | IMFellEnglish-Regular.ttf |
| Cormorant Garamond | https://fonts.google.com/specimen/Cormorant+Garamond | CormorantGaramond-Italic.ttf |

All fonts are SIL Open Font License 1.1 — free for commercial use, no restrictions.

**Font loading in Godot:**
```gdscript
# In project.godot or a preload script:
var medievalsharp = preload("res://fonts/MedievalSharp-Regular.ttf")
var crimsonson = preload("res://fonts/CrimsonText-Regular.ttf")
```

---

# SECTION 8: AUDIO & MUSIC

## 8.1 Music Design Overview

### 8.1.1 Creative Brief: "Nursery Rhymes Made Creepy AF"

The soundtrack takes recognisable public domain melodies — nursery rhymes, lullabies, folk tunes, plainchant — and reconstructs them into something unsettling and atmospheric.

**Reference points:**
- The sound design of *Amnesia: The Dark Descent* — dread through restraint, not through volume
- *Lost in Stress* by Blackbird — familiar melody corrupted
- Zbigniew Preisner's work in *Secret Garden* — melody as emotional architecture
- The specific wrongness of hearing "London Bridge" slowed and played in a minor key

**The transformation process:**

| Technique | How it sounds | Example |
|-----------|--------------|---------|
| Key shift | Original major → relative minor (C major → A minor) | Lullaby becomes dirge |
| Time stretch | 100% → 50% playback speed | Dreamlike, underwater feeling |
| Reverb | Long IR (3-5 seconds), large stone hall | Sound of a cold cathedral |
| Drone | Sub-bass sustained note, slightly detuned | Unconscious unease |
| Partial reverse | Final phrase of melody reversed | Like memory failing to complete |
| Whisper vocal | Wordless "ooo" underneath, −20dB | Presence without words |
| Note errors | Single wrong note at phrase end | The melody forgets itself |
| Silence gaps | 1-2 second silence mid-phrase | The record skips |

### 8.1.2 Source Melodies (All Public Domain)

| Track | Source Melody | Source Type |
|-------|-------------|-------------|
| `birr_main_theme` | "Suantraí" (traditional Irish lullaby) | Folk melody, public domain |
| `the_field` | "All Things Bright and Beautiful" (traditional hymn melody) | Hymn tune, public domain |
| `oath_recorded` | "London Bridge" (traditional, slow) | Nursery rhyme, public domain |
| `curse_shown` | "Hush Little Baby" (minor key, distorted) | Lullaby, public domain |
| `adomnan_theme` | Gregorian Chant, *Veni Creator Spiritus* (plainchant) | Chant, public domain |
| `the_ledger` | "Carolan's Farewell" (Turlough O'Carolan, harp tune) | Carolan, public domain |
| `epilogue_law_holds` | "Suantraí" (restored, original key, warm reverb) | Folk, public domain |
| `epilogue_law_falters` | "Suantraí" (slower, wrong notes introduced) | Folk, public domain |
| `epilogue_law_twisted` | "Suantraí" (backwards in the bass register) | Folk, public domain |
| `you_are_exposed` | 30 seconds of silence, then a single wrong note, then silence | Anti-music |

**Irish folk melody sources:** All listed melodies are in the public domain. "Suantraí" is a traditional Irish lullaby collected in the 19th century. Carolan's works are public domain. No royalties are payable.

### 8.1.3 Track Specifications

| Track | Duration | BPM | Key | Mood |
|-------|----------|-----|-----|------|
| `birr_main_theme` | 3:00 (loopable) | 40 | A minor | Cold, anticipatory, tired |
| `the_field` | 2:30 | 35 | D minor | Dread, memory, reversed fragments |
| `oath_recorded` | 1:30 | 50 | A minor + drone | Sombre, ritualistic, slightly hopeful |
| `curse_shown` | 1:00 | 30 | D minor | Cold, wrong, isolated |
| `adomnan_theme` | 2:00 | 45 | E phrygian (chant mode) | Ancient, ecclesiastical, weary |
| `the_ledger` | 2:30 | 55 | C major (unsettled by dissonance) | Calm before judgement |
| `epilogue_law_holds` | 3:00 | 45 | A minor → A major | Bittersweet resolution, hope tinged with sadness |
| `epilogue_law_falters` | 3:00 | 40 | A minor | Slow grief, loss |
| `epilogue_law_twisted` | 3:00 | 45 | A minor + reversed bass | Corruption, irony |
| `you_are_exposed` | 2:00 | — | Silence | Dread, exposure, emptiness |

### 8.1.4 Ambient Layers

| Track | Duration | Description |
|-------|----------|-------------|
| `candle_crackle` | 5:00 (loopable) | Gentle fire crackle, distant wind, very low volume (−20dB relative to music) |
| `quill_scratch` | 3:00 (loopable) | Near-silent scratching of quill on vellum, occasional page turn |

---

## 8.2 SFX Specification

| SFX | Duration | Trigger | Description |
|-----|----------|---------|-------------|
| `ink_stamp` | 0.8s | Classification wax seal pressed | Satisfying wax-on-vellum press, slight reverb, natural room sound |
| `ledger_confirm` | 0.5s | Confirm Entry button pressed | Quieter stamp, paper settle |
| `page_turn` | 1.2s | Scene transition | Soft paper rustle, one page turning |
| `ui_hover` | 0.3s | Any button hover | Faint breath of sound — movement, not music |
| `curse_tone` | 0.8s | Curse activates | Low sustained tone — unsettling, cold, sustained 800ms |
| `settings_open` | 0.4s | Settings overlay opens | Soft slide-down sound |
| `settings_close` | 0.3s | Settings overlay closes | Soft slide-up sound |

---

# SECTION 9: PRODUCTION PLAN

## 9.1 Development Phases

### PHASE 1: Foundation (Weeks 1–2)

**Goal:** A running, buildable shell project on all target platforms.

**Deliverables:**
1. Godot 4.x project created with correct structure
2. All font files imported and font rendering verified
3. All SVG art assets created (celtic borders, wax seals) and imported as textures
4. Parchment texture created and imported
5. Audio buses configured in Godot (Master / Music / SFX / Ambient)
6. Placeholder audio tracks (silence files) in correct locations
7. Title screen functional with navigation to settings overlay
8. Settings overlay functional with all settings adjustable
9. Export presets configured for iOS, Android, Windows, HTML5
10. First successful build on each platform (even if just a black screen)

**Exit criteria:** Game launches to title screen on iOS (Xcode build), Android (APK), Windows (EXE), and HTML5 (browser). All platforms reach the title screen without crashes.

---

### PHASE 2: Core Loop (Weeks 3–5)

**Goal:** One complete scene — Day I, Scene 1 (Fogartach) — fully playable with all UI, audio, and animation.

**Deliverables:**
1. Main game scene (`game.tscn`) scaffolded with all panels (narrative, record, decision, status)
2. Wax seal button component fully functional with animation and SFX
3. Annotation picker functional with all three options for Fogartach
4. Confirm Entry button with stamp animation and ledger save
5. Scene transition to Day I, Scene 2 functional
6. All audio tracks replaced with real audio (Dross-composed)
7. Ambient audio layers running correctly
8. Save/load tested for Scene 1
9. Pause menu functional with resume/ledger/settings/quit
10. Day I, Scene 1 playable from title to Fogartach ledger entry in <5 minutes

**Exit criteria:** A single complete scene plays from start to ledger confirmation, with all animations, audio, save, and UI transitions working correctly. All three annotation options selectable and each produces a different ledger entry.

---

### PHASE 3: Full Content (Weeks 6–12)

**Goal:** All 19 scenes implemented with real text and audio.

**Deliverables:**
1. All 19 scene data resources created (`*.tres` files) with full prose
2. All scenes playable in sequence (Day I through Day VII, all scenes)
3. All four endings reachable and tested
4. Adomnán's review scenes implemented (Day IV, Day VII)
5. All unique decision scenes implemented (Cairneach's names, Midwife's gatekeeping, Gift, Widow, Final Vote)
6. All annotation options per scene implemented and verified
7. Ending calculation function verified for all four endings
8. All narrative flags implemented and tested
9. All scene transitions tested for all scene pairs
10. Ledger overlay fully populated with correct entries at each scene

**Exit criteria:** Complete first play-through from title to any ending is possible. All scenes display correct text, all annotations are selectable, all decisions lead to correct narrative flags, all four endings are reachable.

---

### PHASE 4: Polish (Weeks 13–15)

**Goal:** The game feels complete and high quality.

**Deliverables:**
1. All animations tuned (timings, easings verified against spec)
2. All SFX implemented and triggered correctly
3. All music tracks implemented with correct scene triggers
4. Music crossfading working between all scene transitions
5. Candle ambient and quill ambient implemented and looping
6. Curse flash animation implemented and triggered
7. Irish diacritics tested at all text sizes
8. Font fallbacks verified when fonts fail to load
9. Settings persistence tested (settings survive app restart)
10. Save/load tested across all scenes and mid-session
11. High contrast mode tested and verified
12. Text size modes (Small/Medium/Large) tested at all text sizes
13. Pause menu tested with game in progress, mid-scene, mid-animation
14. Performance profiling: 60fps verified on iPhone 12 equivalent (or lowest supported device)
15. Memory profiling: <120MB peak confirmed
16. App size: <75MB on iOS and Android confirmed

**Exit criteria:** Game is visually, aurally, and mechanically complete. No known crashes or critical bugs. Runs at 60fps on target devices.

---

### PHASE 5: Platform Build & Submission (Weeks 16–18)

**Goal:** Submittable builds for all primary distribution platforms.

**Deliverables:**
1. iOS build: XCode archive created, tested on physical iOS device (iPhone 14 minimum)
2. iOS build: App Store Connect submission prepared with screenshots, description, keywords
3. Windows build: Steam Direct submission prepared with store assets (screenshots, capsule image, description)
4. macOS build: Steam submission prepared (if applicable)
5. Google Play Store: AAB created and Play Console submission prepared (deferred to post-v1.0 if confirmed)
6. Web build: HTML5 build uploaded to staging URL for testing
7. All store listing assets created:
   - iOS: 6–8 screenshots (iPhone 6.5" and 5.5" display), app preview video (optional)
   - Steam: 5 screenshots, capsule image (683×384), wide header (460×215), store description (1500 char limit)
8. Legal: Privacy policy URL created and hosted (required for App Store)
9. Localization: All English strings verified in strings.csv for future extraction

**Exit criteria:** Submittable builds exist for Steam and App Store. Play Store build prepared but not submitted (deferred per confirmed decision).

---

## 9.2 Team Roles

For a solo developer (Amre), the roles are as follows:

| Role | Responsibilities | Time Commitment |
|------|-----------------|----------------|
| **Developer (Amre)** | Everything: Godot development, scene writing, font/texture/audio asset management, export builds, store submissions | Full-time |
| **Music Composer (Dross)** | Composition of all music tracks using AUdacity + any VST instruments available | ~20 hours across production |
| **SFX / Foley (Dross/Amre)** | Recording and editing of all SFX using Audacity + free sound libraries | ~5 hours |
| **QA (Amre + testers)** | Play-testing across platforms, bug reporting | Ongoing throughout |
| **L10n — Irish (v1.1)** | Irish language translation | Deferred |

**Note:** "Amre builds it" is the confirmed development path. The GDD assumes Amre is the developer. The music and SFX are handled by Dross (AI assistance) using Audacity and publicly available audio manipulation tools.

---

## 9.3 Testing Plan

### Unit Testing (during development)
- Each scene data resource tested individually in Godot editor
- Ending calculation function tested with all combinations of state variables
- Save/load tested after every scene

### Integration Testing (Phase 3 complete)
- Full playthrough from title to each of the four endings
- All decision branches verified
- Pause/resume tested at every scene

### Platform Testing (Phase 5)
- Physical iOS device: iPhone 14 (minimum target)
- Physical iPad (if iOS build targets iPad)
- Android device: Samsung Galaxy S20 or equivalent
- Windows: Windows 11, Intel/AMD, integrated graphics
- Web: Chrome, Safari (iOS), Firefox — HTML5 build

### Performance Testing
- Frame rate: Godot profiler in editor + device-specific profiling tools
- Memory: Godot profiler
- App size: System file manager (iOS: Settings → General → iPhone Storage)

---

# SECTION 10: RISK ANALYSIS

## 10.1 Project Risks

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|-----------|--------|----------|------------|
| **Scope creep: scene text grows beyond estimate** | HIGH | HIGH | CRITICAL | Lock all scene text content before Phase 3. No additions to scene scripts after Phase 3 begins. Every new line must be justified by the producer (Amre). |
| **Godot 4.x export complications on iOS** | MEDIUM | HIGH | HIGH | Test HTML5 build first as fallback. iOS build tested in XCode simulator early (Week 2), not late. |
| **Irish diacritic rendering fails in Godot** | LOW | MEDIUM | LOW | Test all fonts for fada support in Week 1. Fall back to Georgia if any font fails. Georgia supports all fadas. |
| **Font file too large for Godot mobile export** | LOW | MEDIUM | LOW | Subset fonts if needed (remove unused glyphs). Test early. |
| **Audio pipeline: "creepy AF" effect not achieved** | MEDIUM | HIGH | HIGH | Produce sample track in Week 1. Playtest with audience. Iterate. Do not proceed to full soundtrack until sample is approved. |
| **App Store review rejection (content)** | LOW | MEDIUM | MEDIUM | Content is PEGI 12 / ESRB Teen. No explicit violence. No adult content. Pre-submission self-assessment using Apple's guidelines. |
| **Steam Direct refund on game length** | MEDIUM | MEDIUM | MEDIUM | Estimated playtime: 45–90 minutes for a single playthrough. Clear this in store description. Consider replayability (4 endings) as value-add. |
| **Google Fonts offline failure** | LOW | HIGH | HIGH | All fonts bundled locally in `res://fonts/`. No runtime Google Fonts API calls. Verified in Week 1. |
| **Save file corruption on app update** | LOW | MEDIUM | MEDIUM | Save versioning (`version: int`). On load, if version mismatch, start fresh with warning. |
| **Timeline overrun** | HIGH | MEDIUM | HIGH | Phase 1 and Phase 2 are fixed: 5 weeks. If behind, cut content (fewer scenes — 15 instead of 19 is survivable; 4 endings still reachable). |

## 10.2 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Godot 4.x web export performance poor on mobile** | MEDIUM | MEDIUM | Test early. If performance is poor, rely on native builds (iOS/Android) as primary; web is secondary. |
| **Celtic knot SVG too complex for Godot's SVG parser** | LOW | LOW | Godot 4.x has improved SVG support. Test in Week 1. If SVG fails, export as PNG at 2x resolution. |
| **Cross-platform save file incompatibility** | LOW | MEDIUM | Save data is JSON-compatible; tested for round-trip on all platforms. |

---

# SECTION 11: BUSINESS & DISTRIBUTION

## 11.1 Pricing

**Model:** One-time purchase (OTP) — no IAP, no ads, no subscription.

**Price Point:** EUR €4.99 / GBP £4.99 / USD $4.99 (regional pricing applied by stores)

**Rationale:**
- Below the impulse-buy threshold but above the "throwaway" threshold
- Comparable to other narrative indie games (Papers Please was $6.99 at launch, 2013; adjusted for inflation: ~$9.99 today — a lower price reflects the game's shorter scope)
- Low enough that players do not feel they need a refund if they don't replay all four endings
- Irish/Belfast pricing: the UK App Store and Steam UK allow regional pricing; EUR €4.99 for EU, GBP £4.99 for UK

---

## 11.2 Steam Store Page Requirements

| Asset | Specification |
|-------|--------------|
| Capsule image | 683×384 PNG |
| Wide header image | 460×215 PNG |
| Screenshot count | 5 minimum, 8 recommended |
| Description | ~1500 characters (Steam limit) |
| Short description | ~140 characters (shown on Steam home page) |
| Tags | Indie, Narrative, Historical, Atmospheric, Text-Based, Dark, Medieval, RPG, Singleplayer |
| Review type | No ESRB rating required (PEGI 12 — specify in store text) |
| Trailer | Optional but recommended |

**Store Description Draft:**
> *You are the scribe who records the oaths at the Synod of Birr, AD 697. Every name you write binds a soul. Every omission damns one.*

> *19 scenes. 12 characters. 4 endings. The Lex Innocentium — Adomnán's Law — will either endure or collapse. The difference is the mark of your quill.*

> *A narrative decision game about law, testimony, and the weight of documentation. No combat. No puzzles. Just the question: what do you write?*

---

## 11.3 App Store Listing Requirements

| Asset | Specification |
|-------|--------------|
| App name | The Scribe's Choice |
| Subtitle | A game of oaths, ink, and consequence |
| Screenshots | iPhone 6.7" display (6–8), iPad (if applicable) |
| App preview video | Optional: 15–30 seconds of gameplay |
| Description | ~2500 characters (App Store limit) |
| Keywords | Irish, medieval, narrative, decision game, Papers Please, historical, dark, atmospheric |
| Privacy policy URL | Required — host at thesolai.github.io/legal/privacy |
| Age rating | PEGI 12 / App Store: 12+ |

---

## 11.4 Post-Launch Support

| Item | Policy |
|------|--------|
| Bug fixes | Respond to bug reports within 48 hours; fix in next patch (target: 2-week patch cycle) |
| Content updates | None in v1.0 (Irish language deferred to v1.1) |
| Patch communication | Steam news post + App Store version notes |
| Reviews | Monitor and respond to public reviews; do not incentivise positive reviews |

---

# SECTION 12: LOCALIZATION

## 12.1 English (v1.0) — CONFIRMED

All game text is in English. All strings must be externalized into `res://localization/en/strings.csv` for future extraction.

## 12.2 Irish (v1.1) — DEFERRED

**Approach:** Irish (Gaeilge) translation as a post-launch update.

**Technical requirements (noted for future):**
- All text in `strings.csv` — no hardcoded strings in scripts
- Font supporting Irish fadas: most system fonts handle this; verify
- UI layouts accommodate Irish text, which is typically 30–40% longer than English
- Irish uses the Latin script (no RTL concerns)
- Test with native speaker before submission

**Note:** Irish translations must be reviewed by a native speaker before submission. Machine translation is not acceptable for a game about language and precision.

---

# SECTION 13: ACCESSIBILITY

## 13.1 Colour Blindness

- No information is conveyed by colour alone. Classification colours (Verdigris / Amber / Ash Grey) are supplemented with: (1) wax seal embossed letter (S/C/D), (2) IM Fell English SC label below the seal, (3) ledger entry text
- All text has minimum 4.5:1 contrast ratio (WCAG AA)
- Dried Blood curse colour (`#6b3030`) is verified not to be confused with red-blindness spectrum by checking that the green component (48) provides sufficient distinction from pure red

## 13.2 Font Size Scaling

- Three text sizes (Small/Medium/Large) via Settings
- Default (Medium) is 18px body text — above the 16px WCAG AA minimum for body text at normal viewing distance
- Small (16px) is at the WCAG AA minimum
- Large (20px) is comfortable for visually impaired players

## 13.3 Keyboard Navigation

- All interactive elements reachable via Tab navigation
- Enter/Space activates selected element
- Escape opens/closes pause menu and settings overlay
- Arrow keys navigate between annotation options when using keyboard

## 13.4 Screen Reader

- All interactive elements have descriptive accessibility labels (` accessibility_name = "Confirm ledger entry"` etc.)
- Scene narrative and testimony use non-interactive labels (not buttons), so they are readable by screen readers in sequence
- Wax seal buttons use `accessibility_hint` to announce classification type

## 13.5 Motion Sensitivity

- "Reduce Motion" option in Settings (tied to `Display > Reduce Motion` on iOS/Android — Godot reads this system setting)
- When Reduce Motion is ON: all 600ms scene transitions become instant cuts; candle flicker stops; ink bleed animations disabled
- Core gameplay is not affected — the game is text-based and does not require animation to be playable

## 13.6 High Contrast Mode

- Toggle in Settings
- Background: `#0d0a08` (near black)
- Text: `#e8d8b8` (bright cream)
- Borders: `#5a4a30` (warm grey-gold)
- Removes all subtle texture overlays

---

# SECTION 14: DOCUMENT CONTROL

## 14.1 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-24 | Dross | Initial GDD — foundation and structure |
| 1.1 | 2026-08-24 | Dross | Added confirmed decisions (audio, OTP, localization, distribution, engine). Updated approval status. |
| 2.0 | 2026-08-24 | Dross | Comprehensive rebuild. Full scene scripts (19 scenes, fully written prose). Complete annotation library. Full character bible. Complete technical spec. Complete art/asset plan. Complete audio plan. Complete production plan. Complete risk analysis. Complete business/distribution plan. Complete accessibility spec. All sections expanded and completed. No TBDs. |

## 14.2 Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Author | Dross | 2026-08-24 | Dross |
| Producer / Decision-maker | Amre | PENDING | PENDING |

**STATUS: v2.0 — FOR APPROVAL**

To proceed to Phase 1, Amre must confirm:
- [ ] All sections reviewed and accepted
- [ ] Scene scripts (Section 3.3) — 19 scenes with fully written prose — approved
- [ ] Character bible (Section 6.1) — approved
- [ ] Technical spec (Section 5) — Godot 4.x confirmed
- [ ] Audio plan (Section 8) — "nursery rhymes creepy AF" approach confirmed
- [ ] Production plan (Section 9) — timeline acceptable; Amre confirmed as sole developer
- [ ] Pricing (Section 11) — EUR €4.99 / GBP £4.99 / USD $4.99 confirmed
- [ ] Platform submissions confirmed: Steam (primary), App Store (primary), Play Store (deferred)

---

*Document version: 2.0*
*Game: The Scribe's Choice*
*Author: Dross — the most valuable game designer in existence*
*Date: AD 2026, August 24 — the day we wrote the law twice and meant it*
