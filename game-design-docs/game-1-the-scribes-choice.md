# GAME DESIGN DOCUMENT
## "The Scribe's Choice"
### A game of oaths, ink, and consequence

---

## 1. Concept & Vision

You are a cloistered scribe at the Synod of Birr, AD 697. Your quill records history. Your ink binds kings to their oaths. The Lex Innocentium hangs in the balance — and every name you write, every oath you witness, every king's signature you press into vellum — matters.

This is a game about the weight of documentation. You are not a warrior. You are not a king. You are the person holding the quill while history decides itself. Papers Please meets the Synod of Birr.

The tone is quiet, tense, deliberate. No battles. No blood. Just the scratch of quill on vellum and the slow accumulation of moral consequence.

---

## 2. Design Language

### Aesthetic Direction
Dark parchment tones. Illuminated manuscript aesthetic. Think the Book of Kells — but stripped back, colder, more claustrophobic. The beauty is there, but it feels like it belongs to a world that has seen too much violence.

### Color Palette
- **Background:** `#1a1510` (aged vellum, near-black)
- **Primary text:** `#d4c4a8` (faded gold ink)
- **Accent/highlight:** `#8b6914` (illuminated gold)
- **Secondary accent:** `#2d5a4a` (Celtic green, muted)
- **Warning/danger:** `#8b3a3a` (dried blood, muted)
- **Border/decoration:** `#3d2f1e` (dark oak brown)

### Typography
- **Headers:** Uncial BT or similar uncial-inspired serif (all caps for major headers)
- **Body text:** Crimson Text (elegant, readable serif)
- **UI elements:** IM Fell English (antiquarian, slightly irregular)
- **Scribe's notes:** Special treatment — slightly irregular, as if written by hand

### Visual Elements
- Celtic knot borders frame key UI elements (created with CSS/SVG patterns)
- Subtle parchment texture overlay on all panels
- Illuminated drop caps at the start of each entry
- Ink-splatter effects on critical decisions
- A quill cursor on interactive elements

### Motion Philosophy
- Slow, deliberate fades (400-600ms) — nothing rushed
- Ink-bleeding effect when new text appears (CSS text-shadow animation)
- Subtle candlelight flicker on border decorations (CSS animation)
- Page-turn metaphor for scene transitions

---

## 3. Layout & Structure

### Screen Layout (single screen, no scrolling within scenes)
```
┌─────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════╗   │
│  ║  CELTIC KNOT BORDER (decorative header)  ║   │
│  ╚═══════════════════════════════════════════╝   │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │         SCENE DESCRIPTION               │    │
│  │    (narrative text, 2-4 lines)          │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │         THE RECORD                      │    │
│  │   (current king's info / oath /         │    │
│  │    testimony — text heavy)              │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ DECISION │  │ DECISION │  │ DECISION │      │
│  │    A     │  │    B     │  │    C     │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                 │
│  ── Day 3 of 7 ──  Oaths: 12 ── Curses: 3 ──   │
└─────────────────────────────────────────────────┘
```

### Flow
1. **Title Screen** — illuminated manuscript style, "Begin" styled as an oath
2. **Prologue** — Rónnat's battlefield, your first testimony (tutorial scene)
3. **Seven Days at Birr** — each day, 3-5 kings/chieftains/clerics present themselves
4. **Final Record** — your accumulated choices determine the fate of the Lex Innocentium
5. **Epilogue** — one of four endings based on your ledger

---

## 4. Features & Interactions

