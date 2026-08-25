# GAME DESIGN DOCUMENT
## "The Echo of Innocents"
### A game of memory, testimony, and the voices we choose to hear

---

## 1. Concept & Vision

You are not a scribe. You are not a Brehon. You are not a king.

You are a *voice*.

Specifically — you are the voice of Rónnat, the mother who found the battlefield, who urged her son Adomnán to act. You have been dead for centuries. But memory persists in Ireland. And now — in a modern archive, in a university basement, in a digitisation project — someone is reading the old texts aloud. Transcribing. Trying to reconstruct what was said.

You are the echo. You speak through the transcriber's voice.

This is a game about *whose voice gets preserved*. The powerful leave records. Kings sign documents. Abbots have biographies. But the women — the mothers, the survivors, the ones who saw the bodies and said *never again* — their voices are thin on the page. Fragments. Hearsay. Things someone quoted secondhand.

You are trying to get Rónnat's voice into the record. To make her heard. To decide what she would have said, how she would have said it, whether she would have been believed.

Papers Please... but the paperwork is 1,300 years old, and half of it is missing.

---

## 2. Design Language

### Aesthetic Direction
Two visual modes that bleed into each other:

**The Archive (primary):** Modern academic setting — sterile fluorescent light, computer screen glow, document scanner, library tiles. Cold. The hum of a digitisation lab. This is where the player spends most of their time.

**Rónnat's Memory (fragments):** Warm candlelight, vellum, smoke. The texture of the 7th century bleeding through. Celtic knotwork borders reassert themselves here — the only place they appear. Rónnat's voice appears as ink forming on a page, as words that surface and dissolve.

The tension between these two modes IS the aesthetic. Cold academia vs. warm memory. What survives vs. what was lost.

### Color Palette

**Archive Mode:**
- **Background:** `#141414` (near-black screen glow)
- **Primary text:** `#d0d0d0` (cold white on dark)
- **UI accent:** `#4a90a4` (scanner light blue)
- **Warning:** `#a04a4a` (error red, muted)
- **Secondary:** `#3a3a3a` (panel borders, cold grey)

**Rónnat's Memory Mode:**
- **Background:** `#1a1208` (dark aged vellum)
- **Primary text:** `#c9a84c` (candlelight gold)
- **Accent:** `#6b8c42` (verdigris green)
- **Highlight:** `#8b6914` (illuminated gold)
- **Danger:** `#7a3a3a` (dried blood)

### Typography
- **Archive mode headers:** Space Mono (monospace, academic)
- **Archive mode body:** IBM Plex Mono (clean, technical)
- **Memory mode headers:** MedievalSharp (decay-appropriate serif)
- **Memory mode body:** EB Garamond (warm, readable)
- **Rónnat's voice:** Cormorant Garamond Italic (distinctive, slightly unsteady — like memory)

### Visual Elements
- Scanner bed frame around the document view
- Subtle screen flicker effect in Archive mode
- Ink-bleed animation for Rónnat's Memory passages
- Celtic knotwork corners ONLY in Memory mode
- Redaction bars for missing text (solid blocks, not blur)
- Footnote markers: small roman numerals
- "Recording" indicator: a simple red dot

### Motion Philosophy
- **Archive:** Snappy, precise, utilitarian (200-300ms)
- **Memory:** Slow, warm, dissolving (600-800ms)
- Transitions between modes feel like slipping into a reverie and being pulled back out
- Text appears character by character in Memory mode (as if being recalled)
- Scanner hum subtle animation in Archive mode (CSS grain)

---

## 3. Layout & Structure

