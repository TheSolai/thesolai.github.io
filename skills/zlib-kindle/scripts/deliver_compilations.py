#!/usr/bin/env python3
"""Deliver the themed compilations to the Kindle address.

Each file is re-verified immediately before it is sent (magic bytes,
extension agreement, default OPF namespace, readable title/creator), then
sent to every recipient, and only then recorded in the resume file. If a
send fails the file is not marked done, so a later run retries it.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zlib_kindle as zk  # noqa: E402
import slim_epub  # noqa: E402
import recipient_config  # noqa: E402

# The mail API in front of Amazon rejects an oversized attachment with a
# 413. We do not know the exact ceiling, so rather than guess we simply
# stay well under any plausible one.
#
# This is the ceiling the builder uses too (build_new_compilations.py), so a
# file that passes the build is always deliverable without a re-slice.
MAX_ATTACHMENT_BYTES = 3_400_000

# Each step is a downscaling pass; a heavier pass is tried if the lighter
# one was not enough.
SLIM_PASSES = [
    {"threshold": 20_000, "max_edge": 700, "quality": 35},
    {"threshold": 8_000, "max_edge": 500, "quality": 25},
    {"threshold": 1, "max_edge": 380, "quality": 18},
]

COMPILATIONS = os.path.expanduser("~/Downloads/dross-books/compilations")
STATE = os.path.expanduser(
    "~/Downloads/../.openclaw/workspace/skills/zlib-kindle/state/backlog-state.json")

DELIVERIES = [
    ("The-Divine-Comedy-Dante.epub", "The Divine Comedy"),
    ("Paradise-Lost-and-Paradise-Regained-Milton.epub",
     "Paradise Lost and Paradise Regained"),
    ("The-City-of-God-Augustine.epub", "The City of God"),
    ("The-Devils-Library-Bierce-Scot-Conway.epub", "The Devil's Library"),
    ("The-Watched-Wood-Three-Panics.epub",
     "The Watched Wood: Three Narratives of the Old Gods"),
    ("Apocalypse-The-Book-of-Enoch-and-Revelation.epub",
     "Apocalypse: The Book of Enoch and The Revelation of Saint John"),
    ("Fausts-Bargain-Marlowe-and-Goethe.epub",
     "Faust's Bargain: Doctor Faustus and Faust"),
    ("The-Journey-to-the-Celestial-City.epub",
     "The Journey to the Celestial City"),
    # angels, demons, devils, heaven, hell
    ("Angels-and-Seraphim.epub", "Angels and Seraphim"),
    ("The-Hosts-of-Darkness.epub", "The Hosts of Darkness"),
    ("The-Devils-Court.epub", "The Devil's Court"),
    ("Heaven-and-Its-Wonders.epub", "Heaven and Its Wonders"),
    ("The-Vision-of-Hell.epub",
     "The Vision of Hell: Dante and the Great Controversy"),
    # complete series
    ("The-Oz-Series-Part-I-Books-1-to-6.epub",
     "The Oz Series, Part I: Books One to Six"),
    ("The-Oz-Series-Part-II-Books-7-to-12.epub",
     "The Oz Series, Part II: Books Seven to Twelve"),
    ("The-Barsoom-Chronicles.epub", "The Barsoom Chronicles"),
    ("The-Works-of-Edgar-Allan-Poe-Complete.epub",
     "The Works of Edgar Allan Poe, Complete in Five Volumes"),
    ("The-Collected-Works-of-Ambrose-Bierce.epub",
     "The Collected Works of Ambrose Bierce, Volumes One and Two"),
    ("The-Fantasy-Tales-of-Lord-Dunsany.epub",
     "The Fantasy Tales of Lord Dunsany"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", default=recipient_config.as_csv())
    ap.add_argument("--state", default=STATE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()]
    state = {"done": {}}
    if os.path.isfile(args.state):
        with open(args.state, encoding="utf-8") as fh:
            state = json.load(fh)
    state.setdefault("done", {})

    delivered = failed = skipped = 0
    for filename, subject in DELIVERIES:
        path = os.path.join(COMPILATIONS, filename)
        key = subject.lower()
        if key in state["done"]:
            print(f"  = {subject}: already sent, skipping")
            skipped += 1
            continue
        if not os.path.isfile(path):
            print(f"  ! {subject}: missing {path}", file=sys.stderr)
            failed += 1
            continue

        # Fail closed: never let Amazon see a file that has not passed the
        # same guards the Z-Library path applies.
        ok, detail = zk.preflight_book(path)
        if not ok:
            print(f"  ! refusing {subject}: {detail}", file=sys.stderr)
            failed += 1
            continue
        title, creator = zk.epub_metadata(path)
        if not title or not creator:
            print(f"  ! refusing {subject}: title/creator unreadable inside the file",
                  file=sys.stderr)
            failed += 1
            continue
        if not zk.epub_namespace_ok(path):
            print(f"  ! refusing {subject}: OPF namespace is not the default form",
                  file=sys.stderr)
            failed += 1
            continue

        if args.dry_run:
            print(f"  → would send {filename} ({os.path.getsize(path):,} bytes) "
                  f"[{title} / {creator}] -> {', '.join(to_addrs)}")
            continue

        # Send first and let the API tell us the real ceiling, rather than
        # guessing one. A 413 means the attachment was too large, so the
        # illustrations are shrunk and the send retried.
        sent_all = True
        for addr in to_addrs:
            for attempt, opts in enumerate([None] + SLIM_PASSES):
                if attempt:
                    slim_epub.slim(path, **opts)
                    # The file changed underneath us, so the guards must
                    # run again before anything is sent.
                    ok, detail = zk.preflight_book(path)
                    if not ok:
                        print(f"  ! refusing {subject} after slimming: {detail}",
                              file=sys.stderr)
                        sent_all = False
                        break
                    if not zk.epub_namespace_ok(path):
                        print(f"  ! refusing {subject} after slimming: OPF namespace changed",
                              file=sys.stderr)
                        sent_all = False
                        break
                    t2, c2 = zk.epub_metadata(path)
                    if not t2 or not c2:
                        print(f"  ! refusing {subject} after slimming: metadata unreadable",
                              file=sys.stderr)
                        sent_all = False
                        break
                    print(f"    slimmed to {os.path.getsize(path):,} bytes, retrying")
                try:
                    ok = zk.send_to_kindle(path, subject, addr)
                    if ok:
                        break
                    sent_all = False
                    break
                except Exception as exc:  # one bad send must not abort the batch
                    too_big = "413" in str(exc) or "Too Large" in str(exc)
                    if too_big and attempt < len(SLIM_PASSES):
                        print(f"    {subject} too large for {addr}; slimming and retrying",
                              file=sys.stderr)
                        continue
                    print(f"  ! {subject} -> {addr}: {type(exc).__name__}: {exc}",
                          file=sys.stderr)
                    sent_all = False
                    break
            if not sent_all:
                break
        if sent_all:
            state["done"][key] = ",".join(to_addrs)
            with open(args.state, "w", encoding="utf-8") as fh:
                json.dump(state, fh, indent=2, sort_keys=True)
            delivered += 1
            print(f"  ✓ delivered: {subject}")
        else:
            failed += 1

    if args.dry_run:
        print(f"\n=== dry run: {len(DELIVERIES)} compilations ===")
        return 0
    print(f"\n=== delivered {delivered}, failed {failed}, skipped {skipped} ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
