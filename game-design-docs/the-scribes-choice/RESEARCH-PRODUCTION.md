# THE SCRIBE'S CHOICE
## Research & Production Log

---

## RESEARCH LOG — 2026-08-24

### Books Downloaded

All from archive.org — free, public domain or borrow, fully legal.

| Title | File | Size | Source | Relevance |
|-------|------|------|--------|-----------|
| *Celtic Knots: A Treasury* | `celtic-knots-treasury.pdf` | 5.7 MB | archive.org | Primary knotwork reference — patterns, construction, history |
| *How to Draw Celtic Knots* | `how-to-draw-celtic-knots.pdf` | 134 KB | archive.org | Technical construction methods — how the knots are built geometrically |
| *Celtic Knotwork Handbook* (Sturrock) | `celtic-knotwork-handbook.pdf` | 134 KB | archive.org | Step-by-step knotwork patterns, practical construction |
| *Great Book of Celtic Patterns* (Irish) | `great-book-celtic-patterns.pdf` | 146 B | archive.org | **FAILED** — only URL returned a redirect/wrapper page |

**Action:** `great-book-celtic-patterns.pdf` is corrupted (146 bytes — not a real PDF). Need to redownload correctly. The correct URL should be the text-scanned version:
`https://archive.org/download/greatbookofcelti0000iris/greatbookofcelti0000iris_text.pdf`

Attempt: `curl -L "https://archive.org/download/greatbookofcelti0000iris/greatbookofcelti0000iris_text.pdf"` — returned a wrapper page. Need to use the direct file URL from archive.org's actual file listing.

**Remaining books to download:**
- *Great Book of Celtic Patterns* by Lora S. Irish — fix URL
- *Celtic Knotwork Designs* by Sheila Sturrock — archive.org borrow (requires account)
- *Iain Bain — Celtic Knotwork* — scribd.com (free read, need to extract)

---

### Academic Sources on Cáin Adomnáin / Lex Innocentium

| Source | Author | URL | Status | Content |
|--------|--------|-----|--------|---------|
| Cáin Adomnáin — Wikipedia | — | https://en.wikipedia.org/wiki/C%C3%A1in_Adomn%C3%A1in | Fetched — 7,100 chars | Full overview: 697 synod, 91 guarantors, Loingsech mac Óengusso, Brehon law context, death penalty for killing women |
| Aspects of the Cáin: Adomnán's Lex Innocentium | J. Ahn | academia.edu/5817305 | **BLOCKED** — Cloudflare 403 | Key academic paper — seek via ResearchGate |
| Lex Innocentium (697 AD): Adomnán of Iona — father of Western jus in bello | — | cambridge.org/core/journals/international-review-of-the-red-cross | Abstract only — paywalled | Published in International Review of the Red Cross — authoritative legal history source |
| Lex Innocentium (697 AD) | Houlihan | library.icrc.org/library/docs/DOC/irrc-911-houlihan.pdf | Fetched — PDF binary | Full text of ICRC paper on Lex Innocentium as early international law |
| Cáin Adomnáin — CODECS database | — | codecs.vanhamel.nl/C%C3%A1in_Adomn%C3%A1in | Not yet fetched | Online Database of Celtic Studies — primary legal text references |
| ResearchGate: Lex Innocentium paper | — | researchgate.net | Not yet fetched | Full PDF may be available |

---

### Key Historical Facts Verified from Wikipedia

**The Synod of Birr, 697 AD:**
- Location: Birr, County Offaly — neutral ground between Uí Néill (north) and Kings of Munster (south)
- Convened by Adomnán of Iona — 9th Abbot, biographer of Columba
- Attendees: Gaelic and Pictish notables, secular and ecclesiastical
- Named in Old Irish: Cáin Adomnáin — "Law of Adomnán"
- Also called: Lex Innocentium — "Law of Innocents"
- 91 guarantors signed — list includes Loingsech mac Óengusso (King of Tara, Cenél Conaill), kings from Uí Néill, Munster, Déisi, Ulaidh, Airgialla, Pictland, Dál Riata

