#!/usr/bin/env python3
"""
Resolve and download CSS-referenced assets (url(...)) into a mirrored site.

The first-pass mirror only followed references found in HTML. Background
images, logos and fonts referenced from stylesheets were therefore missing.
This pass:
  * scans every local .css file for url(...) references
  * resolves each relative to the stylesheet's own directory
  * tries the launchpad origin first, then the shared elemento.cloud origin
  * writes the file into the same relative position and rewrites the CSS to
    point at the local copy
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

ORIGINS = [
    "https://launchpad.electros.cloud/",
    "https://elemento.cloud/",
]

URL_FUNC = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.I)
SKIP_PREFIX = ("data:", "http://", "https://", "//", "#", "about:")

downloaded = 0
failed = []
seen = set()


def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read(), r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.0)
    raise last


def resolve(css_rel, ref):
    """Return candidate absolute URLs for a ref seen in css_rel."""
    ref = ref.strip()
    if ref.startswith(SKIP_PREFIX):
        return []
    # absolute path on the origin
    if ref.startswith("/"):
        path = ref
    else:
        base_dir = os.path.dirname(css_rel)
        path = "/" + os.path.normpath(os.path.join(base_dir, ref)).replace(os.sep, "/")
    cands = []
    for origin in ORIGINS:
        cands.append(urllib.parse.urljoin(origin, path.lstrip("/")))
    return cands


def main():
    root = os.path.abspath(sys.argv[1])
    global downloaded

    # collect css files
    css_files = []
    for dirpath, _d, files in os.walk(root):
        for fn in files:
            if fn.endswith(".css"):
                css_files.append(os.path.join(dirpath, fn))

    replacements = {}  # css file -> list of (old, new)

    for css_path in css_files:
        css_rel = os.path.relpath(css_path, root)
        txt = open(css_path, encoding="utf-8", errors="replace").read()
        for m in URL_FUNC.finditer(txt):
            ref = m.group(2)
            if ref.startswith(SKIP_PREFIX):
                continue
            key = (css_rel, ref)
            if key in seen:
                continue
            seen.add(key)

            got = False
            for absu in resolve(css_rel, ref):
                if absu in seen and False:
                    continue
                try:
                    body, final = fetch(absu)
                except Exception as e:  # noqa: BLE001
                    failed.append((absu, str(e)[:60]))
                    continue

                sp = urllib.parse.urlsplit(final)
                rel_path = urllib.parse.unquote(sp.path).lstrip("/")
                if not rel_path:
                    continue
                dest = os.path.join(root, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if rel_path.endswith(".css"):
                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(body.decode("utf-8", "replace"))
                else:
                    with open(dest, "wb") as f:
                        f.write(body)

                # relative path from the css file to the new local file
                new_ref = os.path.relpath(rel_path, os.path.dirname(css_rel) or ".")
                new_ref = new_ref.replace(os.sep, "/")
                if new_ref.startswith("./"):
                    new_ref = new_ref[2:]
                replacements.setdefault(css_rel, []).append((ref, new_ref))
                downloaded += 1
                got = True
                break
            if not got:
                failed.append((f"{css_rel} :: {ref}", "unresolved"))

    # apply rewrites
    for css_rel, pairs in replacements.items():
        p = os.path.join(root, css_rel)
        txt = open(p, encoding="utf-8", errors="replace").read()
        for old, new in pairs:
            # only replace the exact ref token, preserving quotes
            txt = re.sub(
                r"(url\(\s*['\"]?)" + re.escape(old) + r"(['\"]?\s*\))",
                lambda m: m.group(1) + new + m.group(2),
                txt,
            )
        open(p, "w", encoding="utf-8").write(txt)

    print(f"css_files_scanned={len(css_files)} downloaded={downloaded} failed={len(failed)}")
    for f, e in failed[:10]:
        print("  FAIL", f, "->", e)


if __name__ == "__main__":
    main()