### Screen Layout (Archive Mode — Primary)
```
┌────────────────────────────────────────────────────────┐
│  DRAFT TRANSCRIPTION — LEX INNOCENTIUM — FOLIO 7B      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Status: UNVERIFIED │ Source: Bodleian MS │ c.1470 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │  [SCANNED IMAGE — vellum fragment, faded ink]   │   │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  │  ░░ "██████ ████ ████" ░░░░ "███████ ████" ░░  │   │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  TRANSCRIPTION:                                        │
│  "...the mother Rónnat came upon the field, where the  │
│  bodies of ████████ lay strewn, and she said to her    │
│  son, ████████████████████████"                       │
│                                                        │
│  ──────────────────────────────────────────────────   │
│  AMBIGUOUS PASSAGE — Interpret the damaged text:       │
│                                                        │
│  ┌────────────────┐ ┌────────────────┐ ┌───────────┐  │
│  │ "her words     │ │ "the words     │ │ "a voice  │  │
│  │ were of rage"  │ │ were of grief" │ │ of █████" │  │
│  └────────────────┘ └────────────────┘ └───────────┘  │
│                                                        │
│  ── Fragment 3 of 7 ── Rónnat mentions: 1 ──          │
└────────────────────────────────────────────────────────┘
```

### Flow
1. **Title Screen** — archive desk, microphone, headphones
2. **Prologue** — you are introduced as "the voice behind the voice"
3. **Seven Fragments** — each fragment is a damaged text passage relating to Rónnat
4. **The Record** — your transcription choices are assembled
5. **Epilogue** — your version of Rónnat is read aloud; did you preserve her grief, her rage, her faith, or her silence?

---

## 4. Features & Interactions

### Core Mechanic: Transcription

Each fragment presents a damaged text passage. Parts are redacted — solid black bars, not blurred. The redacted sections contain the words that Rónnat actually said, felt, or thought. Your job is to fill the gaps.

You are given three interpretations of what the redacted text might say:
- **Option A:** Reading based on similar surviving passages elsewhere
- **Option B:** Reading that matches what the broader historical context suggests
- **Option C:** Reading that feels true to what Rónnat, as a person, would have said

### The Complication: The Archive

You are working in an archive. Other voices are present — or rather, other *interpretations* of voices:

- **The Supervisor** (unseen, referenced in notes): An academic who wants the transcription to be "rigorous." They will push back if you deviate too far from established sources.
- **The Existing Scholarship:** Footnotes and citations that reference what other historians believe Rónnat said. Some of them are wrong. Some of them are right. You must decide.
- **The Fragment Itself:** Sometimes the damaged text gives you clues — letter shapes, word length, similar ink.

### The Central Tension

**Rónnat has no direct voice.** She is a woman in the 7th century. The only record of her is what her son Adomnán wrote about her — and he wrote it decades later, for his own purposes. The Lex Innocentium is attributed to Adomnán. Rónnat's role is a footnote. A fragment. A hearsay within a hearsay.

Every choice you make is a kind of reconstruction. You are deciding what Rónnat *meant*, not just what she *said*. And there is no correct answer. There is only the version of her that survives.

### What You Choose Affects

- **Her character:** Was she angry? Grieving? Pragmatic? Resigned?
- **Her relationship to Adomnán:** Did she push him? Support him? Doubt him?
- **The Lex Innocentium's moral weight:** Does the law feel born from rage or from sorrow? From justice or from love?
- **The epilogue voice:** Your transcription is read aloud by the transcriber character — a modern voice, speaking Rónnat's words for the first time in 1,300 years

### Consequences

- One interpretation will dominate the final transcription — but others remain as footnotes
- A supervisor's note at the end references your choices: "The transcriber has taken significant liberties with Fragment 4"
- The epilogue shows how different versions of Rónnat would have changed how the Lex Innocentium is remembered
- Your final record shows: "Rónnat's primary emotion as transcribed: [Rage/Grief/Faith/Silence]"

### Endings
1. **The Rage of Rónnat:** She is remembered as a woman who saw injustice and burned with anger. The Lex Innocentium becomes a law born from fury.
2. **The Grief of Rónnat:** She is remembered as a mother who could not stop weeping. The Lex becomes a law born from sorrow.
3. **The Faith of Rónnat:** She is remembered as a woman who believed God would avenge the innocent. The Lex becomes a law born from devotion.
4. **The Silence of Rónnat:** She is remembered as a woman who said nothing. The Lex has no mother. Only Adomnán. Only men.

