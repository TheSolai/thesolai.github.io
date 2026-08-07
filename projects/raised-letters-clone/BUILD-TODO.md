# Raised Letters Clone — Build TODO

**Project:** Raised Letters Personal Clone
**Status:** Phase 0 — Starting Build
**Stack:** Python/FastAPI (backend) + Tauri/Rust (desktop shell) + React/Vite (frontend) + Ollama (local AI)
**Decisions:** Python backend ✅ | Tauri desktop ✅ | Full feature scope ✅ | Model TBD (see README)
**Created:** 2026-08-07

---

## How to Read This Doc

Each phase must be **completed and working** before moving to the next. Within phases, items are ordered: foundational first, UI/UX last.

---

## Phase 0 — Project Foundation (Do First)

### 0.1 Scaffold
- [ ] Create project directory structure
  ```
  raised-letters-clone/
  ├── backend/
  │   ├── main.py
  │   ├── routers/
  │   │   ├── projects.py
  │   │   ├── chapters.py
  │   │   ├── checkpoints.py
  │   │   ├── companions.py
  │   │   └── ai.py
  │   ├── models/
  │   │   └── schemas.py
  │   ├── services/
  │   │   ├── ollama_service.py
  │   │   └── manuscript_context.py
  │   └── requirements.txt
  ├── frontend/
  │   ├── src/
  │   │   ├── components/
  │   │   ├── pages/
  │   │   ├── hooks/
  │   │   └── lib/
  │   └── package.json
  ├── data/              (runtime — created on first run)
  │   ├── raised-letters.db
  │   ├── manuscripts/
  │   └── checkpoints/
  └── scripts/
      └── init_db.py
  ```
- [ ] Write `requirements.txt` (fastapi, uvicorn, python-multipart, aiosqlite, httpx)
- [ ] Write `package.json` (react, react-dom, @tanstack/react-query, tiptap, axios, react-router-dom, zustand)
- [ ] Run `npm create vite@latest frontend -- --template react-ts`
- [ ] Verify backend starts: `uvicorn backend.main:app --reload --port 8000`
- [ ] Verify frontend dev server starts: `npm run dev` in frontend/

### 0.2 Database
- [ ] Write `scripts/init_db.py` — creates SQLite schema
  - Run it manually to create `data/raised-letters.db`
  - Document: schema must match `backend/models/schemas.py`
- [ ] Verify: query the DB with sqlite3 CLI — projects table returns empty, no errors

### 0.3 Ollama Connection
- [ ] Verify Ollama is running: `curl http://localhost:11434/api/tags`
- [ ] Verify model is available: `ollama list` — qwen3.5:35b should be there
- [ ] Write a minimal test: `POST /api/ai/ping` → returns `{"status": "ok", "model": "qwen3.5:35b"}`
- [ ] Stress test: send a 500-word passage, confirm response < 60s on CPU

---

## Phase 1 — Core Writing Environment

### 1.1 Project CRUD
- [ ] `POST /api/projects` — create project (title, author, genre)
- [ ] `GET /api/projects` — list all projects with word counts
- [ ] `GET /api/projects/:id` — get project + chapter list
- [ ] `PATCH /api/projects/:id` — rename, update metadata
- [ ] `DELETE /api/projects/:id` — cascade delete chapters, companions
- [ ] Frontend: Projects page — list view, "New Project" button, click to open
- [ ] Frontend: Delete confirmation modal
- [ ] Frontend: Project word count displayed in list

### 1.2 Chapter Editor
- [ ] `POST /api/projects/:pid/chapters` — create chapter (title, order)
- [ ] `GET /api/chapters/:id` — get chapter content
- [ ] `PATCH /api/chapters/:id` — save chapter content (auto-save trigger)
- [ ] `DELETE /api/chapters/:id` — delete chapter
- [ ] `PATCH /api/chapters/:id/reorder` — change order_index
- [ ] Frontend: Chapter list sidebar — drag-to-reorder (order_index update)
- [ ] Frontend: Rich text editor (TipTap) — bold, italic, headings, blockquote
- [ ] Frontend: Per-chapter word count (live, computed client-side)
- [ ] Frontend: Auto-save — debounce 2s after typing, save to backend
- [ ] Frontend: "Unsaved changes" indicator

### 1.3 Checkpoint / Version History
- [ ] `POST /api/chapters/:id/checkpoints` — named snapshot (user types name)
- [ ] `GET /api/chapters/:id/checkpoints` — list all checkpoints for chapter
- [ ] `GET /api/checkpoints/:id` — get checkpoint content
- [ ] `DELETE /api/checkpoints/:id`
- [ ] `POST /api/chapters/:id/restore/:cpid` — restore chapter from checkpoint
- [ ] Frontend: Checkpoints panel (slide-out or modal)
- [ ] Frontend: "Save Checkpoint" button — prompts for name
- [ ] Frontend: Checkpoint list — name + timestamp, click to preview, "Restore" button
- [ ] Frontend: Restore confirmation ("This will overwrite current content")

