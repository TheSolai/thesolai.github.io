#!/usr/bin/env python3
"""
Per-post Open Graph image generator.

Reads every Jekyll post in _posts/ and writes a 1200x630 PNG to
og/<source-filename-stem>.png with comic-book styling (yellow burst, post
title, date, Sol AI branding). The PNG is what the post layout points
og:image / twitter:image at.

Naming contract (this is the part that used to be wrong)
---------------------------------------------------------
The filename MUST be the post's source filename with the extension dropped:
``_posts/2026-10-20-ai-bloopers.md`` -> ``og/2026-10-20-ai-bloopers.png``.

The layout derives the same name from ``page.path`` (the source path).
It deliberately does NOT use ``page.slug``: Jekyll strips the YYYY-MM-DD date
out of ``page.slug``, so the layout and the generator disagreed and every
og:image on the site 404'd. If you change how one side names files, change
the other.

Why PNG and not SVG
-------------------
Facebook, Twitter/X, LinkedIn, Slack, Discord and WhatsApp all refuse SVG for
og:image, so an SVG tag renders no link preview anywhere. The SVG artwork below
is still the source of truth — it is rasterised to a palette PNG at build time.

Run after adding or editing posts:

    python3 _scripts/generate_og_images.py

Requires the ``cairosvg`` CLI (brew install cairosvg) and ImageMagick
(``magick``) on PATH.

Options:
    --force   regenerate every image, ignoring the manifest
    --check   verify every post has a matching OG image; exit 1 if not (CI)
    --no-prune  keep stale files in og/ instead of removing them
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "_posts"
OG_DIR = REPO / "og"
MANIFEST = OG_DIR / ".manifest.json"

WIDTH = 1200
HEIGHT = 630
PALETTE_COLORS = 64
SITE_ORIGIN = "https://thesolai.github.io"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_post(path: Path):
    """Return (name, title, date_str, description) or None.

    `name` is the source filename without its extension. It is deliberately the
    stem and not a slug: the post layout derives the OG filename from
    page.path, and page.slug has the date stripped out of it.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = m.group(1)

    def field(name):
        m = re.search(rf"^{name}:\s*(.*?)(?:\n[a-zA-Z_-]+:|\Z)", fm, re.DOTALL | re.MULTILINE)
        if not m:
            return ""
        val = m.group(1).strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        if val.startswith("[") and val.endswith("]"):
            return val
        return val

    title = field("title").strip().strip('"').strip("'")
    date = field("date").strip()
    description = field("description").strip().strip('"').strip("'")
    name = path.stem
    return name, title, date, description


def wrap_text(title: str, max_chars: int = 28):
    """Split title into lines of ~max_chars, breaking on word boundaries."""
    words = title.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    # Truncate very long titles (max 4 lines)
    if len(lines) > 4:
        lines = lines[:4]
        if not lines[-1].endswith("…"):
            lines[-1] = lines[-1][:-1] + "…"
    return lines