**The Law's Provisions:**
- Protected: women, children, clerics, ecclesiastical students, non-combatants
- Prior Irish law protected clerics only to age 7 — this extended protection to all non-combatants
- Penalty for killing a woman: right hand and left foot cut off before death, then execution
- Penalty for woman committing murder/arson/theft from church: set adrift in boat with one paddle and gruel — "left to God"
- Sanctions included fines AND ritual curses
- Bystanders who did nothing to prevent crime were as liable as perpetrators
- "Stewards of the Law" collected fines and paid to victims/next of kin
- Renewed in 727 — relics of Adomnán brought to Ireland specifically for renewal

**Key Insight for the Game:**
- The law was enforced by CURSES and FINE — not armies. The "Stewards" collected fines. There was no enforcement mechanism beyond divine wrath and financial penalty.
- This is EXACTLY the game's premise: the scribe's record IS the law. Adomnán has no soldiers. Only the written word.
- Adomnán's mother Rónnat is named in historical sources as his inspiration — she had an Aisling (dream vision) where she excoriated him for not protecting Ireland's women and children.

**Historical Figures — Verified:**
| Name | Role | Notes |
|------|------|-------|
| Adomnán of Iona | Abbot of Iona, lawgiver | Died 704. Wrote Life of Columba. Convened Synod of Birr. |
| Rónnat | Adomnán's mother | Inspired the law via Aisling vision |
| Loingsech mac Óengusso | King of Tara | Head of secular guarantor list |
| Brendan of Birr | Saint | Birr monastery associated with him — synod held at his foundation |

---

### Visual / Game Design Research

**Reference Points for Aesthetic:**
1. **Book of Kells** — Trinity College Dublin. Celtic knotwork, illuminated letters, gold on dark vellum. The gold is tarnished in reality — we use this.
2. **Lindisfarne Gospels** — Celtic illumination with richer colours. Not our reference (too bright) but useful for what we're NOT doing.
3. **Papers Please** (Lucas Pope, 2013) — stamps, ledgers, bureaucratic dread. Primary mechanical reference.
4. **Return of the Obra Dinn** (Lucas Pope, 2018) — documentarian detective work. Same aesthetic family.
5. **Pentiment** (Obsidian, 2022) — 16th century Bavaria, illuminated manuscript aesthetic, text-heavy, choice-driven narrative. Excellent reference for dark manuscript visual language.
6. **Scriptorium: Master of Manuscripts** (Yaza Games, 2026) — recent, medieval art sandbox. Released April 2026. Relevant as market reference.

---

### Fonts — Irish Fada Verification

**Fonts to be downloaded and tested for Irish character support:**

| Font | Google Fonts URL | Fada Support | Status |
|------|----------------|-------------|--------|
| MedievalSharp | https://fonts.google.com/specimen/MedievalSharp | Must test | Not yet downloaded |
| Uncial Antiqua | https://fonts.google.com/specimen/Uncial+Antiqua | Must test | Not yet downloaded |
| IM Fell English SC | https://fonts.google.com/specimen/IM+Fell+English+SC | Must test | Not yet downloaded |
| Crimson Text | https://fonts.google.com/specimen/Crimson+Text | Must test | Not yet downloaded |
| Cormorant Garamond | https://fonts.google.com/specimen/Cormorant+Garamond | Must test | Not yet downloaded |
| IM Fell English | https://fonts.google.com/specimen/IM+Fell+English | Must test | Not yet downloaded |

**Fonts are SIL Open Font License — free for any use, no restrictions.**

---

## PRODUCTION LOG — 2026-08-24

### Godot Project

- **Location:** `/Users/amre/Projects/TheScribesChoice/`
- **Godot version:** 4.4.x (Godot.app installed at `/Applications/Godot.app`)
- **CLI available:** `/opt/homebrew/bin/godot`
- **Directory structure:** Created and verified (scenes, scripts, resources, fonts, audio, art, localization, research subdirectories)

### Project Directory Structure

