# Vellum Rust — Spec

**App Name:** Vellum Rust  
**Tagline:** A writer's editor with a Tab that makes your words better.  
**Type:** Rust TUI (terminal UI)  
**Price:** $29 one-time  
**Stack:** Rust + ratatui TUI + reqwest (Ollama API)  
**Build time:** 4-5 hours  
**Status:** v1 spec  

---

## The One-Line Pitch

A distraction-free terminal writing app where **Tab autofixes your prose** using a local Ollama model — then export to Vellum, publish to Kindle.

---

## Problem

You're a writer. You open a blank page and the words come out rough — sentences that trail off, paragraphs that repeat themselves, prose that sounds like you wrote it at 2am (because you did). You could switch to an AI tool, but that means alt-tabbing, pasting, copying back, losing your flow.

What you want: keep typing, hit Tab when you're stuck, watch your sentence become a real sentence.

---

## The Tab Autofix — Core Feature

In the editor, pressing **Tab** at the end of any line or paragraph sends that text to Ollama and replaces it with the improved version. That's it. That's the feature.

**How it works:**
1. User finishes a sentence/paragraph
2. Presses Tab (not Enter — Tab is the signal)
3. Current line (or current paragraph if cursor is mid-block) is sent to Ollama
4. A subtle overlay shows "✦ Fixing…" for 1-3 seconds
5. Original text is replaced with improved text
6. Cursor stays at end of new text, ready to continue

**Ollama model:** configurable, default `qwen3:4b` (fast, cheap, good at prose). User can set `OLLAMA_MODEL` env or pass `--model` flag.

**Prompt sent to Ollama:**
```
You are a prose editor. The user will give you a paragraph of writing. 
Improve it: fix grammar, remove repetition, strengthen weak verbs, 
keep the writer's voice. Return ONLY the improved paragraph, no commentary.
Text:
[Pasted text]
```

**Safety:** If Ollama is unavailable, Tab does nothing and status bar shows "Ollama offline". No crash, no error noise.

---

## Editor Features (v1 — ruthless scope)

| Feature | Detail |
|---|---|
| **Writing area** | Full-screen text area, scrollable, line numbers optional |
| **Tab autofix** | Described above |
| **Word count** | Live word count in status bar |
| **Autosave** | Saves to ~/.vellum-rs/[filename].draft every 30 seconds |
| **Open file** | `vellum-rs mybook.txt` opens existing file |
| **New file** | `vellum-rs --new mybook` creates ~/.vellum-rs/mybook.txt |
| **Status bar** | Bottom bar: word count, Ollama status (connected/offline), filename |

---

## Export (Phase 1 — Vellum-ready formats)

**Fountain export** (`--export fountain`):  
Fountain is a plain-text screenplay/formatting syntax that Vellum imports natively. The app writes a `.fountain` file.

**Basic EPUB export** (`--export epub`):  
Generates a valid EPUB from the manuscript — title page, chapters (separated by `# Chapter Name` or blank-line doucments), body text. EPUB is what Vellum and Kindle both accept.

**MOBI export** (`--export mobi`):  
Uses `kindlegen` or `epubcheck` + `EPUB→MOBI` conversion. If tools aren't installed, outputs a clear error telling user what to install.

---

## Kindle Direct Publishing (Phase 2 — stretch goal)

**Not in v1.** The app exports to formats Vellum accepts. Vellum handles Kindle publishing.  
v2 may add: direct KDP upload via Amazon API (requires auth token).

---

## Keybindings

| Key | Action |
|---|---|
| `Tab` | Autofix current line/paragraph via Ollama |
| `Ctrl+S` | Manual save |
| `Ctrl+E` | Export (prompts for format: fountain/epub/mobi) |
| `Ctrl+Q` | Quit (with save) |
| `Ctrl+G` | Toggle word count display |
| `↑/↓ or j/k` | Navigate (vim-style) |
| `Esc` | Clear autofix overlay |

---

## Configuration

**File:** `~/.vellum-rs/config.toml`

```toml
ollama_url = "http://localhost:11434"
model = "qwen3:4b"
autosave_seconds = 30
default_export = "epub"
```

**Defaults if no config:** Ollama at localhost:11434, model qwen3:4b, 30s autosave.

---

## Technical Architecture

```
vellum-rs/
├── Cargo.toml
├── src/
│   ├── main.rs          — CLI args, startup
│   ├── editor.rs        — TUI editor with ratatui
│   ├── ollama.rs        — Ollama API calls
│   ├── autofix.rs       — Tab handling, text extraction, replacement
│   ├── export.rs        — Fountain/EPUB/MOBI export
│   └── config.rs        — config.toml loading
└── README.md
```

**Dependencies:**
- `ratatui` — TUI framework
- `reqwest` — HTTP client for Ollama
- `tokio` — async runtime
- `serde` / `toml` — config
- `zip` — EPUB creation
- `clap` — CLI argument parsing
- `rusxml` or string templates — EPUB XML generation

---

## Quality bar

- [ ] App opens in < 1 second on M4 Max
- [ ] Tab autofix returns in < 3 seconds on local Ollama
- [ ] No crash if Ollama is offline — graceful degradation
- [ ] Exports produce valid EPUB (passes epubcheck)
- [ ] Word count is accurate to ±1 word
- [ ] Builds on macOS (primary) and Linux

---

## DrossCash Integration

This replaces the stuck DrossCash pipeline for this cycle.  
Brief to be filed: `briefbank/READY/011-vellum-rs.md`  
Product slug: `vellum-rs`  
Stack: `rust`  
Price: `$29`  
Build time: `4-5h`  
Status: `building`

---

*Built by Dross on the M4 Max. The Mac finally does real work.*
