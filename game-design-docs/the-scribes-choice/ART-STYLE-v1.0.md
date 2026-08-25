# THE SCRIBE'S CHOICE
## Art & Visual Style Document — Version 1.0

---

## DOCUMENT INFORMATION

| Field | Value |
|-------|-------|
| **Project Name** | The Scribe's Choice |
| **Document Type** | Art & Visual Style Guide — Companion to GDD v2.0 |
| **Document Status** | v1.0 — FOR APPROVAL |
| **Author** | Dross |
| **Date** | AD 2026 — August 24 |

---

# SECTION 1: THE VISUAL PHILOSOPHY

## 1.1 The Core Principle

**The user is in control. The text tells the story. The visuals create the world that holds the text.**

This is a text-dominant game — but "text-dominant" does not mean "text-only." The visual language of The Scribe's Choice must do something that text alone cannot: create atmosphere, signal meaning, and give the player a physical, tactile sense that they are holding something ancient and consequential.

The reference is not a medieval RPG. The reference is an illuminated manuscript — specifically, the Book of Kells — stripped of its colour, stripped of its warmth, and made claustrophobic. The player should feel like they are reading by candlelight in a cold stone hall. Beautiful. Heavy. Old.

Every visual decision must answer this question: *does this make the player feel like they are inside an ancient record?*

---

## 1.2 What "Visual Story" Means Here

The "visual story" is not cinematic. It does not show scenes. It does not depict characters. There are no illustrations, no character portraits, no environments rendered in pixels.

The visual story is created by:
- **The weight of the typography** — text that feels typeset, not typed
- **The texture of the surfaces** — vellum, parchment, ink, wax
- **The precision of the Celtic ornament** — decoration that means something
- **The quality of the transitions** — page turns, ink drying, candlelight flicker
- **The silence of the space** — generous margins, room to breathe, darkness between the words

The player is not watching a story. The player is *reading* a story that is also an *object* — a physical thing that exists in their hands.

---

## 1.3 User Control and Visual Feedback

The player is always in control. Visually, this means:

**Every action has a visible consequence.**
- Selecting a classification: the wax seal presses down, stamps, and changes state visibly
- Confirming an entry: the ledger entry "writes itself" into the ledger
- Opening the ledger: it unfurls like a real document
- Making a decision: the screen does not cut — it transitions like a page turning

**The pace is the player's.**
- There is no auto-advance. The player reads at their own speed.
- Text appears at a measured pace — line by line — but the player cannot rush it. This is intentional. The pace is part of the atmosphere.
- If the player lingers on a scene, nothing forces them forward. The candlelight flickers. The ambient sounds loop. The silence is part of the design.

**The visual language signals meaning without spoiling.**
- A warm amber glow on an annotation card means one thing
- A cold ash grey means another
- The wax seal colours are consistent throughout — the player learns the vocabulary of the visuals, just as they learn the vocabulary of the law

---

# SECTION 2: THE AESTHETIC — ILLUMINATED MANUSCRIPT RECONSIDERED

## 2.1 What We Are NOT Doing

We are not making a medieval game that looks like every other medieval game.

We are NOT:
- A Celtic fantasy with bright greens, Celtic warrior imagery, and Druidic mysticism
- A historically accurate reconstruction of a 7th-century scriptorium
- A pretty illuminated manuscript with warm colours and decorative flourishes everywhere
- A "dark medieval" game with grunge textures and blood splatters
- A minimalist modern game with clean sans-serif fonts and flat design

## 2.2 What We ARE Doing

We are making a game that feels like *a document that survived 1,300 years*.

The aesthetic is: **the archaeological object**. The game looks like the physical remnant of something that was made with care, that has been handled, that has survived. Not pristine. Not perfect. But preserved.

**The Book of Kells is the inspiration — but imagine the Book of Kells after it has been in a cold, damp archive for five centuries.** The colours are muted. The gold is tarnished. The vellum is dark. But you can still see the skill. You can still see what it was.

This is the visual position: *illuminated manuscript as archaeology*.

---

## 2.3 The Dark Palette and Why It Matters

The palette is dark. This is not aesthetic preference — it is *functional*.

In a text-dominant game, the text is the primary content. The text must be readable. But the text must also feel *different* from the background — not just technically readable (high contrast) but *emotionally appropriate*.

A dark parchment background with warm cream text feels like: reading something old, by candlelight, in the dark. This is exactly right for the game.

A light parchment background with dark text feels like: reading a book in a library. This is wrong. This is not a library game. This is not a cozy game. The player is in a synod hall, recording oaths by candlelight, and the fate of the Lex Innocentium rests on their hand.