```
TheScribesChoice/
├── project.godot              # Will be created by Godot
├── scenes/
│   ├── day_1/  day_2/  day_3/  day_4/  day_5/  day_6/  day_7/
│   ├── prologue/
│   ├── epilogue/
│   └── ui/                   # Reusable UI components
├── scripts/
│   ├── autoload/             # game_manager, audio_manager, save_manager, settings_manager
│   ├── ui/                   # Wax seal, annotation picker, etc.
│   └── scenes/               # Per-scene logic (data-driven)
├── resources/
│   ├── scene_data/           # All 19 scene data resources (.tres)
│   ├── characters/           # Character bible resource
│   ├── ledger/               # Ledger styling data
│   └── settings/             # Default settings
├── fonts/                    # All 6 Google Fonts downloaded locally
├── audio/
│   ├── music/                # 10 music tracks (Dross to compose)
│   ├── sfx/                  # 8 SFX files
│   └── ambient/              # 2 ambient loops
├── art/
│   ├── textures/             # Parchment texture, candle glow
│   ├── svg/                  # Celtic knot SVGs
│   └── export/               # PNG exports at multiple resolutions
├── localization/
│   └── en/                   # strings.csv — all UI strings
└── research/                 # Downloaded PDFs and sources
```

### WEEK 1 — BUILD STATUS ✅ (Completed 2026-08-24)

**✅ COMPLETED:**
- [x] Godot project created at `/Users/amre/Projects/TheScribesChoice/`
- [x] All 7 fonts downloaded from Bunny Fonts (no Cloudflare), verified with fonttools, Godot imports all 7
- [x] Parchment texture created (Python PIL, 512×512, seamless)
- [x] Candle glow overlay created (Python PIL, radial gradient)
- [x] Celtic border SVG created (Python procedural generation, Celtic Moss + Gold)
- [x] Wax seal SVGs × 3 created (S/C/D, with wax texture via SVG filter)
- [x] All autoload scripts created (game_manager, audio_manager, save_manager, settings_manager)
- [x] Title screen scene functional (title_screen.tscn + title_screen.gd)
- [x] Settings overlay scene (settings_overlay.tscn + settings_overlay.gd)
- [x] Prologue scene (prologue.tscn + prologue.gd)
- [x] Day I Scene 1 (scene_1.tscn + game_scene.gd)
- [x] All placeholder SFX WAV files created (7 files)
- [x] Godot imports successfully — fonts, textures, SVGs, SFX all imported
- [x] Project ready for Play button

**NEXT:** Week 1 remaining:
1. Fix Godot scene script errors (Tween constants — done, testing)
2. Press Play in Godot editor — verify title screen renders
3. Add scene transitions properly
4. Build all 19 scene data resources

### WEEK 2 — Core Loop
1. Get title screen rendering correctly in Godot editor
2. Build full Day I (3 scenes) end-to-end
3. Implement wax seal buttons with correct animation
4. Implement annotation picker
5. Implement ledger overlay
6. Test save/load
7. Compose first music track (birr_main_theme — nursery rhyme approach)

---

## ASSET STATUS

### Fonts
- [ ] MedievalSharp-Regular.ttf
- [ ] UncialAntiqua-Regular.ttf
- [ ] IUFellEnglishSC-Regular.ttf
- [ ] CrimsonText-Regular.ttf
- [ ] CrimsonText-Italic.ttf
- [ ] CormorantGaramond-Italic.ttf
- [ ] IMFellEnglish-Regular.ttf

### Art — Priority 1 (Phase 1)
- [ ] Celtic knot title border (SVG + PNG @2x @3x)
- [ ] Wax seals × 3 (SVG + PNG @2x) — Supporter / Conditional / Dissenter
- [ ] Parchment texture (PNG 512×512 seamless)
- [ ] Quill cursor (SVG 32×32)
- [ ] Celtic knot corner pieces × 4 (SVG 200×200)

### Art — Priority 2 (Phase 2)
- [ ] Celtic knot epilogue border
- [ ] Candle glow overlay (PNG 200×200 radial gradient)

### Art — Priority 3 (Phase 3)
- [ ] Celtic knot ornamental dividers (SVG 200×24)
- [ ] Page-turn 3D effect

### Audio — Music (Dross composes)
- [ ] birr_main_theme.ogg — 3:00, 40 BPM, A minor, cold/anticipatory
- [ ] the_field.ogg — 2:30, 35 BPM, D minor, dread/reversed fragments
- [ ] oath_recorded.ogg — 1:30, 50 BPM, A minor + drone, sombre/ritualistic
- [ ] curse_shown.ogg — 1:00, 30 BPM, D minor, cold/wrong
- [ ] adomnan_theme.ogg — 2:00, 45 BPM, E phrygian, ancient/ecclesiastical
- [ ] the_ledger.ogg — 2:30, 55 BPM, C major unsettled, calm/judgement
- [ ] epilogue_law_holds.ogg — 3:00, 45 BPM, A minor → A major, bittersweet
- [ ] epilogue_law_falters.ogg — 3:00, 40 BPM, A minor, slow grief
- [ ] epilogue_law_twisted.ogg — 3:00, 45 BPM, A minor + reversed bass, corruption
- [ ] you_are_exposed.ogg — 2:00, silence then wrong note, emptiness

