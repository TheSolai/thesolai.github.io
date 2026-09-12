# Vellum Rust

*A writer's editor with a Tab that makes your words better.*

![Vellum Rust](https://img.shields.io/badge/version-0.1.0-blue)

## What is it?

Vellum Rust is a distraction-free terminal writing app for macOS and Linux. The killer feature: **press Tab** and your current line gets rewritten by a local Ollama AI model — grammar fixed, prose sharpened, voice preserved. No alt-tabbing, no copy-pasting, no losing your flow.

## The Tab Autofix

When you're mid-sentence or finish a paragraph and it still sounds rough:

1. Keep typing — or put your cursor anywhere on the line
2. Press **Tab**
3. A "✦ Fixing…" overlay appears for 1-3 seconds
4. Your line is replaced with the AI-improved version
5. Keep writing

If Ollama is offline, Tab does nothing and the status bar shows "Ollama: offline" — no crash, no noise.

The default model is `qwen3:4b` — fast, cheap, and genuinely good at prose. Configure any Ollama model you like.

## Installation

### Prerequisites

- **Rust 1.94+** — [Install via rustup](https://rustup.rs)
- **Ollama** — [ollama.com](https://ollama.com), running locally at `http://localhost:11434`

### Build from source

```bash
git clone https://github.com/your-repo/vellum-rs.git
cd vellum-rs
cargo build --release
cargo install --path .
```

Or run directly without installing:

```bash
cargo run --release -- [options]
```

### Quick start

```bash
# New file
vellum-rs --new mynovel

# Open existing file
vellum-rs ~/Documents/mynovel.txt

# With custom Ollama model
vellum-rs --new mynovel --model llama3:8b

# Export without opening editor
vellum-rs mynovel.txt --export epub
```

## Configuration

Edit `~/.vellum-rs/config.toml`:

```toml
ollama_url = "http://localhost:11434"
model = "qwen3:4b"
autosave_seconds = 30
default_export = "epub"
```

All settings have defaults — the file is optional.

## Keybindings

| Key | Action |
|---|---|
| **Tab** | Fix current line via Ollama |
| **Ctrl+S** | Save |
| **Ctrl+E** | Export (fountain/epub/mobi) |
| **Ctrl+G** | Toggle word count |
| **Ctrl+Q** | Save and quit |
| **Esc** | Dismiss overlay/modal |
| **↑/↓ or j/k** | Navigate (scroll) |
| **Enter** | New line |
| **Backspace** | Delete |

## Export Formats

| Format | Extension | Description |
|---|---|---|
| Fountain | `.fountain` | Plain-text screenplay format, imports to Vellum |
| EPUB | `.epub` | Standard ebook format for Vellum and Kindle |
| MOBI | `.mobi` | Kindle format (converted via Calibre) |

Export with `Ctrl+E` in the editor, or from the command line:

```bash
vellum-rs mynovel.txt --export epub
vellum-rs mynovel.txt --export fountain
vellum-rs mynovel.txt --export mobi
```

## How the Tab Fix Works

1. Vellum captures the **current line** (the line the cursor is on)
2. Sends it to Ollama at `POST /api/generate` with a prose-editor prompt
3. Replaces the line with the response
4. The cursor stays in place — you're ready to keep writing

The prompt sent to Ollama:

```
You are a prose editor. The user will give you a paragraph of writing. 
Improve it: fix grammar, remove repetition, strengthen weak verbs, 
keep the writer's voice. Return ONLY the improved paragraph, no commentary.
Text:
[your text]
```

## Data & Privacy

All files are stored locally in `~/.vellum-rs/`. Autosave drafts go to `~/.vellum-rs/[filename].draft`. No data leaves your machine — Ollama runs locally.

## Requirements

- macOS (primary) or Linux
- Rust 1.94+
- Ollama running on localhost:11434
- A terminal with at least 80 columns × 24 rows

## License

MIT