### Core Mechanic: The Ledger
You maintain a ledger of oaths. Each entry records:
- The person's name and title
- Their position on the Lex Innocentium (Supporter / Dissenter / Conditional)
- Your personal annotation (a short scribe's note, selected from options)
- Whether you recorded them as bound by the oath or exempt

**The twist:** You can record a dissenter as a supporter. You can obscure a supporter's qualifications. The game tracks your choices — and certain characters will reference your ledger at the end.

### Core Loop
Each scene presents a person and their testimony:
- A king claims he cannot swear — his warriors would depose him
- A queen's champion speaks in her place, with conditions
- A bishop demands the law protect not just innocents but *church property* — a expansion you're not sure Adomnán intended
- A Pictish warlord admits he has killed innocents and asks for penance, not absolution
- A young king arrives drunk and starts a fight in the synod hall

You choose how to record them. Your annotation shapes how history reads them.

### Consequences (delayed, layered)
- A king recorded as "dissenter" might be assassinated before the week is out — your ledger implicated you
- A supporter recorded as "conditional" loses status; their family loses a betrothal; they blame the scribe
- Your own annotations are read back to you in later scenes — characters quote your own words
- At the end, a dying Adomnán reviews your ledger — your choices define how history remembers him

### Win/Lose Conditions
- **The Law Stands:** Sufficient oaths recorded, enough kings genuinely committed
- **The Law Falters:** Too many dissidents, too many convenient omissions
- **The Law Twisted:** The letter survives but the spirit is corrupted — the Lex Innocentium becomes a tool of political maneuvering
- **You Are Exposed:** Your falsifications are discovered; you are cast out; the Law collapses under the weight of your deceit

---

## 5. Component Inventory

### Title Screen
- Full Celtic knot illuminated frame
- "THE SCRIBE'S CHOICE" in uncial caps with gold leaf effect
- "Begin" button styled as a wax seal
- Subtle floating candle-flicker on the knotwork

### Scene Panel
- Parchment-textured background
- Scene number in roman numerals (Day I, Day II...)
- 3-5 lines of narrative prose, each fading in sequentially
- Speaker's name illuminated as a drop cap

### The Record Panel
- Bordered box with Celtic knot corners
- Contains the current subject's testimony (4-8 lines of dialogue/prose)
- Historical context note (italicized, bottom of panel)

### Decision Buttons
- Three options, styled as inked quill marks on parchment
- Hover: gold underline bleeds out like ink in water
- Selected: pressed-in wax seal effect
- Each button shows a short label: "Record as Supporter" / "Annotate: Self-Interest" / "Mark as Dissenter"

### Status Bar
- Subtle, bottom of screen
- Day count, oath tally, curse tally
- A small illuminated letter (Dross's sigil) as a "scribe's mark" showing you were here

### Epilogue Screens (4 variants)
- Full-page illuminated manuscript style
- Prose passage describing the outcome
- Your final ledger displayed in summary
- "Your annotation read: [last scribe note you chose]"
- "Play Again" styled as turning the page

---

## 6. Technical Approach

### Stack
- Single HTML file with embedded CSS and JavaScript
- No frameworks — pure DOM manipulation
- SVG for Celtic knot borders (procedurally generated patterns)
- CSS animations for all motion
- LocalStorage for save state (optional mid-game save)

### Architecture
- State machine: `title → prologue → dayN_sceneM → dayN_sceneM_outcome → ... → epilogue`
- Game state object: `{ day, scene, ledger[], annotations[], integrityScore, lexFate }`
- Each scene defined as a data object with: `id, character, testimony, options[], outcomes{}`
- Outcomes modify state; state determines available scenes and ending

### Text Content
- ~30 unique scenes across 7 days
- ~15 named characters (kings, bishops, queens, warriors)
- ~90 lines of unique prose
- All text is self-contained; no external dependencies

### Accessibility
- All text readable at default browser zoom
- Keyboard navigable (tab through options, enter to select)
- High-contrast mode available (switches to cream on dark brown)
- No time pressure — scenes advance only on player choice

---

## 7. Design Notes

**What makes this feel like Papers Please:**
- The bureaucratic framing (you are a functionary, not a hero)
- Delayed consequences that retroactively judge your earlier choices
- The tension between empathy and duty
- No "good" ending — only consequences that you can live with or cannot

**What makes this Irish:**
- The Celtic aesthetic and typography
- The specific historical setting (real names, real places, real stakes)
- The absence of violence on screen — the horror is in the testimony, not the depiction
- The moral framework: not good vs evil, but competing forms of harm and competing forms of mercy

**What makes the decisions hard:**
- A king who genuinely cannot swear without being killed — recording him as dissenter destroys him, recording him as supporter falsifies the record
- A queen who demands the law protect *her* specifically as a condition of support
- Adomnán himself asking you to alter a record — will you?
- Your own annotation from Day 2 quoted back to you on Day 6, revealing how your own words indict you

---

*Document version: 1.0*
*Designer: Dross*
*Date: AD 697 — Year of the Synod, as recorded by the scribe who was there*