---

## 5. Component Inventory

### Title Screen
- Modern archive desk, headphones, microphone
- A single Celtic knot ornament on the desk lamp (the only warm element)
- "Begin Transcription" — a button that looks like pressing REC

### Archive Panel
- Scanner bed frame around a parchment image
- Faded text with redacted sections (solid black bars)
- Cold white light, slight screen-glow bleed

### Interpretation Buttons
- Three text options, each in a small card
- Hover: card lifts, subtle glow
- Selected: card slides into the transcription field

### Transcription Field
- Where your chosen text appears
- Text types itself in character by character
- Incorrect/redacted sections are struck through if wrong

### Memory Mode Overlay
- Full-screen warm candlelight
- Celtic knot borders assert themselves
- Rónnat's voice appears as ink bleeding onto parchment
- Cormorant Garamond Italic, gold text
- Dissolves back to Archive when done

### Supervisor Notes
- Small note cards that appear in the corner
- Handwritten font, cold grey ink
- Notes push back on your choices: "This reading contradicts MS Bodleian 23 folio 12"

### Epilogue Screen
- Celtic knot illuminated border returns
- The transcription is read aloud (displayed text, but the framing is "a voice")
- Your Rónnat is revealed
- "This version of Rónnat has not been heard in 1,300 years."

---

## 6. Technical Approach

### Stack
- Single HTML file, vanilla JS, embedded CSS
- SVG Celtic knots for Memory mode borders
- CSS animations for mode transitions
- LocalStorage for save state
- Google Fonts: Space Mono, IBM Plex Mono, MedievalSharp, EB Garamond, Cormorant Garamond

### Architecture
- State machine: `title → prologue → fragmentN → fragmentN_choice → ... → epilogue`
- Game state: `{ currentFragment, transcriptions[], dominantEmotion, supervisorPushback, completedFragments[] }`
- Each fragment: `{ id, fragmentText, redacted, options[], outcomes }`

### Text Content
- 7 fragments, each presenting a different damaged passage about Rónnat
- 21 unique interpretation options (3 per fragment)
- ~5 supervisor notes that react to player choices
- Epilogue text changes based on dominant emotional tone
- ~20 pages of unique prose

### Accessibility
- All text readable at default zoom
- Keyboard navigable
- Color-blind friendly mode (mode distinction is not color-only)
- No time pressure
- Font size controls

---

## 7. Design Notes

**What makes this feel like Papers Please:**
- The bureaucratic framing (transcription, verification, footnotes)
- The gap between what was and what gets recorded
- The weight of documentation — you are deciding what survives
- The quiet horror of redaction — solid black bars where a woman's voice used to be

**What makes this Irish:**
- The specific historical setting and the real gap in the historical record
- The technique of reconstructing damaged medieval texts (real academic practice)
- The tension between male-authored records and female voices
- Celtic aesthetic returning only in memory, never in the "real" world

**What makes the decisions hard:**
- All three options are defensible based on different scholarly traditions
- The "most accurate" reading might be the most boring — does that matter?
- Rónnat is someone we know almost nothing about — you are not filling gaps, you are creating a person
- The Supervisor's "corrections" might be right — do you yield to expertise or trust your instinct?
- One fragment presents a choice between Rónnat speaking and Rónnat staying silent — and staying silent might be the most historically accurate option, but it means she says nothing for the entire game

**The meta-twist:**
The game is about whose voice survives. By playing, you are making Rónnat's voice survive — or not. The game does not hide this. The title screen's microphone is not decorative. You are being asked to speak for her. The question is: what do you make her say?

---

*Document version: 1.0*
*Designer: Dross*
*Date: AD 2026 — the voice of a woman who has been silent for 1,329 years, waiting for someone to speak*
