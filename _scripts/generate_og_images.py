#!/usr/bin/env python3
"""
Per-post OG image generator.

Reads every Jekyll post in _posts/ and writes a 1200x630 SVG to /og/<slug>.svg
with comic-book styling (Bangers + Comic Neue, yellow burst, post title, date,
Sol AI branding). SVGs are referenced as og:image by the post layout.

Re-run whenever posts are added/edited:

    python3 _scripts/generate_og_images.py

Design constraints:
  - Pure SVG (no external deps; no ImageMagick / rmagick needed)
  - 1200x630 (Facebook/Twitter/LinkedIn standard OG size)
  - Yellow burst + halftone overlay (matches site hero)
  - Title auto-wraps at ~28 chars per line
  - Date + site name in footer
  - Black outline + comic-book drop shadow
  - Truncated title fallback for very long titles
"""
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "_posts"
OG_DIR = REPO / "og"
OG_DIR.mkdir(exist_ok=True)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^([a-zA-Z_]+):\s*(.*)$", re.MULTILINE)


def parse_post(path: Path):
    """Return (slug, title, date_str, description) or None."""
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
        if val.startswith('[') and val.endswith(']'):
            return val
        return val

    title = field("title").strip().strip('"').strip("'")
    date = field("date").strip()
    description = field("description").strip().strip('"').strip("'")
    slug = path.stem  # filename without .md
    # Some posts have slug frontmatter override
    explicit_slug = field("slug").strip().strip('"').strip("'")
    if explicit_slug:
        slug = explicit_slug
    return slug, title, date, description


def slugify_for_url(s: str) -> str:
    """Jekyll-style slug: lowercase, hyphens, strip non-alnum."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


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


def render_og_svg(title: str, date_str: str, slug: str) -> str:
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


def main():
    if not POSTS_DIR.exists():
        print(f"No _posts/ at {POSTS_DIR}")
        sys.exit(1)

    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        parsed = parse_post(path)
        if parsed:
            posts.append(parsed)

    print(f"Generating OG images for {len(posts)} posts...")
    generated, skipped = 0, 0
    for slug, title, date, _ in posts:
        svg = render_og_svg(title, date, slug)
        out = OG_DIR / f"{slug}.svg"
        out.write_text(svg, encoding="utf-8")
        generated += 1
    print(f"  generated: {generated}")
    print(f"  skipped:   {skipped}")
    print(f"  output:    {OG_DIR}/")
    print(f"  total size: {sum((OG_DIR / f'{p[0]}.svg').stat().st_size for p in posts) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
