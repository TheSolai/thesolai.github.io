# Raised Letters Clone — Frontend Specification

**Project:** Raised Letters Personal Clone
**Scope:** React + TypeScript + TipTap + Vite
**Created:** 2026-08-07

---

## App Shell

### Layout (Three-Panel)

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOPBAR: [Project Title]           [Word Count]  [Save ●]  [⚙️]   │
├──────────────┬──────────────────────────────────┬────────────────────┤
│              │                                  │                    │
│  SIDEBAR    │         EDITOR CANVAS            │    AI PANEL        │
│  (240px)    │         (flex: 1)                │    (360px)         │
│              │                                  │    (collapsible)   │
│  Projects    │  Chapter title (editable)        │                    │
│  > Chapters  │  ─────────────────────────       │  [Persona ▾]       │
│    Ch 1  ✓  │                                  │  ────────────      │
│    Ch 2     │  [Rich text editor — TipTap]     │  [Feedback]        │
│    Ch 3     │                                  │  [Copyedit]        │
│              │  Body text in EB Garamond 18px   │  [Format]          │
│  ──────────  │  Warm off-white background       │  [Revision]        │
│  Companions  │  #f5f0e8                        │                    │
│  > World     │                                  │  ────────────      │
│  > Style     │                                  │                    │
│  > Editorial │                                  │  Response area     │
│              │                                  │  (scrollable)      │
│  ──────────  │                                  │                    │
│  Checkpoints │                                  │                    │
│  > snapshot  │                                  │                    │
│              │                                  │                    │
├──────────────┴──────────────────────────────────┴────────────────────┤
│  STATUSBAR: Ch 2: 3,241 words | Project: 47,892 | Session: 1,203  │
└─────────────────────────────────────────────────────────────────────┘
```

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-app` | `#0f0e0d` | App background (dark charcoal) |
| `--bg-sidebar` | `#1a1816` | Sidebar background |
| `--bg-editor` | `#f5f0e8` | Writing canvas (warm off-white) |
| `--bg-panel` | `#1f1d1b` | AI panel background |
| `--text-primary` | `#e8e4df` | Main UI text |
| `--text-muted` | `#7a7470` | Secondary text, labels |
| `--text-editor` | `#1a1816` | Text in editor (dark on warm paper) |
| `--accent` | `#c47b5a` | Terracotta — buttons, highlights |
| `--accent-hover` | `#d4916d` | Hover state |
| `--border` | `#2e2b28` | Dividers, borders |
| `--success` | `#6b9b7a` | Save confirmed, success states |
| `--warning` | `#c9a84c` | Warnings |
| `--danger` | `#b85c5c` | Delete, errors |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| App UI | Source Sans 3 | 14px | 400/600 |
| Sidebar labels | Source Sans 3 | 12px | 600 uppercase |
| Chapter title | Crimson Pro | 28px | 600 |
| Editor body | Crimson Pro | 18px | 400, line-height 1.8 |
| Statusbar | Source Sans 3 | 12px | 400 |
| AI response | Source Sans 3 | 14px | 400 |

---

## Page: Home / Project List

### What It Shows
- Header: "Raised Letters" (logo text) + tagline "A writing environment for authors"
- Grid of project cards (2-3 columns)
- Empty state if no projects: "Start your first manuscript" + large CTA button

### Project Card
```
┌─────────────────────────────────────┐
│  [Genre tag]                        │
│  PROJECT TITLE                       │
│  by Author Name                      │
│                                     │
│  12 chapters · 47,892 words         │
│  Last edited: 3 days ago            │
│                                     │
│  [Continue Writing →]               │
└─────────────────────────────────────┘
```
- Click anywhere → opens project
- Hover: subtle lift shadow + border accent glow
- Genre tag: small pill, top-left corner

### "New Project" Modal
Fields:
- **Title** (required) — placeholder: "Untitled Manuscript"
- **Author** (optional) — pre-filled from last project or empty
- **Genre** (optional dropdown) — Literary Fiction, Thriller, Sci-Fi, Non-Fiction, Fantasy, Horror, Romance, Other
- **Subtitle** (optional)

Buttons: Cancel | Create Project

---

## Page: Project View (Editor)

### Top Bar
- Left: Back arrow (←) → home
- Center: Project title (click to edit inline)
- Right: Word count chip + save indicator (● = saved, ◐ = saving, ✗ = error)

### Sidebar Sections

#### Section: Chapters
- List of chapters, ordered by `order_index`
- Each item: chapter title + word count
- Active chapter: accent left border + slightly brighter background
- Click → switch chapter (editor loads new content)
- Drag handle on left for reordering
- Right-click / hover menu: Rename, Delete, Save Checkpoint
- Bottom: "+ Add Chapter" button

#### Section: Companions
- Accordion items: World Bible, Style Guide, Editorial Letter
- Badge on each showing: number of entries (e.g. World Bible: 4 characters)
- Click expands inline below accordion header
- No separate page — inline in sidebar