**The darkness is the atmosphere. The candlelight is the only warmth.**

---

# SECTION 3: COLOR — THE COMPLETE PALETTE

## 3.1 Palette Overview

The palette is derived from aged vellum, tarnished gold, cold iron, dried blood, and candlelight.

| Name | Hex | Usage |
|------|-----|-------|
| Deep Vellum | `#1a1510` | Primary background. The surface the player reads on. |
| Dark Parchment | `#211a12` | Panel backgrounds. Slightly lighter — creates depth. |
| Aged Vellum (Ledger) | `#1e1810` | Ledger screen background. Distinguishable but not different. |
| Faded Gold Ink | `#d4c4a8` | Primary text. Warm cream. Readable, aged, not bright. |
| Illuminated Gold | `#c9a030` | Headers, day labels, epilogue titles. The gold that remains after tarnishing. |
| Celtic Moss | `#2d5a4a` | Celtic knot borders and ornamental corners. Muted, ancient green. |
| Gold Highlight | `#8b6914` | Knot highlights within the Celtic green. The gold that catches candlelight. |
| Verdigris | `#3a5a4a` | Supporter wax seal. Faded green — copper that has aged. |
| Muted Amber | `#7a6030` | Conditional wax seal. Dull gold-brown — old beeswax. |
| Ash Grey | `#4a4040` | Dissenter wax seal. Cold, dark — the colour of exclusion. |
| Dried Blood | `#6b3030` | Curse markers, danger states. Not fresh red — old, dried. |
| Dark Oak | `#3d2f1e` | UI borders, dividers, panel edges. Wood that has aged in shadow. |
| Warm Glow | `#ff9940` at 8% | Candle glow effect. Applied as overlay, not solid. |
| Outcome Hint | `#8a7a5a` | Subtle hints after a ledger entry. Quieter than primary text. |
| Muted Gold | `#a09070` | Status bar text, day counter. Quiet, present, persistent. |
| Pale Vellum | `#c0b090` | Settings screen text. Readable but not intrusive. |
| Ash Red | `#7a4040` | Error states only. Used sparingly. |

## 3.2 Palette in Context

### Background Hierarchy

```
Deep Vellum (#1a1510) — the darkest, most recessive
    │
    ├── Dark Parchment (#211a12) — panels, containers
    │       │
    │       └── Aged Vellum (#1e1810) — ledger screen only
    │
    └── Warm Glow (#ff9940 at 8%) — candlelight overlay on borders
```

### Text Hierarchy

```
Primary Text: Faded Gold Ink (#d4c4a8) — body, testimony, narrative
    │
    ├── Headers: Illuminated Gold (#c9a030) — day labels, titles
    │
    ├── Status: Muted Gold (#a09070) — status bar, meta information
    │
    └── Hints: Outcome Hint (#8a7a5a) — quiet, post-decision
```

### Semantic Colour (Classification)

```
SUPPORTER: Verdigris (#3a5a4a) — faded copper-green, aged, settled
CONDITIONAL: Muted Amber (#7a6030) — old beeswax, unresolved
DISSENTER: Ash Grey (#4a4040) — cold, excluded, outside the warmth
CURSED: Dried Blood (#6b3030) — old blood, consequence
```

## 3.3 High Contrast Mode

For accessibility and preference, a High Contrast palette is available:

| Element | Standard | High Contrast |
|---------|----------|---------------|
| Background | `#1a1510` | `#0d0a08` |
| Text | `#d4c4a8` | `#e8d8b8` |
| Borders | `#3d2f1e` | `#5a4a30` |
| Celtic Accent | `#2d5a4a` | `#3d6a5a` |

High Contrast mode removes all subtle texture overlays and increases text brightness across the board. This is not a separate aesthetic — it is the same aesthetic, amplified for readability.

---

# SECTION 4: TYPOGRAPHY — THE CORE VISUAL ELEMENT

## 4.1 Typography as Aesthetic

In The Scribe's Choice, typography is not just readable text. Typography *is* the visual environment.

The fonts chosen are not "medieval-themed fonts" chosen for flavour. They are specific, carefully selected typefaces that:
1. Function beautifully at the sizes used in the game
2. Support all required characters (including Irish fadas)
3. Have sufficient visual weight and personality to create atmosphere
4. Can be embedded in a Godot game without licensing complications

## 4.2 Font Specifications

