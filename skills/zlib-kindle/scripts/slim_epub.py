#!/usr/bin/env python3
"""Shrink the images inside an EPUB in place (same paths, same formats).

Amazon's Send-to-Kindle email and the mail API in front of it both cap the
size of an attachment, so a compilation whose illustrations are scanned at
full resolution can be too large to deliver at all. Downscaling the images
keeps every illustration and every word of text, and brings the file back
under the ceiling.

Only the bytes change: paths, formats and the manifest stay exactly as they
were, so nothing in the book can break. macOS `sips` does the resizing;
no Python imaging library is required.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

# Only images above this size are worth a resize; a small icon costs
# nothing and gains nothing from re-encoding.
THRESHOLD = 60_000
MAX_EDGE = 1000
JPEG_QUALITY = 45
# Palette entries for PNG re-quantisation. Scanned line-art plates reduce
# to this without visible loss and get far smaller.
PNG_COLORS = 64
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".gif")


def slim_bytes(name, data, workdir, max_edge=MAX_EDGE, quality=JPEG_QUALITY,
               colors=PNG_COLORS):
    """Return possibly-resized image bytes, or None to keep the original.

    ImageMagick does the work. It is used rather than `sips` because `sips`
    re-encodes a palette PNG at a larger size than it started with, which
    would make the book bigger rather than smaller. The file keeps its
    original path and original format, so every reference inside the book
    still resolves.
    """
    ext = os.path.splitext(name)[1].lower()
    if ext not in IMAGE_EXT:
        return None
    src = os.path.join(workdir, "in" + ext)
    dst = os.path.join(workdir, "out" + ext)
    with open(src, "wb") as fh:
        fh.write(data)

    if ext in (".jpg", ".jpeg"):
        cmd = ["magick", src, "-auto-orient", "-resize", f"{max_edge}x{max_edge}>",
               "-strip", "-interlace", "Plane", "-sampling-factor", "4:2:0",
               "-quality", str(quality), dst]
    else:
        # PNG stays PNG (the book references .png paths). Palette-reduce and
        # re-deflate rather than re-encode losslessly.
        cmd = ["magick", src, "-auto-orient", "-resize", f"{max_edge}x{max_edge}>",
               "-strip", "-colors", str(colors), "-define",
               "png:compression-level=9", "-define", "png:compression-filter=5",
               f"PNG8:{dst}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not os.path.isfile(dst):
        return None
    with open(dst, "rb") as fh:
        out = fh.read()
    if not out or len(out) >= len(data):
        return None
    return out


def slim(path, target_bytes=None, threshold=THRESHOLD, max_edge=MAX_EDGE,
         quality=JPEG_QUALITY, colors=PNG_COLORS):
    """Rewrite `path` with downscaled images. Returns (new size, count)."""
    with zipfile.ZipFile(path) as zf:
        entries = [(i, zf.read(i.filename)) for i in zf.infolist()]

    shrunk = 0
    with tempfile.TemporaryDirectory() as workdir:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for info, data in entries:
                if info.filename == "mimetype":
                    zf.writestr("mimetype", data, zipfile.ZIP_STORED)
                    continue
                if info.file_size >= threshold:
                    out = slim_bytes(info.filename, data, workdir, max_edge,
                                     quality, colors)
                    if out is not None:
                        data = out
                        shrunk += 1
                zf.writestr(info.filename, data)

    size = os.path.getsize(path)
    if target_bytes and size > target_bytes:
        print(f"  ! {os.path.basename(path)} still {size:,} bytes "
              f"(target {target_bytes:,})", file=sys.stderr)
    return size, shrunk


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--threshold", type=int, default=THRESHOLD)
    ap.add_argument("--max-edge", type=int, default=MAX_EDGE)
    ap.add_argument("--quality", type=int, default=JPEG_QUALITY)
    ap.add_argument("--colors", type=int, default=PNG_COLORS)
    args = ap.parse_args()

    for target in args.files:
        before = os.path.getsize(target)
        after, n = slim(target, threshold=args.threshold, max_edge=args.max_edge,
                        quality=args.quality, colors=args.colors)
        print(f"{os.path.basename(target)}: {before:,} -> {after:,} bytes "
              f"({n} images resized)")