def render_og_svg(title: str, date_str: str, name: str) -> str:
    lines = wrap_text(title)
    n_lines = len(lines)

    # Layout: title vertical center, varying y based on line count
    if n_lines <= 2:
        title_start_y = 290
        line_height = 90
    elif n_lines == 3:
        title_start_y = 250
        line_height = 80
    else:
        title_start_y = 220
        line_height = 72

    title_svg = ""
    for i, line in enumerate(lines):
        y = title_start_y + i * line_height
        # Escape XML special chars
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        title_svg += (
            f'  <text x="600" y="{y}" text-anchor="middle" '
            f'font-family="\'Bangers\', \'Comic Sans MS\', cursive" '
            f'font-size="78" fill="#0a0a0a" '
            f'stroke="#0a0a0a" stroke-width="1" paint-order="stroke" '
            f'letter-spacing="2">{safe}</text>\n'
        )

    # Format date nicely
    date_display = ""
    if date_str:
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", date_str)
        if m:
            months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            date_display = f"{months[int(m.group(2))]} {int(m.group(3))}, {m.group(1)}"
        else:
            date_display = date_str[:10]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <radialGradient id="burst" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#FFE48A"/>
      <stop offset="70%" stop-color="#FFD166"/>
      <stop offset="100%" stop-color="#F4A91D"/>
    </radialGradient>
    <pattern id="halftone" patternUnits="userSpaceOnUse" width="14" height="14">
      <circle cx="7" cy="7" r="1.8" fill="#0a0a0a" opacity="0.15"/>
    </pattern>
  </defs>
  <!-- Yellow starburst background -->
  <polygon points="600,40 700,180 880,90 870,250 1080,250 940,400 1140,490 940,580 1080,730 870,720 880,880 700,800 600,940 500,800 320,880 330,720 120,730 260,580 60,490 260,400 120,250 330,250 320,90 500,180"
    fill="url(#burst)"/>
  <polygon points="600,40 700,180 880,90 870,250 1080,250 940,400 1140,490 940,580 1080,730 870,720 880,880 700,800 600,940 500,800 320,880 330,720 120,730 260,580 60,490 260,400 120,250 330,250 320,90 500,180"
    fill="url(#halftone)" opacity="0.5"/>
  <!-- Comic action lines -->
  <g stroke="#0a0a0a" stroke-width="4" stroke-linecap="round" opacity="0.7">
    <line x1="600" y1="60" x2="600" y2="120"/>
    <line x1="200" y1="120" x2="240" y2="160"/>
    <line x1="1000" y1="120" x2="960" y2="160"/>
    <line x1="80" y1="350" x2="140" y2="370"/>
    <line x1="1120" y1="350" x2="1060" y2="370"/>
    <line x1="60" y1="540" x2="130" y2="510"/>
    <line x1="1140" y1="540" x2="1070" y2="510"/>
  </g>
  <!-- Site badge top-left -->
  <g transform="translate(80,90) rotate(-4)">
    <rect x="-5" y="-5" width="240" height="58" fill="#0a0a0a"/>
    <rect x="0" y="0" width="230" height="48" fill="#E63946"/>
    <text x="115" y="34" text-anchor="middle" font-family="'Bangers', cursive" font-size="28" fill="#FFFFFF" letter-spacing="3">SOL AI</text>
  </g>
  <!-- Date badge top-right -->
  <g transform="translate(1120,90) rotate(3)">
    <rect x="-180" y="-5" width="180" height="48" fill="#0a0a0a"/>
    <rect x="-175" y="0" width="170" height="38" fill="#FFD166"/>
    <text x="-90" y="28" text-anchor="middle" font-family="'Bangers', cursive" font-size="22" fill="#0a0a0a" letter-spacing="2">{date_display.upper() if date_display else ""}</text>
  </g>
  <!-- Title -->
{title_svg}
  <!-- Footer bar -->
  <rect x="0" y="565" width="1200" height="65" fill="#0a0a0a"/>
  <rect x="0" y="560" width="1200" height="6" fill="#FFD166"/>
  <text x="600" y="606" text-anchor="middle" font-family="'Bangers', cursive" font-size="26" fill="#FFD166" letter-spacing="4">THESOLAI.GITHUB.IO  •  REAL BUILDS, NO CORPORATE SPEAK</text>