#### Section: Checkpoints
- Collapsible, shows last 5 checkpoints for current chapter
- "View all" → opens full checkpoint modal
- Each: name + relative time ("2 hours ago")

### Editor Canvas

#### Chapter Header
- Editable chapter title (contenteditable, Crimson Pro 28px)
- Click to focus, blur to save

#### Writing Area
- TipTap editor instance
- Toolbar (minimal, appears on text selection):
  - Bold (`Cmd+B`)
  - Italic (`Cmd+I`)
  - Blockquote (for scene breaks: `>`)
  - Horizontal rule (--- for chapter breaks)
- No visible toolbar on empty state
- Toolbar floats near selection, auto-dismisses

#### Auto-Save
- Debounce: 2000ms after last keystroke
- Status: top-right corner
  - `●` (grey) = saved
  - `◐` (amber) = saving
  - `✗` (red) = error — hover shows error message
- On error: banner above status bar with retry button

#### Text Selection → AI Context Menu
When user selects text (min 10 chars):
```
┌──────────────────────┐
│ 🔍 Get Feedback      │
│ ✏️ Copyedit          │
│ 📋 Format Check      │
│ 🔄 Revision Pass     │
└──────────────────────┘
```
- Appears near selection (smart positioning — always in viewport)
- Each option activates that AI mode with selected text

---

## AI Panel (Right Side, 360px)

### Header
- Persona selector: dropdown with search
  - Each option: persona name + one-line description
  - Selected persona: accent color highlight
- Toggle button: `[AI ✗]` / `[AI ◐]` — click to collapse/expand panel

### Mode Tabs
Four tabs, styled as underline tabs:
`Feedback | Copyedit | Format | Revision`

Active tab: accent underline + bright text
Inactive: muted text

### Response Area
- Scrollable, takes remaining height
- When empty (no request yet): centered placeholder text
  - "Select text in your manuscript and choose a mode to begin."
- When loading: 
  - Step indicator: "📖 Reading manuscript..." → "✍️ Analyzing..." → "💬 Preparing feedback..."
- When complete: response text + annotation list
- Streaming: tokens render as they arrive (逐字显示)

### Annotation Style
```
┌────────────────────────────────────────────┐
│ 📍 [Repetition] Ch 3, para 2              │
│                                            │
│ "She walked slowly toward the door"        │
│                                            │
│ You're using 'slowly' again (3rd time).   │
│ Consider cutting or replacing:              │
│ → "She walked toward the door"             │
│                                            │
│ [Accept] [Dismiss]                         │
└────────────────────────────────────────────┘
```
- Annotation cards, stacked vertically
- Source passage quoted in italic
- Accept/Dismiss: client-side only (no backend call)
- Accepted annotations: muted, collapsed

---

## Companion Panel — World Bible

Expanded inline in sidebar (below accordion header):

### Character Cards
```
┌────────────────────────────────────────┐
│ ALICE HOLLOWAY                      ⋮  │
│ Protagonist · Ch 1                    │
│ ────────────────────────────────────── │
│ Age 34. Investigative journalist.       │
│ Prone to self-destruction when truth   │
│ conflicts with loyalty.                │
└────────────────────────────────────────┘
```
- Collapsed by default (shows name + role)
- Click → expands to show full description
- `⋮` menu: Edit, Delete
- Bottom: "+ Add Character" button

### Add/Edit Character (slide-over panel)
Fields:
- **Name** (required)
- **Role** (optional): Protagonist, Antagonist, Supporting, Minor
- **First Appearance** (optional): chapter reference
- **Description** (textarea): full character description

---

## Companion Panel — Style Guide

Expanded inline in sidebar:

### Rule Toggles
| Rule | Toggle |
|------|--------|
| Oxford comma | ⚪ / 🔘 |
| Em-dashes (—) vs hyphens (-) | ⚪ / 🔘 |
| Dialogue tag style | `says` / `said` / varies |
| POV | 1st / 3rd limited / 3rd omni |
| Tense | Past / Present |

### Custom Rules
- List of text rules, user can add/remove
- Each: freeform text input
- "+ Add Rule" button at bottom

---

## Companion Panel — Editorial Letter

Expanded inline in sidebar:
- Large textarea
- Placeholder: "What should the AI know about this project? Themes to preserve, known problem areas, what you're trying to achieve..."
- Auto-saves on blur (debounced 2s)
- Character count bottom-right

---

## Checkpoint Modal

Triggered by: "Save Checkpoint" button or right-click chapter → Save Checkpoint

```
┌─────────────────────────────────────────┐
│ Save Checkpoint                      ✗  │
│ ─────────────────────────────────────── │
│                                         │
│  Snapshot name:                          │
│  ┌─────────────────────────────────┐   │
│  │ After first edit pass            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Chapter: Chapter 3 — The Door         │
│  Will save current content as:           │
│  "After first edit pass"                │
│                                         │
│              [Cancel]  [Save Snapshot]   │
└─────────────────────────────────────────┘
```