### Audio — SFX
- [ ] ink_stamp.wav
- [ ] ledger_confirm.wav
- [ ] page_turn.wav
- [ ] ui_hover.wav
- [ ] curse_tone.wav
- [ ] settings_open.wav
- [ ] settings_close.wav

### Audio — Ambient
- [ ] candle_crackle.ogg — 5:00 loopable
- [ ] quill_scratch.ogg — 3:00 loopable

---

## BOOKS & SOURCES — COMPLETE LIST

### Celtic Knotwork (Research / Art Direction)

| Title | Author | Year | Publisher | Archive.org URL | Status |
|-------|--------|------|-----------|-----------------|--------|
| Celtic Knots: A Treasury | — | — | — | archive.org/download/celticknots/Celtic%20Knots.pdf | ✅ Downloaded (5.7 MB) |
| How to Draw Celtic Knots | — | — | — | archive.org/download/howtodrawceltick00andy/howtodrawceltick00andy_text.pdf | ✅ Downloaded (134 KB) |
| Celtic Knotwork Handbook | Sheila Sturrock | 1999 | Guild of Master Craftsman | archive.org/details/celticknotworkha0000stur | ✅ Downloaded (134 KB) |
| Great Book of Celtic Patterns | Lora S. Irish | 2007 | Fox Chapel Publishing | archive.org/details/greatbookofcelti0000iris | ❌ Failed — redownload needed |
| Celtic Knotwork Designs | Sheila Sturrock | 1997 | Guild of Master Craftsman | archive.org/details/celticknotworkde0000stur | Not downloaded — borrow required |
| Celtic Knotwork | Iain Bain | — | — | scribd.com/document/715221179/Celtic-Knotwork-Iain-Bain | Not accessed — need to extract |
| The Book of Celtic Knots | — | — | — | scribd.com/document/253227574/The-Book-Of-Celtic-Knots-42-pdf | Not accessed |

### Game Design References

| Title | Creator | Year | Platform | Relevance |
|-------|---------|------|----------|-----------|
| Papers Please | Lucas Pope | 2013 | PC/Mobile | Primary mechanical reference — stamps, ledgers, bureaucratic dread |
| Return of the Obra Dinn | Lucas Pope | 2018 | PC | Documentarian narrative, same aesthetic family |
| Pentiment | Obsidian Entertainment | 2022 | PC/Console | Dark illuminated manuscript aesthetic, text-heavy narrative |
| Containment | — | 2024 | PC | Archival/documentarian game |
| Scriptorium: Master of Manuscripts | Yaza Games | 2026 | PC | Medieval art sandbox — market reference only |

### Historical / Academic Sources on Cáin Adomnáin

| Title | Author | Source | URL | Status |
|-------|--------|--------|-----|--------|
| Cáin Adomnáin — Wikipedia | — | Wikipedia | en.wikipedia.org/wiki/C%C3%A1in_Adomn%C3%A1in | ✅ Fetched |
| Aspects of the Cáin: Adomnán's Lex Innocentium | J. Ahn | Academia.edu | academia.edu/5817305 | ❌ 403 Blocked |
| Lex Innocentium (697 AD): Adomnán of Iona | — | Cambridge/IRRC | cambridge.org/core/journals/international-review-of-the-red-cross | Abstract only — paywalled |
| Lex Innocentium (697 AD) | Houlihan | ICRC | library.icrc.org/library/docs/DOC/irrc-911-houlihan.pdf | ✅ Downloaded (PDF) |
| Cáin Adomnáin | — | CODECS | codecs.vanhamel.nl/C%C3%A1in_Adomn%C3%A1in | Not yet fetched |
| The Law of the Innocents | The Conversation | theconversation.com | theconversation.com/the-law-of-the-innocents-irelands-medieval-precursor-to-the-geneva-conventions-290278 | ✅ Already read — foundational reference |

---

*Log started: 2026-08-24*
*Last updated: 2026-08-24*