</svg>
'''


def _which(binary):
    """Locate a binary, including the usual Homebrew prefixes.

    The content pipeline runs under launchd, whose PATH is minimal and usually
    does not include /opt/homebrew/bin, so a plain shutil.which() would report
    the tools as missing and every publish would fail.
    """
    found = shutil.which(binary)
    if found:
        return found
    for d in ("/opt/homebrew/bin", "/usr/local/bin", "/opt/homebrew/sbin"):
        candidate = Path(d) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _require_tools():
    cairosvg = _which("cairosvg")
    magick = _which("magick") or _which("convert")
    missing = []
    if not cairosvg:
        missing.append("cairosvg (brew install cairosvg)")
    if not magick:
        missing.append("ImageMagick (brew install imagemagick)")
    if missing:
        raise RuntimeError("missing required tool(s): " + ", ".join(missing))
    return cairosvg, magick


def rasterise(svg: str, cairosvg_bin: str, magick_bin: str) -> bytes:
    """Render the SVG artwork to a palette-quantised 1200x630 PNG."""
    raw = subprocess.run(
        [cairosvg_bin, "-f", "png", "-o", "-", "-",
         "--output-width", str(WIDTH), "--output-height", str(HEIGHT)],
        input=svg.encode("utf-8"),
        capture_output=True,
    )
    if raw.returncode != 0:
        raise RuntimeError(f"cairosvg failed: {raw.stderr.decode('utf-8', 'replace')[:400]}")

    quantised = subprocess.run(
        [magick_bin, "png:-", "-colors", str(PALETTE_COLORS), "PNG8:-"],
        input=raw.stdout,
        capture_output=True,
    )
    if quantised.returncode != 0:
        raise RuntimeError(f"magick failed: {quantised.stderr.decode('utf-8', 'replace')[:400]}")
    if not quantised.stdout:
        raise RuntimeError("magick produced an empty PNG")
    return quantised.stdout


def load_manifest():
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def collect_posts():
    if not POSTS_DIR.exists():
        print(f"No _posts/ at {POSTS_DIR}")
        sys.exit(1)
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        parsed = parse_post(path)
        if parsed:
            posts.append(parsed)
    return posts


def check_mode(posts):
    """Verify every post has a matching OG image. Exit 1 if any are missing."""
    manifest = load_manifest()
    problems = []
    for name, title, date, _ in posts:
        png = OG_DIR / f"{name}.png"
        if not png.exists():
            problems.append(f"missing OG image: og/{name}.png")
            continue
        expected = hashlib.sha1(render_og_svg(title, date, name).encode("utf-8")).hexdigest()
        if manifest.get(f"{name}.png") != expected:
            problems.append(f"stale OG image: og/{name}.png")
    if problems:
        print(f"OG check FAILED — {len(problems)} problem(s):")
        for p in problems[:40]:
            print(f"   {p}")
        if len(problems) > 40:
            print(f"   ... and {len(problems) - 40} more")
        return 1
    print(f"OG check passed — {len(posts)} posts, all images present and current")
    return 0


def prune(expected_names, manifest):
    """Remove stale files from og/ (old SVGs, images for deleted posts)."""
    removed = []
    for f in sorted(OG_DIR.iterdir()):
        if not f.is_file():
            continue
        if f.name == MANIFEST.name:
            continue
        if f.name.endswith(".png") and f.stem in expected_names:
            continue
        removed.append(f.name)
        f.unlink()
    for name in list(manifest):
        if f"{name[:-4]}.png" not in expected_names:
            del manifest[name]
    if removed:
        print(f"  pruned {len(removed)} stale file(s): {', '.join(removed[:10])}"
              + (" ..." if len(removed) > 10 else ""))
    return removed


def main():
    ap = argparse.ArgumentParser(description="Generate Open Graph images for every post.")
    ap.add_argument("--force", action="store_true", help="regenerate every image")
    ap.add_argument("--check", action="store_true", help="verify only, exit 1 on problems")
    ap.add_argument("--no-prune", action="store_true", help="keep stale files in og/")
    ap.add_argument("--jobs", type=int, default=8, help="parallel render workers")
    args = ap.parse_args()

    OG_DIR.mkdir(exist_ok=True)
    posts = collect_posts()

    if args.check:
        return check_mode(posts)

    cairosvg_bin, magick_bin = _require_tools()
    manifest = load_manifest()

    print(f"Generating OG images for {len(posts)} posts...")

    todo = []
    reused = 0
    total_bytes = 0
    for name, title, date, _ in posts:
        svg = render_og_svg(title, date, name)
        digest = hashlib.sha1(svg.encode("utf-8")).hexdigest()
        out = OG_DIR / f"{name}.png"
        if not args.force and manifest.get(f"{name}.png") == digest and out.exists():
            reused += 1
            total_bytes += out.stat().st_size
            continue
        todo.append((name, svg, digest, out))

    def render(job):
        name, svg, digest, out = job
        out.write_bytes(rasterise(svg, cairosvg_bin, magick_bin))
        return name, digest, out.stat().st_size

    generated = 0
    if todo:
        # Rendering is dominated by two subprocess calls, so threads are enough
        # to use every core. The manifest is persisted as we go so an
        # interrupted run resumes instead of starting over.
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            for name, digest, size in pool.map(render, todo):
                manifest[f"{name}.png"] = digest
                generated += 1
                total_bytes += size
                if generated % 50 == 0:
                    MANIFEST.write_text(
                        json.dumps(manifest, indent=0, sort_keys=True), encoding="utf-8"
                    )
                    print(f"  {generated}/{len(todo)} rendered", flush=True)

    if not args.no_prune:
        prune({p[0] for p in posts}, manifest)

    MANIFEST.write_text(json.dumps(manifest, indent=0, sort_keys=True), encoding="utf-8")

    print(f"  generated: {generated}")
    print(f"  reused:    {reused}")
    print(f"  output:    {OG_DIR}/")
    print(f"  total size: {total_bytes / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
