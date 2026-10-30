#!/usr/bin/env python3
"""Deliver the themed compilations and the single-recipient gap files.

Two properties this script has that the Z-Library job does not need:

* It is CAP-AWARE. The AgentMail account has a hard ceiling of 100 sends
  per UTC day and the service enforces it. Rather than discover the
  ceiling by being rejected mid-batch, the script reads the live sent
  log before every send and stops cleanly, with its state intact, when
  the day's budget is gone. A clean stop is exit code 3.

* It is GAP-AWARE. A file that only one recipient still needs is sent to
  that recipient alone, and a recipient that already has a file is never
  sent it again. The recipient list recorded in the state file is the
  set that actually received the file, so a partial delivery is
  resumable and a completed one is never repeated.

Each file is re-verified immediately before it is sent: magic bytes,
extension agreement, default OPF namespace, and readable title/creator
metadata. A file that fails is never sent, because Amazon accepts a bad
file silently.

Exit codes:
    0: everything requested was delivered.
    1: some files failed.
    3: the daily send cap was reached; the state file is intact and the
       next run resumes where this one stopped.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zlib_kindle as zk  # noqa: E402
import slim_epub  # noqa: E402
import send_cap  # noqa: E402
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
LIBRARY = os.path.expanduser("~/Downloads/dross-books")
STATE = os.path.expanduser(
    "~/Downloads/../.openclaw/workspace/skills/zlib-kindle/state/backlog-state.json")

# The two delivery addresses are read at run time from an untracked
# local config file. They are deliberately not written here: the publish
# gate refuses to publish a tree containing an address that appears
# under secrets/, and reading them at run time keeps that literal out of
# the source without weakening the gate. See recipient_config.py.
KINDLE, GMAIL = recipient_config.load()

# The compilations, in the order they were built. The subject is the
# state key, so it must not change once a file has been delivered.
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
    # complete series, second wave: the rest of Oz, and the sagas
    ("The-Oz-Series-Part-III-Books-13-to-14.epub",
     "The Oz Series, Part III: Books Thirteen and Fourteen"),
    ("The-Later-Oz-Books.epub",
     "The Later Oz Books: The Scarecrow, the Royal Book, Glinda and the Woggle-Bug"),
    ("The-Pellucidar-Series.epub", "The Pellucidar Series"),
    ("The-Mahabharata-Part-I-Volumes-1-to-2.epub",
     "The Mahabharata, Part I: Volumes One and Two"),
    ("The-Mahabharata-Part-II-Volumes-3-to-4.epub",
     "The Mahabharata, Part II: Volumes Three and Four"),
    ("The-Decline-and-Fall-Volumes-1-to-2.epub",
     "The Decline and Fall of the Roman Empire, Part I: Volumes One and Two"),
    ("The-Decline-and-Fall-Volumes-3-to-4.epub",
     "The Decline and Fall of the Roman Empire, Part II: Volumes Three and Four"),
    ("The-Decline-and-Fall-Volumes-5-to-6.epub",
     "The Decline and Fall of the Roman Empire, Part III: Volumes Five and Six"),
    ("The-History-of-Herodotus.epub", "The History of Herodotus"),
    ("The-Norse-Sagas-and-Tales.epub", "The Norse Sagas and Tales"),
    ("The-Golden-Bough-Volumes-1-to-3.epub",
     "The Golden Bough, Part I: Volumes One to Three"),
    ("The-Golden-Bough-Volumes-4-to-6.epub",
     "The Golden Bough, Part II: Volumes Four to Six"),
    ("The-Golden-Bough-Volumes-7-to-9.epub",
     "The Golden Bough, Part III: Volumes Seven to Nine"),
    ("The-Golden-Bough-Volumes-10-to-12.epub",
     "The Golden Bough, Part IV: Volumes Ten to Twelve"),
    ("The-Thousand-Nights-and-a-Night-Volumes-1-to-5.epub",
     "The Book of the Thousand Nights and a Night, Part I: Volumes One to Five"),
    ("The-Thousand-Nights-and-a-Night-Volumes-6-to-10.epub",
     "The Book of the Thousand Nights and a Night, Part II: Volumes Six to Ten"),
    ("The-Thousand-Nights-and-One-Night.epub",
     "The Book of the Thousand Nights and One Night"),
    ("The-Ghostly-Tales-of-Le-Fanu.epub",
     "The Ghostly Tales of Joseph Sheridan Le Fanu"),
    ("In-a-Glass-Darkly.epub", "In a Glass Darkly"),
    ("The-Purcell-Papers.epub", "The Purcell Papers"),
    ("The-Tenants-of-Malory.epub", "The Tenants of Malory"),
    ("Le-Morte-dArthur.epub", "Le Morte d'Arthur"),
    ("The-Mabinogion.epub", "The Mabinogion"),
    ("Kalevala-The-Land-of-the-Heroes.epub",
     "Kalevala, the Land of the Heroes"),
    ("The-Decameron.epub", "The Decameron"),
    ("The-Faerie-Queene.epub", "The Faerie Queene"),
    ("The-Fairy-Tales-of-Hans-Andersen.epub",
     "The Fairy Tales of Hans Christian Andersen"),
    ("Ghost-Stories-of-an-Antiquary.epub", "Ghost Stories of an Antiquary"),
    ("The-Persian-Literature.epub", "The Persian Literature"),
    ("Faust-Der-Tragoedie-Complete.epub",
     "Faust: Der Tragodie, Parts One and Two"),
    ("The-History-of-Greece-Volumes-1-to-3.epub",
     "The History of Greece, Volumes One to Three"),
    ("The-History-of-Greece-Volumes-4-to-6.epub",
     "The History of Greece, Volumes Four to Six"),
    ("The-History-of-Greece-Volumes-7-to-9.epub",
     "The History of Greece, Volumes Seven to Nine"),
    ("The-History-of-Greece-Volumes-10-to-12.epub",
     "The History of Greece, Volumes Ten to Twelve"),
    ("The-Ramayana-Volumes-1-to-2.epub",
     "The Ramayana, Volumes One and Two"),
    ("The-Ramayana-Volumes-3-to-4.epub",
     "The Ramayana, Volumes Three and Four"),
    ("The-Maharamayana-Volumes-1-to-2.epub",
     "The Maharamayana of Valmiki, Volumes One and Two"),
    ("The-Maharamayana-Volumes-3-to-4.epub",
     "The Maharamayana of Valmiki, Volumes Three and Four"),
    # the final five, built from the seven sources the coverage sweep
    # found uncovered by anything already sent
    ("The-Kalevala.epub", "The Kalevala: The Epic Poem of Finland"),
    ("Fairy-Tales-and-Ghost-Stories.epub",
     "Hans Andersen's Fairy Tales and The Ghost Stories of M. R. James"),
    ("Faust-in-English-Part-One.epub", "Faust, Part One in English"),
    ("The-Poetical-Works-of-John-Milton.epub",
     "The Poetical Works of John Milton"),
    ("The-Complete-Works-of-William-Shakespeare.epub",
     "The Complete Works of William Shakespeare"),
    # the five new series sets, built from the sources the second sweep
    # found uncovered by anything already sent
    ("Trollope-Barsetshire-Chronicles-Part-One.epub",
     "The Barsetshire Chronicles, Part One: The Warden, Barchester Towers and Doctor Thorne"),
    ("Trollope-Barsetshire-Chronicles-Part-Two.epub",
     "The Barsetshire Chronicles, Part Two: Framley Parsonage, The Small House at Allington and The Last Chronicle of Barset"),
    ("Dumas-dArtagnan-Cycle-Part-One.epub",
     "The d'Artagnan Cycle, Part One: The Three Musketeers and Ten Years Later"),
    ("Dumas-dArtagnan-Cycle-Part-Two.epub",
     "The d'Artagnan Cycle, Part Two: Twenty Years After, The Vicomte de Bragelonne and Louise de la Valliere"),
    ("Lytton-The-Works-Part-One.epub",
     "The Works of Edward Bulwer-Lytton, Part One: Athens, Eugene Aram, My Novel and Night and Morning"),
    ("Lytton-The-Works-Part-Two.epub",
     "The Works of Edward Bulwer-Lytton, Part Two: The Caxtons and Zicci"),
    ("Tarzan-The-Complete-Series-Volumes-One-to-Six.epub",
     "Tarzan: The Complete Series, Volumes One to Six"),
    ("Tarzan-The-Complete-Series-Volumes-Seven-to-Twelve.epub",
     "Tarzan: The Complete Series, Volumes Seven to Twelve"),
    ("Tarzan-The-Complete-Series-Volumes-Thirteen-to-Eighteen.epub",
     "Tarzan: The Complete Series, Volumes Thirteen to Eighteen"),
    ("Dumas-Celebrated-Crimes-Complete.epub",
     "Celebrated Crimes, Complete"),
    ("Zola-The-Three-Cities.epub",
     "The Three Cities Trilogy, Complete: Lourdes, Rome and Paris"),
]

# Files that only one recipient is still missing, or that a recipient
# never received at all. Ordered by how empty the gap is: a recipient
# that has no copy of the work at all comes first.
#
#   (filename, subject, recipients)
#
# The state key is prefixed with "gap:" so it can never collide with a
# title key written by the Z-Library job, which shares this state file.
GAPS = [
    ("The-King-in-Yellow-Chambers.epub", "The King in Yellow", [GMAIL]),
    ("The-Fisherman-by-John-Langan.epub", "The Fisherman", [GMAIL]),
    ("NOS4A2-by-Joe-Hill.epub", "NOS4A2", [GMAIL]),
    # No repaired Haunting entry on purpose. Both recipients already hold
    # The-Haunting-of-Hill-House.epub (2026-10-29T19:50), and that file's
    # single content part is well-formed XHTML with a valid two-item spine
    # and no prefixed opf: root, so Amazon renders it. Sending the
    # repaired original as well would duplicate a book both sides have.
    ("Boccaccio-Decameron-Complete.epub", "The Decameron, Complete",
     [KINDLE, GMAIL]),
]


# ------------------------------------------------------------------ state --
def load_state(path):
    state = {"done": {}}
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                state = json.load(fh)
        except (OSError, ValueError):
            state = {"done": {}}
    state.setdefault("done", {})
    return state


def save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


def recipients_done(state, key):
    """The set of recipients that already received this state key."""
    raw = state["done"].get(key) or ""
    if isinstance(raw, list):
        return {a.strip() for a in raw if a.strip()}
    return {a.strip() for a in str(raw).split(",") if a.strip()}


def mark_done(state, key, addr):
    have = recipients_done(state, key)
    have.add(addr)
    state["done"][key] = ",".join(sorted(have))


# -------------------------------------------------------------- delivery --
def verify(path, subject):
    """Fail-closed checks run immediately before anything is sent.

    Returns (ok, reason). The reason on success is the real format.
    """
    ok, detail = zk.preflight_book(path)
    if not ok:
        return False, detail
    if not zk.epub_namespace_ok(path):
        return False, "OPF namespace is not the default form"
    title, creator = zk.epub_metadata(path)
    if not title or not creator:
        return False, "title/creator unreadable inside the file"
    return True, detail


def send_one(path, subject, addr):
    """Send one file to one recipient, re-verifying it first.

    An oversized file is slimmed on a COPY, never on the library file:
    the original EPUB on disk is left exactly as it was found.
    """
    ok, detail = verify(path, subject)
    if not ok:
        print(f"  ! refusing {subject} -> {addr}: {detail}", file=sys.stderr)
        return False

    work = path
    tmpdir = None
    try:
        if os.path.getsize(path) > MAX_ATTACHMENT_BYTES:
            # A copy is slimmed; the library file is never rewritten.
            tmpdir = tempfile.mkdtemp(prefix="dross-slim-")
            work = os.path.join(tmpdir, os.path.basename(path))
            shutil.copy2(path, work)
            for opts in SLIM_PASSES:
                slim_epub.slim(work, **opts)
                ok, detail = verify(work, subject)
                if not ok:
                    print(f"  ! refusing {subject} after slimming: {detail}",
                          file=sys.stderr)
                    return False
                if os.path.getsize(work) <= MAX_ATTACHMENT_BYTES:
                    break
                print(f"    still {os.path.getsize(work):,} bytes, slimming again")
            else:
                print(f"  ! {subject} -> {addr}: still over "
                      f"{MAX_ATTACHMENT_BYTES:,} bytes after slimming",
                      file=sys.stderr)
                return False
            print(f"    slimmed copy to {os.path.getsize(work):,} bytes")

        try:
            return zk.send_to_kindle(work, subject, addr)
        except Exception as exc:
            print(f"  ! {subject} -> {addr}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            return False
    finally:
        if tmpdir and os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)


def remaining_budget(day=None):
    """How many sends are left in the current UTC day."""
    import datetime as dt
    day = day or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    sent = send_cap.sent_messages()
    total, _ = send_cap.count_day(sent, day)
    return max(0, send_cap.CAP - total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", default=f"{KINDLE},{GMAIL}")
    ap.add_argument("--state", default=STATE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=("all", "gaps", "compilations"),
                    default="all")
    ap.add_argument("--budget", type=int, default=0,
                    help="stop after this many sends in this run")
    args = ap.parse_args()

    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()]
    state = load_state(args.state)

    delivered = failed = skipped = 0
    spent = 0
    capped = False

    # The gap files come first: a recipient that has no copy of a work at
    # all is a bigger hole than a compilation that is merely undelivered.
    jobs = []
    if args.only in ("all", "gaps"):
        for filename, subject, recipients in GAPS:
            jobs.append(("gap:" + filename, subject,
                         os.path.join(LIBRARY, filename), recipients))
    if args.only in ("all", "compilations"):
        for filename, subject in DELIVERIES:
            jobs.append((subject.lower(), subject,
                         os.path.join(COMPILATIONS, filename), to_addrs))

    for key, subject, path, recipients in jobs:
        have = recipients_done(state, key)
        want = [a for a in recipients if a not in have]
        if not want:
            print(f"  = {subject}: every recipient already has it, skipping")
            skipped += 1
            continue

        if not os.path.isfile(path):
            print(f"  ! {subject}: missing {path}", file=sys.stderr)
            failed += 1
            continue

        if args.dry_run:
            print(f"  → would send {os.path.basename(path)} "
                  f"({os.path.getsize(path):,} bytes) -> {', '.join(want)}")
            continue

        for addr in want:
            # Ask the live sent log how much budget is left before every
            # send, so the day's ceiling is never discovered by being
            # rejected mid-batch.
            left = remaining_budget()
            if left <= 0:
                print(f"  ! daily send cap reached; stopping with state intact")
                capped = True
                break
            if args.budget and spent >= args.budget:
                print(f"  ! run budget of {args.budget} send(s) reached")
                capped = True
                break

            if send_one(path, subject, addr):
                mark_done(state, key, addr)
                save_state(args.state, state)
                delivered += 1
                spent += 1
                print(f"  ✓ delivered: {subject} -> {addr}")
            else:
                failed += 1
                break
        if capped:
            break

    if args.dry_run:
        print(f"\n=== dry run: {len(jobs)} job(s) ===")
        return 0

    if capped:
        print(f"\n=== delivered {delivered}, failed {failed}, skipped {skipped}, "
              f"stopped: daily send cap ===")
        return 3
    print(f"\n=== delivered {delivered}, failed {failed}, skipped {skipped} ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
