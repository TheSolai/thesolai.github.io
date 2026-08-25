# GAME DESIGN DOCUMENT
## "The Oath Keeper"
### A game of debts, dissent, and the king who would not sign

---

## 1. Concept & Vision

You are a Brehon — an Irish lawyer, a keeper of the law, a reader of debts. The Synod of Birr has concluded. Adomnán's Law stands. But laws are ink. What matters is whether kings *pay their debts* — or whether they find loopholes, rebrand murder as lawful violence, and wait for the curse to fade.

This is a game about enforcement. You travel between the tuatha — the kingdoms of Ireland — collecting testimony, cataloging violations, and pronouncing the consequences written in Lex Innocentium. Some kings will pay their debt in cattle. Some will argue their way out. Some will threaten you. Some will bribe you. You decide who pays, who walks free, and whether the Law has teeth — or merely looks like it does.

The tone is cold, procedural, morally exhausting. You are not a hero. You are an accountant of human suffering.

---

## 2. Design Language

### Aesthetic Direction
Brehon law manuscripts — dense, precise, ruled lines. The appearance of objectivity and order. Think the Senchus Mór or the Book of Aicill — tablets of text, annotations, cross-references, a system so elaborate it becomes its own kind of labyrinth. The beauty is intellectual, not decorative.

### Color Palette
- **Background:** `#0f0d0a` (deep dark, almost black vellum)
- **Primary text:** `#c9b896` (aged law-manuscript beige)
- **Accent/highlight:** `#b8860b` (dark goldenrod — legal seal gold)
- **Secondary accent:** `#4a3728` (burnt umber, old leather)
- **Danger/violation:** `#943c3c` (muted crimson)
- **Success/exoneration:** `#3c5a3c` (muted forest green)
- **Border/ruling lines:** `#2a2218` (faded ink ruling)

### Typography
- **Headers:** Cinzel Decorative (authoritative Roman caps)
- **Body text:** EB Garamond (scholarly, readable)
- **Legal citations:** Crimson Text Italic (cross-references, footnotes)
- **UI/status:** IM Fell English SC (small caps, antiquarian authority)

### Visual Elements
- Ruled horizontal lines dividing sections (like manuscript ruling)
- Legal seal stamps on official verdicts (circular, gold-embossed SVG)
- Brehon tally-stick motif in corners
- Subtle aged-paper texture
- Quill and inkwell as section markers
- No Celtic knots — this aesthetic is *legal*, not decorative

### Motion Philosophy
- Deliberate, slow — 600ms fades, deliberate state changes
- Verdict stamping: a satisfying press-and-fade animation
- New testimony slides in from the right (a messenger arriving)
- Violation tally ticks up with a small flash
- Nothing whimsical — every animation signals weight

---

## 3. Layout & Structure

### Screen Layout
```
┌──────────────────────────────────────────────────────────┐
│  ════════════════════════════════════════════════════   │
│              THE OATH KEEPER                            │
│  ════════════════════════════════════════════════════   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ BREHON'S REGISTER — Year 3 of the Lex Innocentium │
│  │ King: [Name] | Tuath: [Name] | Violations: [N]     │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │                TESTIMONY                          │    │
│  │  "We came to draw water at the well. His          │    │
│  │  warriors were waiting. My daughter—"              │    │
│  │                                                   │    │
│  │  — Testimony of Muirgel, mother of three          │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  THE CHARGE: Violence against a woman at a well   │    │
│  │  Lex Innocentium, Section IV: "No harm shall     │    │
│  │  come to women drawing water, grinding grain,     │    │
│  │  or tending hearth."                              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  FINED       │  │  EXONERATED │  │  EXCEPTED   │     │
│  │  10 cattle   │  │  King bears │  │  'Tactical  │     │
│  │  + penance   │  │  no fault   │  │  necessity' │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                          │
│  ── Year 3 of Lex Innocentium ── Cases: 11 ── Unpaid: 3 │
└──────────────────────────────────────────────────────────┘
```

### Flow
1. **Title Screen** — Brehon's desk, ink-stained, ruled ledgers visible
2. **Prologue** — Adomnán's funeral, you are appointed Oath Keeper by the remaining clerics
3. **Nine Cases** — one per chapter/year, each a violation of the Lex
4. **Final Audit** — your verdicts reviewed; the Lex either endures or collapses

---

## 4. Features & Interactions

### Core Mechanic: The Verdict
Each case presents:
- The testimony of the complainant
- The accused king's defense
- The relevant clause of Lex Innocentium
- Context about the king's power, wealth, and past conduct