### 1.4 Navigation & Layout
- [ ] Three-panel layout: sidebar (projects/chapters) | main editor | companion panel (collapsible)
- [ ] Top bar: project title, total word count, save status
- [ ] Keyboard shortcut: `Cmd+S` — manual save + checkpoint prompt
- [ ] Frontend: Empty state — "Create your first project" on fresh load
- [ ] Frontend: Chapter tabs or scrollable list in sidebar

---

## Phase 2 — Companion Documents

### 2.1 World Bible
- [ ] `PUT /api/projects/:pid/companions/world_bible` — upsert (one per project)
- [ ] `GET /api/projects/:pid/companions` — list all companions
- [ ] `GET /api/companions/:id/characters` — list characters
- [ ] `POST /api/companions/:id/characters` — add character
- [ ] `PATCH /api/companions/:id/characters/:cid` — update character
- [ ] `DELETE /api/companions/:id/characters/:cid`
- [ ] Frontend: World Bible tab — character list + detail view
- [ ] Frontend: Character card: name, role, description, first appearance
- [ ] Frontend: Inline add/edit character — no modal, expandable card

### 2.2 Style Guide
- [ ] `PUT /api/projects/:pid/companions/style_guide`
- [ ] Frontend: Style Guide tab — toggle switches + text rules
  - Oxford comma: on/off
  - Dialogue tags: says / said / asked
  - POV: first person / third limited / third omniscient
  - Tense: past / present
  - Custom rules: freeform text list (add/remove)

### 2.3 Editorial Letter
- [ ] `PUT /api/projects/:pid/companions/editorial_letter`
- [ ] Frontend: Editorial Letter tab — textarea, project-level notes to AI
  - What to watch for in this manuscript
  - Themes to preserve
  - Known problem areas
  - Example: "This is a slow-burn. Don't flag pacing as an issue."

---

## Phase 3 — AI Editorial Engine

### 3.1 Ollama Bridge
- [ ] `backend/services/ollama_service.py` — single service, all LLM calls
  - `chat(model, messages, system_prompt)` → text response
  - `stream_chat(model, messages, system_prompt)` → generator
  - Timeout handling (120s for full chapter)
  - Error handling (model not found, context overflow, timeout)
- [ ] Health check endpoint: `GET /api/ai/status` — Ollama up?, model loaded?
- [ ] Test: send simple editorial prompt, receive response

### 3.2 Manuscript Context Builder
- [ ] `backend/services/manuscript_context.py`
  - `build_context(project_id, focus_chapter_id)` → full manuscript text + companions
  - Context format: `[World Bible]\n{content}\n\n[Style Guide]\n{content}\n\n[Editorial Letter]\n{content}\n\n[Manuscript — Chapters in order]\n`
  - Truncation: if total > 28k tokens, truncate from earliest chapters first
  - Cache: memoize for 5 minutes (project_id + focus_chapter_id key)
- [ ] Unit test: build_context for project with 10 chapters, verify truncation logic

### 3.3 Editorial Personas
- [ ] Pre-seed 5 personas in SQLite (seed data):
  1. **Blunt Editor** — Direct, no-nonsense. "Cut the filler."
  2. **Literary Lens** — Subtext, symbolism, voice. "What's underneath?"
  3. **Pulp Coach** — Tight prose, action-first. "Trim 20% of every sentence."
  4. **Beta Reader** — Emotional, character-focused. "I didn't buy their motivation."
  5. **Self-Revision** — Ruthless personal voice. "You wrote this. Is this what you meant?"
- [ ] `GET /api/ai/personas` — list personas
- [ ] `GET /api/ai/personas/:id` — get persona details
- [ ] Frontend: Persona selector — dropdown in AI panel, shows name + one-line description
- [ ] Persona prompt injected as system message in all AI calls

### 3.4 Feedback Mode
- [ ] `POST /api/ai/feedback`
  - Build full context (manuscript + companions + persona)
  - System prompt: "You are [persona name]. You read the full manuscript. Now give editorial feedback on the selected passage. Be specific. Quote the prose you're responding to. Never rewrite."
  - User prompt: "Passage: [{selected_text}]\n\nWhat does this passage do well? What does it not do? What should be changed?"
  - Return: `{ summary: string, annotations: Annotation[] }`
- [ ] Frontend: Select text in editor → "Get Feedback" button appears
- [ ] Frontend: Feedback panel slides in (right side) — shows response, annotations highlighted inline
- [ ] Frontend: Loading state: "Reading your manuscript..." while context builds

### 3.5 Copyedit Mode
- [ ] `POST /api/ai/copyedit`
  - Mode: mark grammar, punctuation, style violations
  - System prompt: "Mark every issue. Format: `[issue]: original → suggested`"
  - Returns: `{ fixes: CopyeditFix[] }`
- [ ] Frontend: "Copyedit" button → highlights inline, click annotation to see fix suggestion
- [ ] "Accept" / "Reject" per annotation (client-side only)

