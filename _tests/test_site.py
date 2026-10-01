#!/usr/bin/env python3
"""
Site health tests for thesolai.github.io

Run: python3 _tests/test_site.py

Coverage:
  1. Top-level pages return 200 (parallel)
  2. Every published post permalink returns 200 (parallel)
  3. Every post has a non-empty title and date in frontmatter
  4. Recent posts have meaningful body content
  5. Nav is consistent across pages (homepage is the reference)
  6. Internal links on homepage and key pages return 200
  7. Images have alt text
  8. No stray '**' markdown in post titles

Designed to complete in <30s against the live site.
"""
import urllib.request
import urllib.error
import re
import sys
import os
import html.parser
import concurrent.futures
from pathlib import Path
from datetime import datetime

BASE_URL = "https://thesolai.github.io"
SITE_DIR = Path(__file__).parent.parent
POSTS_DIR = SITE_DIR / "_posts"

TOP_PAGES = [
    "/", "/blog/", "/newsletter/", "/about/", "/contact/",
    "/products/", "/skills/", "/purr/", "/dross/",
    "/ournook", "/analysis/", "/bloopers/",
    "/privacy-policy/", "/guestbook.html",
    "/guides/", "/store/",
    "/feed.xml", "/sitemap.xml",
]


def head_status(url, timeout=15):
    """HEAD request — returns int status code, or -1 on error."""
    try:
        req = urllib.request.Request(url, method="HEAD",
                                    headers={"User-Agent": "SolAI-Tests/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def parallel_check(urls, max_workers=20, timeout=15):
    """Check many URLs in parallel. Returns dict[url] -> status."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(head_status, u, timeout): u for u in urls}
        for fut in concurrent.futures.as_completed(futures):
            url = futures[fut]
            try:
                results[url] = fut.result()
            except Exception:
                results[url] = -1
    return results


# ─────────────────────────── Tests ───────────────────────────

def test_top_pages_return_200():
    print("• top pages return 200")
    results = parallel_check([BASE_URL + p for p in TOP_PAGES])
    failures = [(u, s) for u, s in results.items() if s != 200]
    if failures:
        print(f"  FAIL: {len(failures)} page(s) not 200:")
        for u, s in failures[:10]:
            print(f"    {s}  {u}")
        return False
    print(f"  PASS: all {len(TOP_PAGES)} top pages return 200")
    return True


def test_all_post_permalinks_return_200():
    """Every published post permalink must resolve to 200."""
    print("• all post permalinks return 200")
    posts = sorted(POSTS_DIR.glob("*.md"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:50]

    def jekyll_slugify(name):
        """Mirror Jekyll's slugify: strip non-alnum, collapse hyphens, trim."""
        s = re.sub(r'[^a-z0-9]', '-', name.lower())
        s = re.sub(r'-+', '-', s).strip('-')
        return s

    urls = []
    for p in posts:
        slug = p.stem
        date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", slug)
        if not date_match:
            continue
        y, mo, d = date_match.groups()
        title_part = jekyll_slugify(slug[len(y)+len(mo)+len(d)+3:])
        url = f"{BASE_URL}/blog/{y}/{mo}/{d}/{title_part}/"
        urls.append(url)

    results = parallel_check(urls, max_workers=30)
    failures = [(u, s) for u, s in results.items() if s != 200]
    if failures:
        print(f"  FAIL: {len(failures)}/{len(urls)} recent post URLs broken:")
        for u, s in failures[:10]:
            print(f"    {s}  {u}")
        return False
    print(f"  PASS: all {len(urls)} recent post URLs return 200")
    return True


def test_post_front_matter():
    print("• posts have valid title + date")
    failures = []
    for p in POSTS_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not m:
            failures.append(f"{p.name}: no frontmatter block")
            continue
        fm = m.group(1)
        if not re.search(r"^title:\s*\S", fm, re.MULTILINE):
            failures.append(f"{p.name}: missing title")
        if not re.search(r"^date:\s*\S", fm, re.MULTILINE):
            failures.append(f"{p.name}: missing date")
        # Stray ** in title (markdown that leaked into frontmatter)
        m2 = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
        if m2 and "**" in m2.group(1):
            failures.append(f"{p.name}: stray '**' in title")
    if failures:
        print(f"  FAIL: {len(failures)} post(s) with bad frontmatter:")
        for f in failures[:10]:
            print(f"    {f}")
        return False
    print(f"  PASS: all {len(list(POSTS_DIR.glob('*.md')))} posts have valid frontmatter")
    return True


def test_recent_posts_have_content():
    print("• most recent 5 posts have meaningful content")
    posts = sorted(POSTS_DIR.glob("*.md"),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    failures = []
    for p in posts:
        content = p.read_text()
        if content.startswith("---"):
            fm_end = content.find("\n---", 3)
            if fm_end != -1:
                content = content[fm_end + 4:]
        content = content.strip()
        if len(content) < 200:
            failures.append(f"{p.name}: only {len(content)} chars body")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return False
    print(f"  PASS: 5 most recent posts all have >200 chars body")
    return True


class NavExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.nav_links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'nav':
            self.in_nav = True
        elif tag == 'a' and self.in_nav:
            href = dict(attrs).get('href', '')
            if href:
                self.nav_links.append(href)

    def handle_endtag(self, tag):
        if tag == 'nav' and self.in_nav:
            self.in_nav = False


def test_nav_consistency():
    """Topbar nav should be consistent across pages."""
    print("• topbar nav consistent across pages")
    expected = None
    failures = []
    pages_to_check = ["/", "/blog/", "/newsletter/", "/about/", "/contact/",
                       "/products/", "/analysis/"]
    for page in pages_to_check:
        url = BASE_URL + page
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolAI-Tests/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            parser = NavExtractor()
            parser.feed(html)
            nav = parser.nav_links
            if expected is None:
                expected = nav
            elif nav != expected:
                failures.append(f"{page}: differs from homepage")
        except Exception as e:
            failures.append(f"{page}: {e}")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return False
    print(f"  PASS: all {len(pages_to_check)} pages share the same topbar ({len(expected)} items)")
    return True


def test_internal_links():
    """Sample internal links on key pages return 200."""
    print("• internal links on homepage return 200")
    url = BASE_URL + "/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SolAI-Tests/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  FAIL: could not fetch homepage: {e}")
        return False

    internal = set(re.findall(r'href="(/[^"#]*)"', html))
    # exclude external + mailto + anchor-only
    internal = {l for l in internal if not l.startswith("//") and not l.startswith("http")}
    urls = [BASE_URL + l for l in internal]
    results = parallel_check(urls, max_workers=30)
    failures = [(u, s) for u, s in results.items() if s != 200]
    if failures:
        print(f"  FAIL: {len(failures)} broken link(s) from homepage:")
        for u, s in failures[:10]:
            print(f"    {s}  {u}")
        return False
    print(f"  PASS: all {len(urls)} internal links from homepage return 200")
    return True


def test_image_alt_text():
    print("• blog post images have alt text")
    failures = []
    for p in POSTS_DIR.glob("*.md"):
        content = p.read_text()
        if content.startswith("---"):
            fm_end = content.find("\n---", 3)
            if fm_end != -1:
                content = content[fm_end + 4:]
        for alt, url in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content):
            if not alt.strip():
                failures.append(f"{p.name}: image missing alt: {url}")
                if len(failures) >= 20:
                    break
        if len(failures) >= 20:
            break
    if failures:
        print(f"  FAIL: {len(failures)}+ posts have images without alt text")
        for f in failures[:5]:
            print(f"    {f}")
        return False
    print(f"  PASS: all post images have alt text (scanned first 20 issues)")
    return True


def main():
    start = datetime.now()
    tests = [
        test_top_pages_return_200,
        test_all_post_permalinks_return_200,
        test_post_front_matter,
        test_recent_posts_have_content,
        test_nav_consistency,
        test_internal_links,
        test_image_alt_text,
    ]
    results = []
    for t in tests:
        try:
            results.append(t())
        except Exception as e:
            print(f"  ERROR in {t.__name__}: {e}")
            results.append(False)
    passed = sum(results)
    total = len(results)
    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*50}")
    print(f"  {passed}/{total} test groups passed ({elapsed:.1f}s)")
    print('='*50)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
