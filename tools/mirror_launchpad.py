#!/usr/bin/env python3
"""
Mirror a static GitHub Pages site to a local folder, rewriting links so it
runs standalone. Stdlib only (no requests / bs4 / wget on this machine).

Usage: python3 mirror_launchpad.py <base_url> <out_dir> [extra_asset_urls...]
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

MAX_PAGES = 40
MAX_ASSETS = 300
TIMEOUT = 25

# attributes that can carry a URL
URL_ATTRS = {
    "a": ["href"],
    "link": ["href"],
    "script": ["src"],
    "img": ["src", "data-src", "srcset"],
    "source": ["src", "srcset"],
    "video": ["src", "poster"],
    "audio": ["src"],
    "iframe": ["src"],
    "embed": ["src"],
    "object": ["data"],
    "use": ["href", "xlink:href"],
    "form": ["action"],
}

ASSET_EXT = {
    ".css", ".js", ".mjs", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".avif", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json", ".map",
    ".webm", ".mp4", ".pdf", ".txt", ".xml",
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []          # raw url strings found
        self.style_blocks = []  # inline <style> text
        self._in_style = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self._in_style = True
            self._buf = []
        a = dict(attrs)
        for attr in URL_ATTRS.get(tag, []):
            if a.get(attr):
                for part in a[attr].split(","):
                    u = part.strip().split(" ")[0] if " " in part.strip() else part.strip()
                    if u:
                        self.urls.append(u)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
            self.style_blocks.append("".join(self._buf))

    def handle_data(self, data):
        if self._in_style:
            self._buf.append(data)


def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read(), r.headers.get("Content-Type", ""), r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.2)
    raise last


def local_path_for(url, out_dir, url_map):
    """Map an absolute URL to a relative local path, recording it in url_map."""
    p = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(p.path)
    if path.endswith("/"):
        path += "index.html"
    if not path:
        path = "/index.html"
    if path.endswith(".html") or path.endswith(".htm"):
        rel = path.lstrip("/")
    else:
        name = os.path.basename(path) or "index.html"
        # keep a directory structure for css/, js/, assets/ etc.
        rel = path.lstrip("/") if "/" in path else name
    dest = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    return dest, rel


def rel_link(from_rel, to_rel):
    """Relative URL from one local file to another."""
    return os.path.relpath(to_rel, os.path.dirname(from_rel) or ".")


def rewrite(text, url_map, base_rel):
    """Replace absolute/relative URLs in text with local relative paths."""
    def sub(m):
        raw = m.group(0)
        key = raw.replace("&amp;", "&")
        target = url_map.get(key)
        if target is None:
            target = url_map.get(raw)
        if not target:
            return raw
        return rel_link(base_rel, target)

    # absolute urls first, then quoted relative ones
    text = re.sub(r"https?://[^\s\"'()<>]+", sub, text)
    text = re.sub(r"(?<=[\"'])(?!https?:|//|#|data:|mailto:|tel:)([^\"'\s]+)(?=[\"'])", sub, text)
    text = re.sub(r"(?<=url\()\s*(?!['\"]?https?:|//|data:)([^\"')]+)", sub, text)
    return text


def main():
    base = sys.argv[1].rstrip("/") + "/"
    out_dir = os.path.abspath(sys.argv[2])
    extra = sys.argv[3:]

    os.makedirs(out_dir, exist_ok=True)
    url_map = {}     # raw url string -> local relative path
    fetched = {}     # absolute url -> local rel path
    seen = set()
    queue = [(base, None)]
    pages = 0
    assets = 0
    failures = []
    external = set()

    # ---- stage 1: discover pages (same origin) ----
    page_queue = [base]
    page_urls = set()

    while page_queue and pages < MAX_PAGES:
        cur = page_queue.pop(0)
        if cur in page_urls:
            continue
        page_urls.add(cur)
        try:
            body, ctype, final = fetch(cur)
        except Exception as e:  # noqa: BLE001
            failures.append((cur, str(e)))
            continue
        text = body.decode("utf-8", "replace")
        p = LinkParser()
        try:
            p.feed(text)
        except Exception:  # noqa: BLE001
            pass

        rel = urllib.parse.urlsplit(final).path.lstrip("/") or "index.html"
        if not rel.endswith(".html"):
            rel = rel.rsplit("/", 1)[-1]
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        # rewrite html + inline css
        new_text = rewrite(text, url_map, rel)
        new_text = new_text.replace(
            'href="/css/', 'href="css/').replace("src=\"/js/", "src=\"js/")

        # register every discovered url for later rewriting
        for u in p.urls:
            absu = urllib.parse.urljoin(cur, u)
            if absu.startswith(base):
                continue
            url_map[u] = url_map.get(u)
            if absu not in [k for k in url_map]:
                url_map.setdefault(absu, None)

        # queue same-origin html pages
        for u in p.urls:
            absu = urllib.parse.urljoin(cur, u)
            if not absu.startswith(base):
                continue
            sp = urllib.parse.urlsplit(absu)
            if sp.path.endswith((".html", "/")):
                page_queue.append(absu)

        with open(dest, "w", encoding="utf-8") as f:
            f.write(new_text)
        pages += 1
        # stash raw content for second pass
        fetched[final] = rel

    # ---- stage 2: download assets (same origin + shared css hosts) ----
    def download(absu, referer):
        nonlocal assets
        if assets >= MAX_ASSETS:
            return
        sp = urllib.parse.urlsplit(absu)
        if sp.path.endswith((".html", "/")):
            return
        ext = os.path.splitext(sp.path)[1].lower()
        if ext not in ASSET_EXT:
            return
        try:
            body, ctype, final = fetch(absu)
        except Exception as e:  # noqa: BLE001
            failures.append((absu, str(e)))
            return
        dest, rel = local_path_for(final, out_dir, url_map)
        if rel.endswith(".css") or rel.endswith(".svg"):
            txt = body.decode("utf-8", "replace")
            txt = rewrite(txt, url_map, rel)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(txt)
        else:
            with open(dest, "wb") as f:
                f.write(body)
        url_map[absu] = rel
        assets += 1

    # gather asset urls from the downloaded html files
    asset_urls = []
    for root, _dirs, files in os.walk(out_dir):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(root, fn)
            txt = open(fp, encoding="utf-8", errors="replace").read()
            pp = LinkParser()
            try:
                pp.feed(txt)
            except Exception:  # noqa: BLE001
                pass
            rel = os.path.relpath(fp, out_dir)
            for u in pp.urls:
                if u.startswith(("http://", "https://", "//")):
                    external.add(u)
                    continue
                absu = urllib.parse.urljoin(base, u)
                asset_urls.append((absu, rel))
            for blk in pp.style_blocks:
                for m in re.finditer(r"url\((['\"]?)([^)'\"]+)\1\)", blk):
                    u = m.group(2)
                    if not u.startswith(("http://", "https://", "//", "data:")):
                        asset_urls.append((urllib.parse.urljoin(base, u), rel))

    for absu, _ref in asset_urls:
        if absu.startswith(base):
            download(absu, base)

    # shared external stylesheets the page hard-depends on
    for x in extra:
        download(x, base)

    # ---- stage 3: final rewrite pass now that url_map is populated ----
    for root, _dirs, files in os.walk(out_dir):
        for fn in files:
            if not (fn.endswith(".html") or fn.endswith(".css")):
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, out_dir)
            txt = open(fp, encoding="utf-8", errors="replace").read()
            new = rewrite(txt, url_map, rel)
            if new != txt:
                open(fp, "w", encoding="utf-8").write(new)

    total = sum(len(f) for _r, _d, f in os.walk(out_dir))
    size = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _d, fs in os.walk(out_dir) for f in fs
    )
    print(f"pages={pages} assets={assets} files={total} bytes={size}")
    print(f"external-left-absolute={len(external)}")
    if failures:
        print(f"failures={len(failures)}")
        for u, e in failures[:12]:
            print("  FAIL", u, "->", str(e)[:90])


if __name__ == "__main__":
    main()