### 3.6 Format Check Mode
- [ ] `POST /api/ai/format-check`
  - Standard manuscript format checks: double-spaced, 12pt, 1" margins, chapter headings centered, etc.
- [ ] Frontend: "Format Check" → list of violations

### 3.7 Revision Pass Mode
- [ ] `POST /api/ai/revision-pass`
  - Flags: repetitive words (within 500 words), passive voice, adverbs, telling vs showing
  - System prompt: "Find every instance of: [word], passive voice, -ly adverbs, telling prose"
  - Returns: `{ flags: RevisionFlag[] }`
- [ ] Frontend: Revision pass runs on full chapter on demand

### 3.8 AI Panel UI
- [ ] Right-side panel (collapsible) — always visible when open
- [ ] Top: persona selector dropdown
- [ ] Middle: mode tabs (Feedback | Copyedit | Format | Revision)
- [ ] Bottom: response area (scrollable)
- [ ] Response stream: render tokens as they arrive (streaming)

---

## Phase 4 — Polish & Personal Touch

### 4.1 Dark Theme
- [ ] CSS variables: `--bg-primary`, `--bg-secondary`, `--text-primary`, `--text-muted`, `--accent`
- [ ] Warm off-white (`#f5f0e8`) for writing canvas (like real paper)
- [ ] Dark sidebar (`#1a1a1a`) — easy on eyes for navigation
- [ ] Accent: deep red or amber (writerly feel)

### 4.2 Typography
- [ ] Editor font: `EB Garamond` or `Crimson Pro` — beautiful serif for prose
- [ ] UI font: `Inter` or `Source Sans 3` — clean sans-serif for chrome
- [ ] Font sizes: editor body 18px, UI 14px, headings scaled

### 4.3 Word Count Dashboard
- [ ] Per-chapter word count (live)
- [ ] Total project word count
- [ ] Session word count (words written this session — start on open, end on close)
- [ ] Frontend: bottom bar — `Chapter: 3,241 words | Project: 47,892 words | Session: 1,203`

### 4.4 Daily Writing Log
- [ ] Backend: `GET /api/projects/:id/word-count-history` — { date, words_written_today }
- [ ] Frontend: mini graph — last 7 days of writing (bar chart, CSS or simple canvas)

### 4.5 Keyboard Shortcuts
- [ ] `Cmd+B` — bold
- [ ] `Cmd+I` — italic
- [ ] `Cmd+S` — save + checkpoint prompt
- [ ] `Cmd+Shift+F` — open feedback on selection
- [ ] `Cmd+P` — persona selector

### 4.6 Import / Export
- [ ] Import: `.txt` file per chapter — drag-drop into chapter list
- [ ] Export project: `.zip` of all `.txt` files (one per chapter) + companions as `.json`

---

## Phase 5 — Harden & Deploy

### 5.1 Error Handling
- [ ] Ollama down: graceful error in UI — "AI unavailable. Install or start Ollama."
- [ ] Model not loaded: auto-pull prompt in UI
- [ ] Network timeout: retry with exponential backoff, max 2 retries
- [ ] DB write failure: save to `data/pending_writes.json`, retry on restart

### 5.2 Performance
- [ ] Auto-save debounce: 2s
- [ ] AI context build: cache 5 min, invalidate on chapter save
- [ ] Large manuscript (100k+ words): paginate context build, process in chunks
- [ ] Editor: virtualize chapter list if > 50 chapters

### 5.3 Persistence
- [ ] `data/` directory: created automatically on first run if missing
- [ ] DB path configurable via env var `RAISED_LETTERS_DB`
- [ ] Manuscripts dir: `data/manuscripts/{project_id}/{chapter_id}.txt`
- [ ] Checkpoints dir: `data/checkpoints/{chapter_id}/{checkpoint_id}.txt`

### 5.4 Local Install
- [ ] Write `setup.sh` — install deps, init DB, pull Ollama model
- [ ] Write `run.sh` — start backend + frontend together
- [ ] Test on clean macOS install (or VM)

---

## Priority Order for Amre

Given the scope above, here's a suggested build order:

```
Week 1 — Phase 0 + 1.1 + 1.2
  → Can create projects, write chapters, auto-save works

Week 2 — Phase 1.3 + 1.4
  → Checkpoints work, full layout functional

Week 3 — Phase 2 (Companions)
  → World Bible + Style Guide + Editorial Letter

Week 4 — Phase 3 (AI)
  → Ollama bridge working, Feedback mode live

Week 5 — Phase 3 (modes) + 4 (Polish)
  → All AI modes, dark theme, word counts
```

---

## Blocker Questions

The following must be answered before building Phase 3:

1. **Model:** `qwen3.5:35b` or a smaller/faster quant? (Amre to decide)
2. **Platform:** Tauri (Rust) or Electron? (Amre to decide)
3. **AI scope for MVP:** Feedback mode only, or copyedit + revision too?
4. **Companions:** All three from day one, or just World Bible first?