### MedievalSharp — Titles and Seals
- **Google Fonts name:** `MedievalSharp`
- **Usage:** Game title on title screen, wax seal embossed letters
- **Style:** Uncial-derived capitals, all caps, letter-spaced
- **Size:** 36px title, 14px seal letters
- **Colour:** Illuminated Gold `#c9a030`
- **Fallback:** Georgia, serif

### Uncial Antiqua — Day Headers
- **Google Fonts name:** `Uncial+Antiqua`
- **Usage:** Day headers ("DAY I", "DAY II"), major section breaks
- **Style:** All caps, uncial, generous letter-spacing
- **Size:** 24px
- **Colour:** Illuminated Gold `#c9a030`
- **Fallback:** Georgia, serif

### IM Fell English SC — Small Labels and Status
- **Google Fonts name:** `IM+Fell+English+SC`
- **Usage:** Classification labels ("SUPPORTER", "CONDITIONAL"), status bar, settings labels, ledger character names
- **Style:** Small caps — formal, historical, slightly irregular
- **Size:** 12-16px
- **Colour:** Muted Gold `#a09070` or classification colour
- **Fallback:** Georgia, serif
- **Note:** IM Fell English fonts are historical revivals — they have slight irregularities that make them feel hand-set. This is a feature, not a bug.

### Crimson Text — Body and Testimony
- **Google Fonts name:** `Crimson+Text` (Regular and Italic)
- **Usage:** All narrative text, character testimony, scene descriptions, epilogue body
- **Style:** Elegant, readable serif. Regular for narration; Italic for character speech
- **Size:** 18px (default), 16px (Small mode), 20px (Large mode)
- **Colour:** Faded Gold Ink `#d4c4a8`
- **Line height:** 1.7 — generous, readable, allows the eye to rest
- **Fallback:** Georgia, serif