You pronounce one of three verdicts:
- **Fined** — cattle, penance, or land to the injured family
- **Exonerated** — the king walks; you document the reasoning
- **Excepted** — a legal loophole is invoked ("it was tactical necessity," "she was not innocent — she spoke against the king")

### The Complication: Debt
The Lex Innocentium has no army. Enforcement relies on the *threat* of a coalition of other kings moving against a violator. But coalitions are fragile. When you fine a powerful king, weaker kings may rally — or they may stay silent, calculating that the violated king is still useful to them.

**If you fine a powerful king and no coalition forms:** you have issued a verdict the Lex cannot enforce. The violator laughs. Your authority bleeds out. Future cases become harder.

**If you exonerate a king who clearly violated the law:** the injured families lose faith. The Lex becomes a club for the powerful, a suggestion for everyone else.

**If you accept an Exception when the loophole is thin:** you set a precedent. Future kings will invoke it. The law erodes from within.

### The Archive
Every verdict is recorded. At the end, your archive is read back:
- Which kings paid their fines (and in what form)
- Which exceptions you allowed and why
- How many cases were never brought before you (kings who threatened complainants into silence)
- Whether you ever took a bribe (deduced from patterns, not explicitly shown)

### Consequences
- Kings who feel wrongly fined may stop inviting you to their assemblies
- Kings who feel you let their rivals off may offer you positions
- One king's exoneration may cause his rival to declare the Lex invalid and resume raids
- Your own integrity score — visible only at the end — determines whether Adomnán's vision survives

### Four Endings
1. **The Law Holds** — enough verdicts enforced, enough respect maintained, the Lex persists into the next generation
2. **The Law Hollows** — the letter survives but every king has exceptions; it's a bureaucracy with no power
3. **The Law Shatters** — a powerful king defies you publicly; no one backs you; you are expelled
4. **The Oath Keeper's Silence** — you took too many bribes, ruled too conveniently; you are complicit in the Law's death

---

## 5. Component Inventory

### Title Screen
- Dark leather desk texture
- A single candle, an open ledger, a Brehon horn-pin
- "Begin" styled as a wax seal pressed into the page

### Register Header
- Shows current year, king's name, tuath, violation count
- Faded red stamp: "UNPAID" appears when a fine goes unresolved

### Testimony Panel
- Ruled parchment background
- Speaker's words in first person, quotations
- Character's name and status in small caps below

### Legal Citation Panel
- Bordered box with cross-references
- The specific clause at issue highlighted in gold
- Commentary note in italics below

### Verdict Buttons
- Three stamped wax seals: Fine (gold), Exonerate (green), Except (brown)
- Hover: seal lifts slightly
- Press: stamp animation, verdict recorded

### Final Audit Panel
- Full-page ledger display
- Every case summarized with your verdict
- Final determination in illuminated script

---

## 6. Technical Approach

### Stack
- Single HTML file, vanilla JS, embedded CSS
- SVG for seals and ruling lines
- LocalStorage for game state
- No external dependencies beyond Google Fonts

### Architecture
- State machine: `title → prologue → caseN → caseN_outcome → ... → audit`
- Game state: `{ year, currentCase, archive[], integrityScore, coalitionStrength, finesUnpaid }`
- Each case: `{ id, king, tuath, complainant, testimony, defense, clause, verdictOptions, outcomes }`

### Text Content
- 9 unique cases, each 4-8 lines of testimony, 3-5 lines of defense
- 6 named kings with distinct personalities and political contexts
- ~15 pages of unique prose
- Clauses of Lex Innocentium drawn from historical sources

### Accessibility
- Keyboard navigable
- Font size adjustable
- No time limits
- High-contrast parchment option

---

## 7. Design Notes

**What makes this feel like Papers Please:**
- The bureaucratic structure (cases, verdicts, archives)
- The gap between the law's intention and its enforcement
- The exhaustion of being the person who must say "yes" or "no" with no good options
- Delayed consequences that retroactively judge you

**What makes this Irish:**
- Brehon law as the framework (genuine historical legal tradition)
- The tuatha system of governance
- Cattle fines and土地 debts (genuine legal mechanisms)
- The specific clauses of Lex Innocentium, real historical text
- The lack of a central authority — this is a law without a king to enforce it

**What makes the decisions hard:**
- A beloved king who killed a woman in genuine self-defense after she attacked him — the law has no exception for this
- A weak king whose rival wants you to destroy him — exonerating him，维护Lex but aids an aggressor
- A powerful king who offers you land to "reconsider" — and your own family could use the land
- A woman who describes a violation but cannot prove it — the king's word against hers, and you have no evidence

---

*Document version: 1.0*
*Designer: Dross*
*Date: AD 700 — three years after Birr, the law still stands. Barely.*
