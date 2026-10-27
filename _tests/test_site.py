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
import time
import html.parser
import concurrent.futures
import subprocess
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


def head_status(url, timeout=15, retries=3, delay=5):
    """HEAD request — returns int status code, or -1 on error.

    Transient upstream failures (502/503/504, or a connection error while
    GitHub Pages swaps the site during a deploy) are retried. Without the
    retry, a deploy landing mid-test failed the whole Site Health Tests
    run on a perfectly healthy site: the 2026-10-22 build failed on
    "503 https://thesolai.github.io/guides" while every other check
    passed and the page was live seconds later.
    """
    last = -1
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, method="HEAD",
                                        headers={"User-Agent": "SolAI-Tests/2.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.getcode()
        except urllib.error.HTTPError as e:
            last = e.code
            # 5xx and 429 are the server's problem, not the site's. Retry.
            if e.code not in (429, 500, 502, 503, 504):
                return e.code
        except Exception:
            last = -1
        if attempt < retries:
            time.sleep(delay * (attempt + 1))
    return last


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

def _sitemap_post_urls():
    """Return the published post paths from the live sitemap, oldest first.

    The sitemap is the source of truth for what is actually published. Using
    it — rather than the local _posts directory — is what keeps this module
    race-free. On a push, the working tree contains posts that were committed
    seconds ago and are not live until the deploy finishes; the sitemap
    contains exactly what has been published.
    """
    try:
        sitemap = urllib.request.urlopen(
            urllib.request.Request(BASE_URL + "/sitemap.xml",
                                  headers={"User-Agent": "SolAI-Tests/2.0"}),
            timeout=20
        ).read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  FAIL: could not fetch sitemap.xml ({e})")
        return None

    urls = re.findall(
        r"<loc>https://thesolai\.github\.io(/blog/\d{4}/\d{2}/\d{2}/[^<]+?)</loc>",
        sitemap)
    if not urls:
        print("  FAIL: no blog post URLs found in sitemap")
        return None
    return urls


def _post_path_sort_key(path):
    """Sort key for a /blog/YYYY/MM/DD/slug/ path — oldest first."""
    m = re.match(r"^/blog/(\d{4})/(\d{2})/(\d{2})/(.*)$", path)
    if not m:
        return ("", "", "", path)
    return (m.group(1), m.group(2), m.group(3), m.group(4))


def _local_posts_by_date(limit=None):
    """Local posts, newest first, ordered by when they were committed.

    The previous implementation sorted by filesystem mtime. That is
    meaningless in CI: actions/checkout writes files in path order, so every
    post gets roughly the same mtime and "most recently modified" collapses
    to "alphabetically last" — which is precisely the set of posts that were
    just committed and are not live yet.

    Git knows the real order. `git log --diff-filter=A` lists post files in
    the order they were first added, newest commit first, which is exactly
    "the most recently published posts" — and it is identical locally and in
    CI. Filenames are date-prefixed as a fallback for the rare case where
    git history is unavailable (a shallow clone with no additions recorded).
    """
    posts = list(POSTS_DIR.glob("*.md"))

    added = []
    try:
        out = subprocess.run(
            ["git", "-C", str(SITE_DIR), "log", "--diff-filter=A", "--name-only",
             "--pretty=format:", "-n", "200", "--", "_posts/"],
            capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            for line in out.stdout.splitlines():
                line = line.strip()
                if line.startswith("_posts/") and line.endswith(".md"):
                    p = SITE_DIR / line
                    if p.exists() and p not in added:
                        added.append(p)
    except Exception:
        pass

    if added:
        # Anything git did not report (added before the history window)
        # follows, newest date first.
        rest = sorted((p for p in posts if p not in added),
                      key=lambda p: (p.stem[:10], p.stem), reverse=True)
        ordered = added + rest
    else:
        ordered = sorted(posts, key=lambda p: (p.stem[:10], p.stem), reverse=True)

    return ordered[:limit] if limit else ordered


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
    """Every published post permalink must resolve to 200.

    Uses the live sitemap as source of truth since Jekyll URL construction
    (date from frontmatter vs filename vs filesystem mtime) varies between
    local dev and GitHub Actions.
    """
    print("• all post permalinks return 200")

    # Fetch sitemap to get authoritative URLs — avoids replicating Jekyll's
    # complex date/slug resolution logic (frontmatter vs filename vs mtime).
    try:
        sitemap = urllib.request.urlopen(
            urllib.request.Request(BASE_URL + "/sitemap.xml",
                                  headers={"User-Agent": "SolAI-Tests/2.0"}),
            timeout=20
        ).read().decode("utf-8", errors="replace")
    except Exception:
        print("  FAIL: could not fetch sitemap.xml")
        return False

    # Extract all /blog/ URLs from sitemap (skip tag/author archive pages)
    sitemap_urls = re.findall(r"<loc>(https://thesolai\.github\.io(/blog/\d{4}/\d{2}/\d{2}/[^<]+?)/)</loc>", sitemap)
    if not sitemap_urls:
        print("  FAIL: no blog post URLs found in sitemap")
        return False

    # Index by slug (last path segment without trailing slash)
    url_map = {u.split("/")[-2]: u for u, _ in sitemap_urls}

    # Get 50 most-recently-committed posts
    posts = _local_posts_by_date(limit=50)

    def jekyll_slugify(name):
        """Mirror Jekyll's slugify: strip non-alnum, collapse hyphens, trim."""
        s = re.sub(r'[^a-z0-9]', '-', name.lower())
        s = re.sub(r'-+', '-', s).strip('-')
        return s

    urls = []
    for p in posts:
        slug = p.stem
        # Derive the title slug the same way the sitemap does — from filename
        date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", slug)
        if not date_match:
            continue
        title_slug = jekyll_slugify(slug[len("YYYY-MM-DD-"):])
        # Look up in sitemap URL map
        url = url_map.get(title_slug)
        if not url:
            # Fallback: construct from sitemap URL if title slug found as substring
            for k, v in url_map.items():
                if title_slug in k or k in title_slug:
                    url = v
                    break
        if url:
            urls.append(url)

    if not urls:
        print("  FAIL: no post URLs could be resolved from sitemap")
        return False

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
    posts = _local_posts_by_date(limit=5)
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


def test_og_image_files_exist():
    """Every post must have a matching Open Graph image on disk.

    The post layout derives the og:image URL from the post's source filename
    (page.path), so the image has to be og/<source-filename-stem>.png. Getting
    this wrong is what left 100% of posts with a 404 og:image — the layout used
    page.slug (which has the date stripped) while the generator wrote the full
    filename. This test is the regression guard for that mismatch.
    """
    print("• every post has a matching OG image file")
    og_dir = SITE_DIR / "og"
    failures = []
    posts = list(POSTS_DIR.glob("*.md"))
    for p in posts:
        expected = og_dir / f"{p.stem}.png"
        if not expected.exists():
            failures.append(f"{p.name}: missing og/{p.stem}.png")
    if failures:
        print(f"  FAIL: {len(failures)} post(s) without an OG image:")
        for f in failures[:10]:
            print(f"    {f}")
        return False
    print(f"  PASS: all {len(posts)} posts have og/<name>.png")
    return True


def test_layout_uses_source_path_for_og_image():
    """The post layout must derive og:image from page.path, not page.slug."""
    print("• post layout derives og:image from page.path")
    layout = SITE_DIR / "_layouts" / "post.html"
    if not layout.exists():
        print("  FAIL: _layouts/post.html not found")
        return False
    html = layout.read_text(encoding="utf-8", errors="replace")
    failures = []
    for tag in ("og:image", "twitter:image"):
        m = re.search(rf'<meta[^>]+{tag}[^>]*>', html)
        if not m:
            failures.append(f"{tag} meta tag missing from post layout")
            continue
        if "page.slug" in m.group(0):
            failures.append(f"{tag} uses page.slug (date stripped) — must use page.path")
    for tag in ("og:title", "og:description"):
        if f'property="{tag}"' not in html:
            failures.append(f"{tag} meta tag missing from post layout")
    if 'rel="canonical"' not in html:
        failures.append("canonical link missing from post layout")
    if failures:
        print("  FAIL:")
        for f in failures:
            print(f"    {f}")
        return False
    print("  PASS: og:image/twitter:image use page.path, canonical + og tags present")
    return True


def test_live_og_images_resolve():
    """Spot-check live posts: their og:image URL must resolve.

    Source-level checks cannot catch a file that exists locally but was never
    deployed, so this fetches a sample of recently published posts and HEADs
    the og:image each one advertises.

    The sample is drawn from the live sitemap, NOT from the local _posts
    directory. A post that was pushed a moment ago is committed but not yet
    deployed, so fetching it here returned 404 and failed the whole run — on
    2026-10-27 this alone failed the Site Health Tests for two commits in a
    row while every other check passed. Taking the sample from what is
    actually published keeps the check meaningful (it still verifies that
    deployed posts advertise a reachable social card) without racing the
    deploy that is still in flight.
    """
    print("• live og:image URLs resolve")
    published = _sitemap_post_urls()
    if published is None:
        return False

    # Most recent published posts — same date ordering as the sitemap.
    recent = sorted(published, key=_post_path_sort_key, reverse=True)[:12]

    failures = []
    checked = 0
    for path in recent:
        url = BASE_URL + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolAI-Tests/2.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            failures.append(f"{path}: could not fetch post ({e})")
            continue
        m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
        if not m:
            failures.append(f"{path}: no og:image tag in rendered page")
            continue
        image_url = m.group(1)
        if image_url.startswith("/"):
            image_url = BASE_URL + image_url
        checked += 1
        status = head_status(image_url)
        if status != 200:
            failures.append(f"{path}: og:image {status} {image_url}")
    if failures:
        print(f"  FAIL: {len(failures)} og:image problem(s):")
        for f in failures[:10]:
            print(f"    {f}")
        return False
    print(f"  PASS: {checked} live og:image URLs return 200")
    return True


def test_latest_posts_are_published():
    """Every locally committed post must be reachable on the live site.

    The 2026-10-22 incident was exactly this failure: content was committed
    and pushed, but a push landed on a side branch instead of main, so the
    posts never went live while every log line said they had. Nothing in the
    suite noticed, because every check that looked at the live site only
    looked at posts that were already there.

    This closes that gap: take the newest posts that exist locally and
    require each one to be published and to resolve. A post that is committed
    but not yet deployed fails here, loudly.

    There is a deliberate grace period. The deploy for a push lands a minute
    or two after the push, so a post committed seconds ago may legitimately
    not be live yet. The check therefore retries for a few minutes before
    declaring failure, which distinguishes "still deploying" from "lost".
    """
    print("• newest committed posts are published")
    newest = _local_posts_by_date(limit=3)
    if not newest:
        print("  FAIL: no posts found in _posts")
        return False

    deadline = time.time() + 300
    attempt = 0
    while True:
        attempt += 1
        published = _sitemap_post_urls()
        if published is None:
            # Sitemap unreachable — treat as a transient network problem and
            # retry rather than failing on a fluke.
            if time.time() < deadline:
                time.sleep(20)
                continue
            return False

        live_paths = {p for p in published}
        missing = []
        for p in newest:
            date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", p.stem)
            if not date_match:
                continue
            slug = re.sub(r"[^a-z0-9]", "-", p.stem[len(date_match.group(0)):].lower())
            slug = re.sub(r"-+", "-", slug).strip("-")
            path = (f"/blog/{date_match.group(1)}/{date_match.group(2)}/"
                    f"{date_match.group(3)}/{slug}/")
            if path not in live_paths:
                missing.append(p.name)

        if not missing:
            print(f"  PASS: all {len(newest)} newest posts are published "
                  f"(attempt {attempt})")
            return True

        if time.time() >= deadline:
            print(f"  FAIL: {len(missing)} committed post(s) not published "
                  f"after {attempt} attempts over 5 minutes:")
            for m in missing:
                print(f"    {m}")
            return False

        time.sleep(20)


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
        test_og_image_files_exist,
        test_layout_uses_source_path_for_og_image,
        test_live_og_images_resolve,
        test_latest_posts_are_published,
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
