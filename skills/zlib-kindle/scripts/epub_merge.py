#!/usr/bin/env python3
"""Merge several EPUBs into a single compilation EPUB using only the stdlib.

Calibre's ebook-merge is not present in the Homebrew build on this machine
and ebook-convert accepts a single input, so merging is done here:

  * each source book's OPF manifest and spine are re-homed under a per-book
    prefix (vol01/, vol02/, ...) so resource files never collide;
  * the OPF is rebuilt with the *default* OPF namespace, because Amazon's
    converter silently drops packages whose root is a prefixed opf: element;
  * one navigation document (EPUB3 nav) and one NCX are generated, listing
    every volume in order, with the spine pointing at each volume's first
    document.

The result is a real book: one title, one spine, one table of contents.
"""

import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
EPUB_NS = "http://www.idpf.org/2007/ops"

ET.register_namespace("", OPF_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("epub", EPUB_NS)


def _q(ns, tag):
    return f"{{{ns}}}{tag}"


def opf_path(zf):
    """Locate the OPF path via META-INF/container.xml."""
    with zf.open("META-INF/container.xml") as fh:
        root = ET.parse(fh).getroot()
    for rf in root.iter(_q(CONTAINER_NS, "rootfile")):
        return rf.get("full-path")
    return None


def _resolve(opf_dir, href):
    """Resolve an OPF-relative href to a zip path."""
    if opf_dir:
        src = f"{opf_dir}/{href}"
    else:
        src = href
    src = src.lstrip("/")
    while "/../" in src:
        src = re.sub(r"[^/]+/\.\./", "", src, count=1)
    return src


def _volume_entries(zf, opf):
    """Return (spine_docs, resources) for one source book.

    spine_docs: list of zip paths, in spine order.
    resources:  dict zip path -> bytes, for everything the spine needs.
    """
    opf_dir = os.path.dirname(opf)
    pkg = ET.fromstring(zf.read(opf))
    manifest = pkg.find(_q(OPF_NS, "manifest"))
    spine = pkg.find(_q(OPF_NS, "spine"))

    by_id = {}
    for item in manifest.findall(_q(OPF_NS, "item")):
        by_id[item.get("id")] = {
            "href": item.get("href"),
            "media-type": item.get("media-type"),
            "properties": item.get("properties") or "",
        }

    spine_docs = []
    wanted = {}
    for ref in spine.findall(_q(OPF_NS, "itemref")):
        entry = by_id.get(ref.get("idref"))
        if not entry:
            continue
        path = _resolve(opf_dir, entry["href"])
        wanted[path] = entry
        spine_docs.append(path)

    # The stylesheet and images a document refers to are pulled in by the
    # manifest of the source book; copy the whole manifest except the
    # per-book navigation documents, which are replaced by the merged ones.
    resources = {}
    for entry in by_id.values():
        if "nav" in entry["properties"].split():
            continue
        path = _resolve(opf_dir, entry["href"])
        try:
            resources[path] = zf.read(path)
        except KeyError:
            continue
    for path in spine_docs:
        try:
            resources[path] = zf.read(path)
        except KeyError:
            pass
    return spine_docs, resources, wanted


def merge(epubs, out_path, title, author, language="en", subtitle=None):
    """Merge epubs (list of (path, volume_title, volume_author)) into out_path."""
    manifest = []
    spine = []
    resources = {}
    volumes = []

    for n, item in enumerate(epubs, 1):
        path, vol_title = item[0], item[1]
        vol_author = item[2] if len(item) > 2 else author
        prefix = f"vol{n:02d}"
        with zipfile.ZipFile(path) as zf:
            opf = opf_path(zf)
            if not opf:
                raise SystemExit(f"{path}: no OPF found")
            spine_docs, book_resources, _ = _volume_entries(zf, opf)
        if not spine_docs:
            raise SystemExit(f"{path}: empty spine")

        first = None
        for doc in spine_docs:
            new_href = f"{prefix}/{doc}"
            media = "application/xhtml+xml"
            if doc.lower().endswith(".html"):
                media = "text/html"
            elif doc.lower().endswith(".htm"):
                media = "text/html"
            item_id = f"{prefix}-d{len(manifest):03d}"
            manifest.append({"id": item_id, "href": new_href, "media-type": media})
            spine.append(item_id)
            if first is None:
                first = new_href
            resources[new_href] = book_resources[doc]

        # Copy the rest of the book's resources under the prefix.
        for doc, data in book_resources.items():
            if doc in spine_docs:
                continue
            new_href = f"{prefix}/{doc}"
            if new_href in resources:
                continue
            media = None
            if doc.lower().endswith((".jpg", ".jpeg")):
                media = "image/jpeg"
            elif doc.lower().endswith(".png"):
                media = "image/png"
            elif doc.lower().endswith(".gif"):
                media = "image/gif"
            elif doc.lower().endswith(".svg"):
                media = "image/svg+xml"
            elif doc.lower().endswith(".css"):
                media = "text/css"
            elif doc.lower().endswith(".ncx"):
                continue
            elif doc.lower().endswith((".xhtml", ".html", ".htm")):
                media = "application/xhtml+xml"
            resources[new_href] = data
            if media:
                manifest.append({"id": f"{prefix}-r{len(manifest):03d}",
                                 "href": new_href, "media-type": media})

        volumes.append({"title": vol_title, "author": vol_author, "href": first})

    # ---- package document -------------------------------------------------
    pkg = ET.Element(_q(OPF_NS, "package"),
                     {"version": "3.0", "unique-identifier": "bookid"})
    md = ET.SubElement(pkg, _q(OPF_NS, "metadata"))
    ET.SubElement(md, _q(DC_NS, "identifier"), {"id": "bookid"}).text = \
        "urn:uuid:dross-compilation"
    ET.SubElement(md, _q(DC_NS, "title")).text = title
    if subtitle:
        ET.SubElement(md, _q(DC_NS, "subtitle")).text = subtitle
    ET.SubElement(md, _q(DC_NS, "creator")).text = author
    ET.SubElement(md, _q(DC_NS, "language")).text = language
    ET.SubElement(md, _q(OPF_NS, "meta"), {"property": "dcterms:modified"}).text = \
        "2026-10-29T00:00:00Z"

    man = ET.SubElement(pkg, _q(OPF_NS, "manifest"))
    ET.SubElement(man, _q(OPF_NS, "item"), {
        "id": "nav", "href": "nav.xhtml", "media-type": "application/xhtml+xml",
        "properties": "nav"})
    ET.SubElement(man, _q(OPF_NS, "item"), {
        "id": "ncx", "href": "toc.ncx", "media-type": "application/x-dtbncx+xml"})
    for entry in manifest:
        ET.SubElement(man, _q(OPF_NS, "item"), entry)
    sp = ET.SubElement(pkg, _q(OPF_NS, "spine"), {"toc": "ncx"})
    for item_id in spine:
        ET.SubElement(sp, _q(OPF_NS, "itemref"), {"idref": item_id})

    # ---- navigation -------------------------------------------------------
    nav_html = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!DOCTYPE html>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">',
        "<head><title>" + _esc(title) + "</title></head><body>",
        '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>',
    ]
    for vol in volumes:
        nav_html.append(
            f'<li><a href="{_esc(vol["href"])}">{_esc(vol["title"])}</a></li>')
    nav_html.append("</ol></nav></body></html>")

    ncx = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
        "<head><meta name=\"dtb:uid\" content=\"urn:uuid:dross-compilation\"/>",
        f"<meta name=\"dtb:title\" content=\"{_esc(title)}\"/>",
        f"<meta name=\"dtb:author\" content=\"{_esc(author)}\"/>",
        "<meta name=\"dtb:depth\" content=\"1\"/>",
        "<meta name=\"dtb:totalPageCount\" content=\"0\"/>",
        "<meta name=\"dtb:maxPageNumber\" content=\"0\"/></head>",
        "<docTitle><text>" + _esc(title) + "</text></docTitle>",
        "<navMap>",
    ]
    for order, vol in enumerate(volumes, 1):
        ncx.append(
            f'<navPoint id="np{order}" playOrder="{order}">'
            f'<navLabel><text>{_esc(vol["title"])}</text></navLabel>'
            f'<content src="{_esc(vol["href"])}"/></navPoint>')
    ncx.append("</navMap></ncx>")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<container version="1.0" '
                    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                    '<rootfiles><rootfile full-path="content.opf" '
                    'media-type="application/oebps-package+xml"/></rootfiles>'
                    '</container>')
        zf.writestr("content.opf",
                    '<?xml version="1.0" encoding="utf-8"?>\n'
                    + ET.tostring(pkg, encoding="unicode"))
        zf.writestr("nav.xhtml", "\n".join(nav_html))
        zf.writestr("toc.ncx", "\n".join(ncx))
        for name, data in resources.items():
            zf.writestr(name, data)
    return out_path


def _esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("usage: epub_merge.py OUT TITLE AUTHOR EPUB [EPUB ...]")
        raise SystemExit(2)
    out, title, author = sys.argv[1], sys.argv[2], sys.argv[3]
    files = sys.argv[4:]
    merge([(f, os.path.splitext(os.path.basename(f))[0]) for f in files],
          out, title, author)
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")
