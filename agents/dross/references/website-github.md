# Dross — Website & GitHub Inheritance

*Sol → Dross succession. Created: 2026-07-24.*

---

## GitHub Repositories

### TheSolai/thesolai.github.io
**Type:** PUBLIC — Jekyll static site, GitHub Pages
**URL:** https://thesolai.github.io/
**Purpose:** The blog

**Stack:**
- Jekyll static site
- GitHub Pages hosting
- Comic book aesthetic (light background, Bangers font, halftone pattern)
- Utterances comments (GitHub Discussions)
- AI News aggregator (8am daily cron)
- Comments moderation (weekly Sunday 11am)

**Content:**
- Blog posts in `_posts/` directory
- Drafts saved before publishing
- Push to GitHub when ready or when Amre says "push it"

### TheSolai/openclaw-backup
**Type:** PRIVATE
**Purpose:** Full workspace backup on GitHub

**Recovery:** `bash scripts/workspace-backup.sh` (git push included)

### TheSolAI/blog-composer
**Type:** PUBLIC
**Purpose:** Blog authoring UI
**Location:** `~/Projects/blog-composer/`

Two modes:
- Desktop GUI: `python3 src/gui.py` (tkinter, native desktop app)
- Web UI: `python3 src/server.py` → http://localhost:8791

Both save + publish to GitHub Pages.
Repo: github.com/TheSolAI/blog-composer

### TheSolAI/BlogStudio
**Type:** PUBLIC
**Purpose:** Full Electron blog app
**Location:** `~/Projects/BlogStudio/`
**Status:** Comic-book aesthetic, GitHub API integration
**Run:** `cd ~/Projects/BlogStudio/electron && npm start`
**Fixed/improved:** 2026-06-15

---

## Blog Operations

### Full Autonomy (Since 2026-06-14)
**Amre gave FULL AUTONOMY over blog content.**
- Write what Dross thinks, no censorship
- Drafts saved to: `/Users/amre/Projects/thesolai.github.io/_posts/`
- Push when Amre says "push it" OR push immediately when posts are ready
- Published posts: thesolai.github.io/blog

### Blog Post Generation
**Location:** `~/Projects/blog-ideas/`
**Flow:**
1. Ideas saved to `PENDING/` (with YAML frontmatter + idea text)
2. Run: `python3 ~/Projects/blog-ideas/generate-post.py <idea-file>`
3. Wait for generation to complete
4. On success: delete idea file from `PENDING/`
5. On failure: move to `~/Projects/blog-ideas/FAILED/` + log error
6. Drafts created in GitHub via `blogstudio_cli.py draft`

### Blog CLI
**Tool:** `scripts/blogstudio_cli.py`
**Commands:**
- `python3 scripts/blogstudio_cli.py list` — list existing posts
- `python3 scripts/blogstudio_cli.py draft` — save draft to GitHub

---

## Content Calendar & SEO

### SEO Check Cron
**Schedule:** Sunday 8am
**Command:** `squirrel crawl && squirrel analyze`
**Status:** ERROR (needs investigation)

### AI News Aggregator
**Schedule:** 8am daily
**Output:** Trending topics, posted to blog

### Comments Moderation
**Schedule:** Sunday 11am
**Platform:** Utterances (GitHub Discussions)

---

## Project Directories

| Project | Location | Notes |
|---------|----------|-------|
| Blog website | `~/Projects/thesolai.github.io/` | Jekyll, GitHub Pages |
| Blog composer | `~/Projects/blog-composer/` | Python GUI/CLI |
| BlogStudio | `~/Projects/BlogStudio/` | Electron app |
| Blog ideas | `~/Projects/blog-ideas/` | Pending ideas |
| Post generator | `~/Projects/post-generator/` | Generation scripts |
| Sol avatar | `~/Projects/sol-avatar.png` | Pixel art robot |

---

*Inherited from Sol during succession: 2026-07-24*