Full checkpoint list view (separate modal):
- Table: Name | Chapter | Saved | Actions
- Actions: Preview (read-only), Restore, Delete
- Restore requires confirmation

---

## Status Bar (Bottom)

```
 Ch 3: 3,241 words  ·  Project: 47,892  ·  Session: 1,203  ·  ● Saved
```
- Fixed to bottom of editor panel
- Monospace font, 12px
- Save indicator pulses amber during save

---

## Modals

### New Chapter
```
┌─────────────────────────────────┐
│ New Chapter                 ✗  │
│ ─────────────────────────────── │
│  Chapter title:                │
│  ┌─────────────────────────┐   │
│  │ Chapter 4               │   │
│  └─────────────────────────┘   │
│                                 │
│    [Cancel]  [Create Chapter]  │
└─────────────────────────────────┘
```

### Delete Confirmation
```
┌─────────────────────────────────┐
│ Delete Chapter?             ✗  │
│ ─────────────────────────────── │
│  "Chapter 4 — The Door" will  │
│  be permanently deleted.        │
│  This cannot be undone.        │
│                                 │
│  [Cancel]  [Delete Chapter ⚠️] │
└─────────────────────────────────┘
```

### Project Settings (gear menu)
- Edit project title, author, genre
- Delete project (requires typing project name to confirm)
- Export project (.zip)

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+S` | Save chapter + prompt for checkpoint name |
| `Cmd+B` | Bold (selection) |
| `Cmd+I` | Italic (selection) |
| `Cmd+Shift+F` | Open feedback on current selection |
| `Cmd+Shift+C` | Open copyedit on current selection |
| `Cmd+P` | Open persona selector |
| `Cmd+\`` | Toggle AI panel |
| `Cmd+[` | Previous chapter |
| `Cmd+]` | Next chapter |
| `Esc` | Close any open modal/panel |

---

## Empty States

| View | Empty State |
|------|-------------|
| No projects | "Your manuscripts will appear here." + "Start Writing" button |
| No chapters | "This project has no chapters yet." + "Add First Chapter" button |
| No checkpoint | "No snapshots yet." + "Save your first checkpoint" |
| No characters | "No characters yet." + "Add Character" button |
| AI panel idle | "Select text in your manuscript and choose a mode." |

---

## Error States

| Situation | Behavior |
|-----------|----------|
| Ollama not running | Banner: "AI unavailable — is Ollama started?" + link to troubleshoot |
| Model not loaded | Inline: "Model loading... (this may take a minute)" |
| Save failed | Top-right indicator turns red ✗, hover: "Save failed — retry" |
| Chapter load failed | Toast notification + retry button |
| Network error | Toast: "Connection lost. Retrying..." |

---

## Toast Notifications

Bottom-right corner, stacked:
- Success (green left border): "Chapter saved"
- Error (red left border): "Save failed — retry"
- Info (grey left border): "Checkpoint created"
- Auto-dismiss: 4 seconds
- Manual dismiss: ✗ button

---

## Routing

```
/                         → ProjectListPage
/project/:id              → ProjectPage (editor)
/project/:id/settings     → ProjectSettingsPage
```

React Router v6. Navigation triggers on:
- Sidebar project click → `/project/:id`
- Topbar back arrow → `/`
- Settings gear → `/project/:id/settings`

---

## State Management (Zustand)

```
appStore:
  - currentProjectId: string | null
  - currentChapterId: string | null
  - aiPanelOpen: boolean
  - sidebarSection: 'chapters' | 'companions' | 'checkpoints'
  - toasts: Toast[]

editorStore:
  - content: string (TipTap JSON or HTML)
  - isDirty: boolean
  - isSaving: boolean
  - lastSaved: Date | null
  - wordCount: number

aiStore:
  - selectedPersonaId: string
  - activeMode: 'feedback' | 'copyedit' | 'format' | 'revision'
  - isLoading: boolean
  - response: string
  - annotations: Annotation[]
```

---

## Component Inventory

| Component | States |
|-----------|--------|
| `ProjectCard` | default, hover, loading |
| `ChapterListItem` | default, active, dragging, hover |
| `EditorCanvas` | empty, writing, selecting, loading |
| `SelectionContextMenu` | hidden, visible (positioned) |
| `AIPanel` | collapsed, expanded, loading, idle |
| `PersonaSelector` | closed, open, searching |
| `ModeTab` | active, inactive |
| `AnnotationCard` | default, accepted, dismissed |
| `CompanionSection` | collapsed, expanded |
| `CharacterCard` | collapsed, expanded, editing |
| `CheckpointModal` | create, list, confirm-delete |
| `Toast` | success, error, info |
| `SaveIndicator` | saved, saving, error |
| `WordCountBar` | static |
| `ConfirmDialog` | default (delete project/chapter) |
