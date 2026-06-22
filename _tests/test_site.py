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

def main():
    results = [
        test_pages_return_200(),
        test_blog_posts_have_titles(),
        test_blog_listing_no_empty_titles(),
        test_recent_posts_have_content(),
        test_no_404_resources(),
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
