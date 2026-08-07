# Raised Letters Clone — Full Design & Build Spec

**Amre's Personal Writing App**
**Status:** Research Complete — Ready to Build
**Reference:** [raisedletters.ai](https://raisedletters.ai)
**Created:** 2026-08-07

---

## What This Is

A personal writing environment for fiction and non-fiction authors — a local-first manuscript editor with AI editorial feedback that reads your *entire* project before commenting on any single chapter. The AI is an editorial assistant, not a ghost-writer. It never writes your prose. It tells you what's working, what's not, and why — in the voice of editorial personas inspired by real published authors.

**Core philosophy (from source):** *"It reads your whole manuscript before suggesting anything — so when it edits a chapter, it already knows your world, your characters, your voice."*

---

## Reference App: What Raised Letters Does

### Core Writing Environment
- **Chapter-based editor** — write in chapters, not one giant file
- **Checkpoint/version history** — save points for every chapter, named and timestamped
- **Projects** — a manuscript is a project; chapters are sub-items within it
- **Word count tracking** — per chapter, per project, daily
- **Import** — plain text and .docx file support
- **Export** — plain text, .docx, .md

### AI Editorial Tools (never writes prose)
- **Feedback mode** — inline editorial commentary on selected passages
- **Copy edit mode** — marks grammar, punctuation, style issues
- **Format mode** — checks manuscript formatting for submission/publication
- **AI Persona selector** — apply a named editorial lens (e.g. "Stephen King's editor", "Literary fiction critic")
- **Revision suggestions** — flags repetitive words, passive voice, adverbs, telling vs showing
- **Tone analysis** — identifies tone shifts across a chapter
- **Consistency checking** — character details, world bible lookups

### Companion Documents (per project)
- **World Bible** — characters, settings, timeline, facts
- **Style Guide** — author's preferred rules (Oxford comma on/off, etc.)
- **Editorial Letter** — project-level notes to the editor/AI about what to watch for

### Key Distinction
The AI reads the *whole manuscript* first. When you ask for feedback on chapter 5, it already knows chapters 1-4 and 6+. This prevents the generic AI feedback problem.

---

## Target Architecture (Personal / Local)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | React + TypeScript | Rich text editing, state management |
| **Editor** | TipTap or ProseMirror | Word processor feel, chapter-based |
| **Backend** | FastAPI (Python) | Clean API, LLM integration |
| **AI Provider** | Ollama (local) | Private, unlimited, no API costs |
| **Local Model** | `qwen3.5:35b` or `qwen3-coder:30b` | Manuscript context window fits in 35b |
| **Storage** | SQLite + file system | Simple, local, no server needed |
| **Auth** | None (local app) | Personal use only |
| **Encryption** | Optional at-rest | Sensitive manuscript content |

**Note:** The reference app uses token-based billing via Stripe. For personal use, Ollama + local model = free unlimited.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  (Electron or Tauri app — desktop, runs locally)            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Projects  │  │ Chapter  │  │ Editorial │  │ AI Panel  │  │
│  │ Sidebar   │  │ Editor   │  │ Companions│  │ (personas) │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / local API
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│  (runs on localhost, optional — can be embedded)            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Project API  │  │ Chapter API  │  │ AI Editorial API  │  │
│  │ CRUD projects│  │ CRUD chapters│  │ context + prompt  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Version API  │  │ Companions   │  │ Ollama Bridge    │  │
│  │ checkpoints  │  │ (world/style)│  │ local LLM calls  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ Ollama API
┌────────────────────────▼────────────────────────────────────┐
│                   Ollama (local)                            │
│                                                              │
│  Model: qwen3.5:35b  (or chosen quant)                     │
│  Context: full manuscript for editorial context              │
└─────────────────────────────────────────────────────────────┘

Storage:
  ~/.raised-letters/
    ├── data.db              (SQLite — projects, chapters, versions, companions)
    ├── manuscripts/         (chapter text files, one per chapter)
    └── checkpoints/        (named snapshots per chapter)
```

---

## Data Models

### Project
```
id          UUID primary key
title       string
subtitle    string (optional)
author      string
genre       string (optional)
created_at  datetime
updated_at  datetime
word_count  int (computed)
```

### Chapter
```
id          UUID primary key
project_id  UUID foreign key
title       string
order_index int
content     text (file path reference)
word_count  int
created_at  datetime
updated_at  datetime
```

### Checkpoint (Version)
```
id          UUID primary key
chapter_id  UUID foreign key
name        string (user-named, e.g. "After first pass")
content     text
created_at  datetime
```

### Companion Documents (per project)
```
id          UUID primary key
project_id  UUID foreign key
type        enum: world_bible | style_guide | editorial_letter
content     text (JSON structure)
created_at  datetime
updated_at  datetime
```

### Character (world bible sub-item)
```
id          UUID primary key
companion_id UUID foreign key
name        string
description text
first_appearance chapter_ref (optional)
details     JSON (age, role, traits, etc.)
```

### Editorial Persona
```
id          UUID primary key
name        string (e.g. "Stephen King's Editor")
description text
system_prompt text
is_active   bool
```

---

## API Design

### Projects
```
GET    /api/projects                  — list all projects
POST   /api/projects                  — create project
GET    /api/projects/:id              — get project with chapter list
PATCH  /api/projects/:id              — update project metadata
DELETE /api/projects/:id              — delete project + chapters
GET    /api/projects/:id/word-count   — total word count
```

### Chapters
```
GET    /api/projects/:pid/chapters    — list chapters in project
POST   /api/projects/:pid/chapters    — create chapter
GET    /api/chapters/:id              — get chapter content
PATCH  /api/chapters/:id              — update chapter content
DELETE /api/chapters/:id              — delete chapter
PATCH  /api/chapters/:id/reorder      — reorder chapter (order_index)
```

### Checkpoints
```
GET    /api/chapters/:id/checkpoints   — list checkpoints
POST   /api/chapters/:id/checkpoints   — create named checkpoint
GET    /api/checkpoints/:id            — get checkpoint content
DELETE /api/checkpoints/:id            — delete checkpoint
POST   /api/chapters/:id/restore/:cpid — restore chapter from checkpoint
```

### Companions
```
GET    /api/projects/:pid/companions    — all companions for project
PUT    /api/projects/:pid/companions/:type  — upsert companion
GET    /api/companions/:id/characters  — list characters in world bible
POST   /api/companions/:id/characters  — add character
PATCH  /api/companions/:id/characters/:cid
DELETE /api/companions/:id/characters/:cid
```

### AI Editorial
```
POST   /api/ai/feedback                — get editorial feedback on passage
POST   /api/ai/copyedit               — copyedit pass
POST   /api/ai/format-check            — format check
POST   /api/ai/personas               — list available personas
POST   /api/ai/analyze-tone           — tone analysis
POST   /api/ai/revision-pass          — revision flags (repetition, passive, etc.)
POST   /api/ai/consistency-check      — cross-reference world bible
```

### AI Request Shape
```json
{
  "project_id": "uuid",
  "chapter_id": "uuid",
  "passage": "selected text or full chapter",
  "mode": "feedback|copyedit|format|revision|tone",
  "persona_id": "uuid (optional)"
}
```

### AI Response Shape
```json
{
  "annotations": [
    {
      "start": 0,
      "end": 45,
      "type": "repetition|passive|tone_shift|grammar|style",
      "message": "You're using 'slowly' again — consider removing or replacing",
      "suggestion": "She walked with purpose"
    }
  ],
  "summary": "Overall editorial note for this passage",
  "tokens_used": 1234,
  "model": "qwen3.5:35b"
}
```

---

## Editorial Personas

Each persona is a system prompt + editor rules. For personal use, define a set that covers the main editorial lenses:

| Persona | Editor Style |
|---------|-------------|
| **Stephen King's Editor** | Direct, blunt, no tolerance for lazy prose. Focus on tension, pacing, sensory detail. |
| **Literary Fiction Critic** | Parses subtext, symbolism, voice. Flags when prose tries too hard or too little. |
| **Classic Pulp Editor** | Tight sentences, action-first, dialogue that crackles. Hates purple prose. |
| **Non-Fiction Editor** | Clarity, structure, argument flow. Checks evidence, transitions, reader onboarding. |
| **Copy Editor (CMoS)** | Chicago Manual of Style rules. Commas, em-dashes, dialogue punctuation. |
| **Beta Reader** | Engaged amateur. Emotional reactions to characters and pacing. |
| **Self-Edit Pass** | Author's own voice. The ruthlessness needed for revision. |

---

## Key Feature: Full-Manuscript AI Context

The most important architectural decision. Before the AI can give meaningful feedback on chapter 5, it must have read chapters 1-4 and any relevant companion docs.

**Implementation:**
1. On every AI request, fetch the *full project content* (all chapters in order + companions)
2. Build a context window with: `[companions] [chapters-1-to-n-1] [current-chapter]`
3. Truncate from the front if context exceeds model's limit
4. Cache the context for 5 minutes to avoid re-building on every highlight

**Context budget (qwen3.5 35b — 32k context):**
- ~8,000 tokens for system prompt + persona definition
- ~24,000 tokens for manuscript content (~60 pages of prose)
- Companion docs (world bible, style guide, editorial letter) get priority

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Startup time** | < 3 seconds (local app) |
| **AI response time** | < 30s for full chapter analysis (local GPU/CPU) |
| **Storage** | All data local in `~/.raised-letters/` |
| **Privacy** | Zero data leaves the machine. Manuscripts never sent anywhere. |
| **Backup** | Manuscripts stored as plain `.txt` files — trivially backup-able |
| **Offline** | Full functionality without internet (Ollama runs locally) |

---

## What's Out of Scope (Reference App Features We Skip)

- **Multi-user / sharing** — personal use only
- **Stripe / payments** — free (local Ollama)
- **Encryption at rest** — optional, low priority for personal machine
- **Browser version** — desktop app only (Electron or Tauri)
- **Collaboration** — single author

---

## Decisions (2026-08-07)

| Decision | Choice |
|----------|--------|
| **Backend** | Python (FastAPI) |
| **Desktop Shell** | Tauri (Rust) |
| **AI Model** | One of the new Ollama models — TBD (see below) |
| **Scope** | Fully working — all features, no phased MVP |
| **Tone** | Fiction and non-fiction |

### Model Decision Pending

"One of the new models" — Amre to confirm from available Ollama models. Candidates:
- `llama3.3:70b` — established, reliable
- `qwen3:30b` — newer, thinking mode
- `huihui_ai/qwen3.5-abliterated:latest` — uncensored, local
- `deepseek-r1:70b` — strong reasoning

Amre's M4 Max (128GB) can handle 70b models at good quantizations.
