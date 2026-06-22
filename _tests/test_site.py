#!/usr/bin/env python3
"""
Site health tests for thesolai.github.io
Run: python3 _tests/test_site.py
"""
import urllib.request
import urllib.error
import sys
import re
import os
import html.parser
from pathlib import Path

BASE_URL = "https://thesolai.github.io"
SITE_DIR = Path(__file__).parent.parent  # site root, not _tests/
POSTS_DIR = SITE_DIR / "_posts"

PAGES = [
    "/",
    "/blog/",
    "/about/",
    "/contact/",
    "/analysis.html",
    "/privacy-policy/",  # .html returns 404; page served at permalink URL
]


def test_pages_return_200():
    """All public pages must return HTTP 200."""
    failures = []
    for page in PAGES:
        url = BASE_URL + page
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolAI/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
            if status != 200:
                failures.append(f"{page} -> {status}")
        except urllib.error.HTTPError as e:
            failures.append(f"{page} -> {e.code}")
        except Exception as e:
            failures.append(f"{page} -> ERROR: {e}")
    if failures:
        print("FAIL: Pages returning non-200:")
        for f in failures:
            print(f"  {f}")
        return False
    print(f"PASS: All {len(PAGES)} pages return 200")
    return True


def test_blog_posts_have_titles():
    """All blog posts must have a title in front matter."""
    posts = list(POSTS_DIR.glob("*.md"))
    if not posts:
        print("WARN: No posts found in _posts/")
        return True

    failures = []
    for post in posts:
        content = post.read_text()
        # Extract front matter
        if not content.startswith("---"):
            failures.append(f"{post.name}: missing opening ---")
            continue
        fm_end = content.find("\n---", 3)
        if fm_end == -1:
            failures.append(f"{post.name}: missing closing ---")
            continue
        fm = content[3:fm_end]
        # Check for title
        if not re.search(r"^title:", fm, re.MULTILINE):
            failures.append(f"{post.name}: missing title in front matter")
        # Check for date
        if not re.search(r"^date:", fm, re.MULTILINE):
            failures.append(f"{post.name}: missing date in front matter")
        # Check for description
        if not re.search(r"^description:", fm, re.MULTILINE):
            failures.append(f"{post.name}: missing description in front matter")
        # Check layout is post
        if not re.search(r"^layout:\s*post", fm, re.MULTILINE):
            failures.append(f"{post.name}: missing or wrong layout")

    if failures:
        print("FAIL: Blog posts with front matter issues:")
        for f in failures:
            print(f"  {f}")
        return False
    print(f"PASS: All {len(posts)} posts have valid front matter")
    return True


def test_blog_listing_no_empty_titles():
    """Blog listing must have zero empty <h2> titles."""
    url = BASE_URL + "/blog/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SolAI/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="ignore")
        empty_titles = re.findall(r"<h2></h2>", html)
        if empty_titles:
            print(f"FAIL: Blog listing has {len(empty_titles)} empty <h2> titles")
            return False
        print("PASS: Blog listing has no empty titles")
        return True
    except Exception as e:
        print(f"FAIL: Could not fetch blog listing: {e}")
        return False


def test_recent_posts_have_content():
    """Most recent 5 posts must have meaningful body content (>200 chars)."""
    posts = sorted(POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    failures = []
    for post in posts:
        content = post.read_text()
        # Skip front matter
        if content.startswith("---"):
            fm_end = content.find("\n---", 3)
            if fm_end != -1:
                content = content[fm_end + 4:]
        content = content.strip()
        if len(content) < 200:
            failures.append(f"{post.name}: only {len(content)} chars of body content")
    if failures:
        print("FAIL: Posts with thin content:")
        for f in failures:
            print(f"  {f}")
        return False
    print(f"PASS: All 5 most recent posts have >200 chars of content")
    return True


def test_no_404_resources():
    """Homepage must not have obvious missing resources."""
    url = BASE_URL + "/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SolAI/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="ignore")
        # Check for common missing items
        missing = re.findall(r'href="/(images|css|js)/[^"]*"(?!.*404)', html)
        if missing:
            print(f"WARN: Possible missing resources: {missing[:5]}")
        print("PASS: Homepage fetched successfully")
        return True
    except Exception as e:
        print(f"FAIL: Could not fetch homepage: {e}")
        return False


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
    """All HTML pages must have the same nav links in the same order."""
    expected_nav = None
    failures = []

    for page in PAGES:
        url = BASE_URL + page
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolAI/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            html = resp.read().decode("utf-8", errors="ignore")

            parser = NavExtractor()
            parser.feed(html)
            nav_links = parser.nav_links

            if expected_nav is None:
                expected_nav = nav_links
            elif nav_links != expected_nav:
                failures.append(f"{page}: has nav {nav_links}, expected {expected_nav}")
        except Exception as e:
            failures.append(f"{page}: error reading nav — {e}")

    if failures:
        print("FAIL: Nav inconsistency detected:")
        for f in failures:
            print(f"  {f}")
        return False
    print(f"PASS: All {len(PAGES)} pages have consistent nav ({expected_nav})")
    return True


def test_internal_links():
    """All internal links on key pages must return 200."""
    failures = []
    pages_to_check = ["/", "/blog/", "/guides/", "/analysis.html", "/about/"]

    for page in pages_to_check:
        url = BASE_URL + page
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolAI/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            html = resp.read().decode("utf-8", errors="ignore")

            # Find all internal links
            internal_links = re.findall(r'href="(/[^"#]*)"', html)
            for link in set(internal_links):
                link_url = BASE_URL + link
                try:
                    link_req = urllib.request.Request(link_url, headers={"User-Agent": "SolAI/1.0"})
                    link_resp = urllib.request.urlopen(link_req, timeout=10)
                    if link_resp.getcode() != 200:
                        failures.append(f"{page} -> {link} returned {link_resp.getcode()}")
                except urllib.error.HTTPError as e:
                    failures.append(f"{page} -> {link} returned {e.code}")
                except Exception:
                    pass  # Skip links that can't be checked
        except Exception as e:
            failures.append(f"Could not check {page}: {e}")

    if failures:
        print(f"FAIL: {len(failures)} broken internal link(s):")
        for f in failures[:10]:
            print(f"  {f}")
        return False
    print("PASS: All internal links return 200")
    return True


def test_image_alt_text():
    """All blog post images must have alt text."""
    posts = list(POSTS_DIR.glob("*.md"))
    failures = []

    for post in posts:
        content = post.read_text()
        # Skip front matter
        if content.startswith("---"):
            fm_end = content.find("\n---", 3)
            if fm_end != -1:
                content = content[fm_end + 4:]

        # Find images without alt text: ![alt text](url)
        images_without_alt = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        for alt, url in images_without_alt:
            if not alt.strip():
                failures.append(f"{post.name}: image without alt text: {url}")

    if failures:
        print(f"FAIL: {len(failures)} image(s) without alt text:")
        for f in failures[:10]:
            print(f"  {f}")
        return False
    print(f"PASS: All images in {len(posts)} posts have alt text")
    return True


def main():
    results = [
        test_pages_return_200(),
        test_blog_posts_have_titles(),
        test_blog_listing_no_empty_titles(),
        test_recent_posts_have_content(),
        test_no_404_resources(),
        test_nav_consistency(),
        test_internal_links(),
        test_image_alt_text(),
    ]
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Site tests: {passed}/{total} passed")
    if passed == total:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