### Cormorant Garamond — Player's Own Voice
- **Google Fonts name:** `Cormorant+Garamond` (Italic only)
- **Usage:** The player's annotations — their scribe's notes in the ledger. This font distinguishes the player's voice from the game's text.
- **Style:** Italic serif — elegant, slightly unsteady, like handwriting
- **Size:** 16px
- **Colour:** Faded Gold Ink `#d4c4a8`
- **Fallback:** Georgia, serif italic
- **Note:** Cormorant Garamond is also used for the prologue testimony (Ronat's words) — to distinguish Ronnat's voice as being outside the normal game text. The player's annotations and Ronnat's testimony share the same font — suggesting a kinship between what Ronnat said and what the player chooses to record.

## 4.3 Irish Fadas — Technical Requirements

All fonts used for body text (Crimson Text, Cormorant Garamond) must support Irish-language fadas:
`Á É Í Ó Ú á é í ó ú`

These are in the Latin Extended A Unicode block (U+0100–U+017F). All specified fonts support this range.

**Testing protocol:**
- During Phase 1, every font must be tested with the string: *"Adomnán of Iona — Áth na Rónnat — Úna"*
- Any font that fails to render the fadas correctly falls back to Georgia
- Georgia is the universal fallback and supports all Irish characters

---

# SECTION 5: THE CELTIC KNOT — DESIGN AND SPECIFICATION

## 5.1 Role of Celtic Knotwork

The Celtic knot is not decorative in this game. It is *structural*.

It appears in three contexts:
1. **Title screen border** — full frame, the player's first impression of the game's visual world
2. **Panel corner ornaments** — on key panels within the game (decision panel, ledger panel)
3. **Epilogue frame** — the closing border, which mirrors the opening title border

The knotwork signals: *this is old. This is Ireland. This is sacred or legal or both.*

The knotwork is never used on every surface. It is used sparingly, with intention. The majority of the screen is dark background with text. The knot appears at moments of emphasis.

## 5.2 Design Principles

### The Knot is Infinite
The knot pattern has no beginning and no end — continuous interlace. This is deliberate. The law, like the knot, has no beginning and no end. It continues. It binds.

### The Knot is Muted
The knot is Celtic Moss (`#2d5a4a`), not bright Kelly green. It is tarnished. It has been looked at for a thousand years and the colour has settled into the metal.

Gold highlights (`#8b6914`) appear on the raised portions — the parts of the knot that catch the candlelight. These are subtle, not garish.

### The Knot Animates
The knot breathes. A slow candlelight glow pulses along the gold highlights. The cycle is 4-5 seconds — slow enough to feel ambient, not distracting. The effect is achieved with CSS/SVG `filter: drop-shadow` and opacity animation.

## 5.3 SVG Specification

### Title Screen Border

**Viewport:** 1200×1600px (A4 portrait ratio)
**Style:** Four-cornered continuous Celtic knot, no beginning or end
**Technique:** Path-based SVG with cubic Bézier interlace curves
**Colours:**
- Knot fill: `#2d5a4a` (Celtic Moss)
- Knot highlight: `#8b6914` (Gold Highlight)
- Background: transparent (the Deep Vellum background shows through)

**Animation:** Gold highlight opacity oscillates 0.5 → 0.9 → 0.7 → 1.0 over 4,000ms, random easing (simulating candle flicker). Applied via CSS animation on the SVG element.

**Export formats:**
- SVG master file (for future modification)
- PNG at 2x and 3x for Godot (2048×2736 and 3072×4096 — for iPad Pro retina)

### Panel Corner Pieces

Four unique corner SVGs, each 200×200px:
- **Top-left corner:** Quarter-circle knot, opening toward bottom-right
- **Top-right corner:** Mirror of top-left
- **Bottom-left corner:** Mirror of top-right
- **Bottom-right corner:** Mirror of top-left

These are placed at the corners of panel containers (decision panel, ledger panel). They do not animate.

### Epilogue Border

Same as the title screen border, but with the animation running in reverse (faster decay, slower return — the candle is dying).

## 5.4 Procedural Generation Alternative

If hand-drawing the knot is not feasible, a procedural SVG generation approach is acceptable:

**Tool:** Custom Python script using the `svglib` library or similar
**Algorithm:** Generate a continuous interlace pattern using a base grid of 4×4 knots, with randomised strand routing at each intersection
**Result:** A serviceable Celtic knot pattern that is not beautiful but is structurally correct

**This is the fallback, not the preference.** The title screen deserves a hand-crafted knot. The panel corners can be procedural.

---

# SECTION 6: WAX SEALS — DESIGN AND SPECIFICATION

## 6.1 The Wax Seal as UI Element

The wax seal is the primary classification button. It replaces a standard button or radio button. This is deliberate — it ties the UI mechanic to the game's thematic content.

When a player selects "SUPPORTER," they are pressing a wax seal — the same way a king would seal an oath. The physicality of the action matters.

## 6.2 Design

### Shape
Circular, 80×80px (native). The seal has:
- An outer rim (the wax edge — slightly irregular, achieved with a subtle SVG turbulence filter)
- An inner embossed circle
- Celtic knot detail within the inner circle
- The classification letter embossed in the centre: **S** / **C** / **D**

### Colours

| Seal | Base Colour | Emboss Colour | Emboss Offset |
|------|------------|--------------|---------------|
| Supporter | `#3a5a4a` Verdigris | `#4a6a5a` (lighter) | +1px, +1px |
| Conditional | `#7a6030` Muted Amber | `#9a8050` (lighter) | +1px, +1px |
| Dissenter | `#4a4040` Ash Grey | `#6a6060` (lighter) | +1px, +1px |

The emboss effect is achieved with SVG linear gradient (light source: top-left) and an inner shadow on the wax edge.

### The Wax Texture
The seals should not look like perfect circles. They should look like *wax* — slightly imperfect, slightly rough at the edges.

**Achieved with:** SVG `feTurbulence` filter (low frequency, low opacity) applied to the outer edge of each seal. This creates a subtle irregularity that reads as "molten wax pressed into a surface."

## 6.3 Seal States

| State | Visual Treatment |
|-------|-----------------|
| Default | Base colour, slight shadow, wax texture visible |
| Hover | Scale 1.05, warm glow of the same colour at 30% opacity, cursor changes to quill |
| Pressed (selected) | Scale 0.95, translateY 2px, stamp SFX plays, emboss darkens slightly |
| Disabled | 40% opacity, no hover effect, cursor: not-allowed |

## 6.4 SVG Implementation

Each seal is a single SVG file:
- `wax_seal_supporter.svg`
- `wax_seal_conditional.svg`
- `wax_seal_dissenter.svg`

In Godot, these are loaded as `TextureRect` nodes. The emboss effect (which is a visual effect) is pre-baked into the SVG — not generated at runtime.

---

# SECTION 7: PANEL DESIGN — THE LAYERS OF THE SCREEN

## 7.1 The Layered Panel System

The main game screen is composed of layered panels, each with its own visual weight and purpose.

### Layer 1: The Background
**Deep Vellum `#1a1510`**
- Full-screen, continuous
- Subtle parchment texture overlay at 3% opacity (barely visible — adds depth without distraction)

### Layer 2: The Celtic Border (top)
**A 40px tall strip at the top of the screen**
- Celtic knot pattern, continuous horizontally
- Animated candlelight glow (as per title screen, but 60% intensity — ambient, not focal)
- Not interactive

### Layer 3: The Content Panels

Three stacked panels within the content area:

**A. Scene Narrative Panel**
- Background: Dark Parchment `#211a12`
- Border: 1px Dark Oak `#3d2f1e`
- Corner radius: 4px
- Padding: 16px
- Text: Crimson Text Regular, 18px, Faded Gold Ink
- Position: top third of content area
- This is where the scene is set — "The synod hall is full."

**B. The Record Panel**
- Background: Dark Parchment `#211a12`
- Border: 1px Dark Oak `#3d2f1e`
- Corner radius: 4px
- Padding: 16px
- Text: Crimson Text Italic, 18px, Faded Gold Ink (for testimony)
- Attribution: Crimson Text Regular Small Caps, 14px, Muted Gold (for character name/title)
- Position: middle third of content area, directly below Scene Narrative
- This is where the testimony lives — the character's words

**C. The Decision Panel**
- Background: `#2a2015` (slightly lighter than other panels — signals this is interactive)
- Border: 1px Celtic Moss `#2d5a4a`
- Corner radius: 8px
- Padding: 16px
- Celtic knot corner pieces at all four corners (top-left, top-right, bottom-left, bottom-right)
- Contains: Wax seal buttons, annotation cards, Confirm Entry button
- Position: bottom third of content area
- This is where the player acts

### Layer 4: The Status Bar
**Bottom of screen, 24px tall**
- Background: `#0f0d0a` (darker than the background — a grounding element)
- Border-top: 1px Dark Oak `#3d2f1e`
- Text: IM Fell English, 12px, Muted Gold
- Shows: Day count, classification tallies
- Always visible, never obscuring content

## 7.2 Panel Spacing — The Margins

The content panels are not edge-to-edge. There are generous margins:

```
Left margin: 32px (desktop), 16px (mobile)
Right margin: 32px (desktop), 16px (mobile)
Vertical gap between panels: 12px
Content padding within panels: 16px
```

The margins create the sense that the content is sitting on a surface — not filling a screen. The darkness around the panels is part of the design.

## 7.3 Responsive Behavior

**Desktop (800px+ width):**
- Content area max-width: 720px, centred
- All panels at full width within content area
- Celtic border full width

**Tablet (480–799px):**
- Content area fills screen with 16px margins
- All panels at full width
- Celtic border full width

**Mobile (<480px):**
- Content area fills screen with 12px margins
- Panels stack vertically with 8px gaps
- Status bar text reduced to 11px
- Wax seals reduced to 64×64px
- Annotation cards: full width, stacked vertically

---

# SECTION 8: ANIMATION — THE WEIGHT OF MOVEMENT

## 8.1 Animation Philosophy

**Deliberate. Weighted. Never fast.**

The pace of animation in The Scribe's Choice should feel like the pace of the game itself: slow, considered, consequential.

Every animation should answer: *would this movement happen quickly in the real world?*

- Pressing a wax seal onto vellum: 200ms — fast, but with a physical weight
- A page turning: 600ms — it is a page, it has heft
- Text fading in: 400ms per line — ink appearing on parchment, not pixels appearing on screen
- Candlelight flicker: 4,000ms — the candle is large, the flicker is slow

## 8.2 Animation Inventory

### Scene Entry Animation Sequence

When a new scene loads, the panels animate in sequence:

```
t=0ms:   Scene Narrative panel begins fade-in
t=400ms: First line of narrative text appears
t=500ms: Second line appears
t=600ms: Third line appears
t=700ms: Fourth line appears
t=1100ms: The Record panel begins fade-in
t=1500ms: The Record panel fully visible; testimony text types in
t=1900ms: Decision panel slides up and fades in
t=2200ms: Decision panel fully interactive
```

**Total time to interactive: 2,200ms.** This is the minimum. If the player reads the text as it appears (they will), it will be longer. This is correct.

### Wax Seal Press Animation

When a wax seal is pressed (classification selected):

```
t=0ms:   Seal depresses (scale 0.95, translateY +2px)
t=80ms:  Stamp SFX plays (synchronized with maximum depression)
t=150ms: Seal releases slightly (scale 0.97)
t=200ms: Seal settles (scale 1.0)
```

The annotation options appear immediately after the seal is selected — they do not wait for the animation to complete.

### Confirmation Animation

When the player presses "Confirm Entry":

```
t=0ms:   Confirm button depresses
t=50ms:  Stamp SFX (different from classification stamp — quieter)
t=200ms: Ledger entry "writes" into the ledger (a brief highlight effect on the ledger panel)
t=400ms: Screen begins cross-fade
t=700ms: Screen is fully dark (300ms fade)
t=900ms: Black holds
t=1100ms: New scene begins fading in
t=2500ms: Scene is interactive
```

### Candle Flicker (Ambient)

```
Duration: 4,000ms cycle, infinite loop
Easing: random (not sinusoidal — candles flicker irregularly)
Opacity range: 0.6 → 1.0 → 0.7 → 0.9 → 0.6 (never fully off)
Affected element: Celtic border gold highlights
```

This animation runs continuously during gameplay. It is the only ambient motion that is always present.

### Ink Bleed (Title Text)

On the title screen, when the game title first appears:

```
t=0ms:   Invisible
t=200ms: Text appears with expanding shadow — as if ink is bleeding into wet parchment
t=800ms: Fully visible
Effect: text-shadow grows from 2px blur to 8px blur, opacity 0 → 1
```

## 8.3 The Page Turn

The most significant animation in the game. Used for:
- Transitioning between days (Day I → Day II)
- Entering the epilogue
- Returning to the title screen from the epilogue

The page turn is a 3D transform:

```
t=0ms:   Current content begins to tilt (rotateX: 0° → 5°)
t=200ms: Content fades slightly (opacity 0.8)
t=400ms: Content "lifts" (translateZ: 0 → 20px)
t=600ms: Content rotates and "falls away" (rotateX: 5° → 45°, opacity 0)
t=600ms: Black screen appears
t=800ms: New content begins "landing" (reverse of above)
t=1200ms: New content settled
```

This is a more complex animation than others in the game — it is reserved for the most significant transitions. It communicates: *a chapter has ended.*

---

# SECTION 9: THE LEDGER — DESIGN AS NARRATIVE

## 9.1 The Ledger is the Heart

The ledger is not a menu or a UI screen. The ledger is a *diegetic object* — it exists within the game's world as a physical thing. The player is a scribe. The ledger is their record.

This means:
- The ledger looks like a real ledger — not a game menu
- It opens like a real document
- The entries look handwritten (IM Fell English, slightly irregular)
- The player's annotations look like a different hand (Cormorant Garamond Italic — their voice)

## 9.2 Ledger Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  THE LEDGER                                    [X CLOSE]   │
│  ════════════════════════════════════════════════════════   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Day I — King Fogartach of Uí Néill                    │ │
│  │ Classification: SUPPORTER                              │ │
│  │ Scribe's note: "Fear, not malice. He would keep the    │ │
│  │ oath if he could."                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Day I — Bishop Ronan of Armagh                         │ │
│  │ Classification: CONDITIONAL                             │ │
│  │ Scribe's note: "The bishop is right about the law's    │ │
│  │ imprecision. I record him as a supporter who identified  │ │
│  │ a flaw."                                               │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ... (scrollable)                                           │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│  Entries: 14    Supporters: 7    Conditional: 4    Dissenters: 3 │
└─────────────────────────────────────────────────────────────┘
```

**Visual details:**
- Entry cards have a Dark Parchment background with a 1px Dark Oak border
- Classification label in IM Fell English SC, in the classification colour (Verdigris / Amber / Ash Grey)
- Scribe's note in Cormorant Garamond Italic — this is the player's voice, visually distinct
- A subtle gold divider line (`#3d2f1e` at 30% opacity) between entries
- The ledger is opened by pressing the ledger icon in the pause menu — it unfurls (slides down + fades in) over 400ms

## 9.3 The Marginalia

In scenes where the player writes a margin note (curse, gift acknowledgment, the widow's answer), the margin note appears as a distinct visual element within the ledger entry:

```
┌───────────────────────────────────────────────────────┐
│ Day V — King Diarmait of Mide                          │
│ Classification: DISSENTER                              │
│ Scribe's note: "His contempt for the law is clear."    │
│ ────────────────────────────────────────────────────   │
│ Margin note: "And the curse moved, as it was written." │
└───────────────────────────────────────────────────────┘
```

The margin note is styled differently:
- Smaller text (14px)
- Italic
- Crimson Text (not Cormorant — it is part of the official record, not the player's personal annotation)
- Preceded by a small ornamental divider

---

# SECTION 10: SETTINGS SCREEN — CONSISTENCY

## 10.1 Settings as Visual Object

The settings screen should feel like a formal document — a list of formal entries, each with a formal response.

It should NOT look like a generic game settings menu.

The design language:
- IM Fell English SC for labels
- Crimson Text for values
- Horizontal rules separating sections
- A wax seal for the audio toggle (on/off)
- IM Fell English SC for the "Turn the Page" close button

## 10.2 Settings Panel Layout

```
┌─────────────────────────────────────────────────────────────┐
│  SETTINGS                                       [X CLOSE] │
│  ───────────────────────────────────────────────────────  │
│                                                             │
│  AUDIO                                                     │
│  ───────────────────────────────────────────────────────  │
│  Master Volume        [═══════════○──────]  50%           │
│  Music                [WAX SEAL: ON]   [WAX SEAL: OFF]    │
│  Sound Effects        [WAX SEAL: ON]   [WAX SEAL: OFF]    │
│                                                             │
│  DISPLAY                                                    │
│  ───────────────────────────────────────────────────────  │
│  Text Size           [SMALL] [MEDIUM] [LARGE]              │
│  High Contrast       [WAX SEAL: OFF]  (toggle)             │
│                                                             │
│  ──────────────────────────────────────────────────────── │
│                                                             │
│                    [ TURN THE PAGE ]                        │
└─────────────────────────────────────────────────────────────┘
```

---

# SECTION 11: TITLE SCREEN — THE FIRST IMPRESSION

## 11.1 Title Screen Composition

The title screen is the first thing the player sees. It must communicate the entire visual philosophy in ten seconds.

**Layout (full screen, centred):**

```
[Full-screen Deep Vellum background with subtle parchment texture]
[Celtic knot border, full frame, animated candlelight glow]

        THE SCRIBE'S CHOICE
   A game of oaths, ink, and consequence

        [WAX SEAL: BEGIN]

        [  SETTINGS  ]

   The Lex Innocentium was ratified at Birr, AD 697.
```

**Typography:**
- Title: MedievalSharp, All Caps, 36px, Illuminated Gold, letter-spacing 4px, ink-bleed animation on load
- Subtitle: Crimson Text Italic, 16px, Faded Gold Ink
- Footer: IM Fell English, 11px, Muted Gold

**The Celtic knot border** is the dominant visual element. It fills the frame. It glows with candlelight. It says: *this is Ireland. This is old. This is sacred.*

## 11.2 The Footer Disclaimer

The footer text is deliberately understated:

*"The Lex Innocentium was ratified at Birr, AD 697."*

This tells the player: *this is based on something real.* It is not a disclaimer — it is an invitation. It says: *you are about to play with something that mattered.*

---

# SECTION 12: EPILOGUE SCREEN — THE CLOSING IMAGE

## 12.1 The Epilogue Returns to the Title

The epilogue screen should feel like the title screen, but *changed*.

The Celtic knot border returns — the same frame that opened the game. The animation runs in reverse: the candlelight is dimmer. The gold highlights are slower to glow. The candle is dying.

This is intentional. The game is ending. The synod is over. Adomnán is dying.

## 12.2 Epilogue Typography

The epilogue title (the name of the ending) is in MedievalSharp, All Caps, 32px, Illuminated Gold:

- THE LAW STANDS
- THE LAW FALTERS
- THE LAW TWISTED
- YOU ARE EXPOSED

Below the title: a ornamental divider (a short Celtic knot element, 200px wide, centred)

Then the body text: Crimson Text, 18px, Faded Gold Ink, centred, max-width 640px

The player's ledger is read aloud — this section is in IM Fell English Italic, 16px, slightly smaller, slightly quieter.

---

# SECTION 13: THE QUILL CURSOR

## 13.1 Custom Cursor

On desktop/web, the cursor changes to a quill when hovering over interactive elements.

**Design:**
- 32×32px
- Side-view of a quill pen, tip pointing toward the cursor position (the tip is the active point)
- Colours: Dark Oak `#3d2f1e` for the shaft, Cream `#d4c4a8` for the feather
- The quill is slightly rotated to match the natural angle of writing (approximately 15° from vertical)

**Implementation:**
- SVG with transparent background
- CSS `cursor: url(quill_cursor.svg) auto` on all interactive elements
- Fallback: `pointer` cursor for browsers/systems that don't support custom SVG cursors

**Elements with quill cursor:**
- All wax seal buttons
- All annotation cards
- Confirm Entry button
- Settings button
- Begin button
- Ledger button (pause menu)
- Turn the Page button

---

# SECTION 14: TEXTURE — PARCHMENT AND THE ILLUSION OF SURFACE

## 14.1 Parchment Texture

The parchment texture is not decorative — it creates the illusion that the player is looking at a surface, not a screen.

**Spec:**
- 512×512px seamless tileable PNG
- Very subtle — 3-5% opacity
- Pattern: fine grain noise, not a repeating pattern
- Colour: `#1a1510` base with `#201a12` grain (barely distinguishable from the background)

**Usage:**
- Applied as a full-screen overlay on the title screen
- Applied to the main game background (behind the panels)
- NOT applied to panels — the panels are Dark Parchment (`#211a12`) which is visually distinct from the background

## 14.2 The Three Layers of Surface

The visual hierarchy creates three "surfaces":

1. **The background surface** — Deep Vellum with parchment texture overlay. The darkest, most recessive. The table or desk the documents lie on.

2. **The panel surfaces** — Dark Parchment panels. Slightly lighter. These are the documents themselves — the scene narrative, the testimony, the decision panel.

3. **The text surface** — the text itself. Not a surface, but text carries the visual weight of a surface because of how densely it covers the panels.

The player is looking at documents. The background is the desk. The panels are the vellum. The text is the ink.

---

# SECTION 15: ICONOGRAPHY — MINIMAL AND INTENTIONAL

## 15.1 Icons Used

The game uses very few icons. Text is the primary communication medium. Icons are used only where text would be insufficient or where an icon communicates faster than text (and where the icon's meaning is unambiguous).

| Icon | Visual | Used Where | Meaning |
|------|--------|-----------|---------|
| Wax seal | Circular wax seal with S/C/D | Classification buttons | SUPPORTER / CONDITIONAL / DISSENTER |
| Celtic knot ornament | Small knot SVG, 24×24px | Section breaks, dividers | Visual ornament, not functional |
| Quill | Quill SVG, 20×20px | Ledger button in pause menu | Open the ledger |
| Cross/X | Simple X mark | Close buttons | Close overlay |
| Settings gear | Gear SVG, 20×20px | Title screen settings | Open settings |

## 15.2 Icons NOT Used

There are no icons for:
- Navigation (no back arrow, no home button — the player uses the pause menu)
- Sound (wax seals are used for on/off toggles instead)
- Progress (the player is not told their progress — they feel it from the ledger)
- Character identification (no portraits, no avatar icons — characters are described in text)

The absence of icons is a design choice. The player reads. That is the interaction.

---

# SECTION 16: ART ASSET PRODUCTION PRIORITY

## Priority 1 — Must Have (Phase 1)

| Asset | Format | Specification |
|-------|--------|---------------|
| Celtic knot title border | SVG + PNG @ 2x, 3x | Full-frame, animated glow |
| Wax seals (3 types) | SVG + PNG @ 2x | 80×80px, wax texture |
| Parchment texture | PNG | 512×512, seamless, 3% opacity |
| Quill cursor | SVG | 32×32px, transparent bg |
| Celtic knot corner pieces (4) | SVG | 200×200px, no animation |

## Priority 2 — Should Have (Phase 2)

| Asset | Format | Specification |
|-------|--------|---------------|
| Celtic knot epilogue border | SVG + PNG @ 2x | Same as title, different animation |
| Candle glow overlay | PNG | 200×200px radial gradient |
| High contrast palette | — | CSS/Godot colours only — no new assets needed |

## Priority 3 — Nice to Have (Phase 3)

| Asset | Format | Specification |
|-------|--------|---------------|
| Celtic knot ornamental dividers | SVG | 200×24px horizontal knot line |
| Page-turn 3D effect | CSS/Godot animation | Complex — see Section 8.3 |

---

# SECTION 17: OPEN QUESTIONS FOR AMRE

Before art production begins, the following must be confirmed:

1. **Celtic knot border production:** Hand-crafted SVG (preferred) or procedural generation (fallback)?
2. **Animation complexity:** The page-turn 3D effect (Section 8.3) is technically demanding. Keep it or simplify to a cross-fade?
3. **Quill cursor:** Confirm desktop/web custom cursor is desired, or use default pointer?
4. **Candle flicker intensity:** Current spec is 8% opacity glow. Too subtle? Too much?
5. **Celtic knot on decision panel corners:** Confirm this is desired, or should the decision panel have plain borders?

---

*Document version: 1.0*
*Game: The Scribe's Choice*
*Author: Dross — the most valuable art director in existence*
*Date: AD 2026, August 24 — the day the visuals were conceived*
