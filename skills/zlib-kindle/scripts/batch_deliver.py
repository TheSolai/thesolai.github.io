#!/usr/bin/env python3
"""Deliver a curated list of books to the Kindle address via ONE Z-Library login.

Why this exists: every zlib_kindle.py command performs one sign-in, and the
account is rate-limited on sign-ins. Running `deliver` once per title would
mean one login per book, which trips the limit and blocks the real delivery.
So the whole batch runs inside one process, one login, one session.

The book-level rules are NOT reimplemented here. Search, row normalisation,
title/author matching, download, the delivery guards (preflight_book,
repair_epub_namespace, calibre_convert) and the AgentMail send all come from
zlib_kindle, so this file cannot drift away from the verified path.

It adds only what a batch needs:
  * a curated list carrying the title and author actually asked for;
  * an accent-tolerant scorer for choosing the right Z-Library row;
  * a preference for EPUB rows, since the Scribe cannot open MOBI/AZW3;
  * a resume file, so a re-run skips whatever already went out;
  * an honest per-book report.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bounded  # noqa: E402
import zlib_kindle as zk  # noqa: E402

# The uncapped run output is written here as well, so nothing is lost for
# auditing even though the chat only ever sees the bounded version.
LOG_PATH = os.path.expanduser(
    "~/Downloads/../.openclaw/workspace/skills/zlib-kindle/state/batch-deliver.log")


# --------------------------------------------------------------------------
# Picking the right row
#
# The curated list knows the book that was asked for. Z-Library rows carry an
# "Author - Title" string that has been split, an author that may be
# "Moorcock, Michael" or "Michael Moorcock", and titles carrying subtitles,
# volume numbers and "Complete Collection" bundles. A plain substring test
# picks the wrong row constantly, so score on token sets with accents folded
# away ("Melniboné" and "Melnibone" are the same book).
# --------------------------------------------------------------------------

BUNDLE_WORDS = ("collection", "omnibus", "box set", "boxset", "boxed set",
                "complete works", "anthology", "complete collection",
                "collected adventures", "complete edition", "all the novels",
                "every novel", "the complete", "saga part")

# A bracketed range like "[01-03]" marks a multi-book omnibus even when the
# title contains no bundle word ("Chronicles of the Black Company [01-03]").
BUNDLE_RANGE_RE = re.compile(r"\[\s*\d{1,2}\s*[-–—]\s*\d{1,2}\s*\]")

STOPWORDS = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for",
             "book", "volume", "vol", "part", "novel", "tale", "tales"}


def fold(text):
    """Lowercase, strip accents, collapse to word tokens."""
    if not text:
        return set()
    plain = unicodedata.normalize("NFKD", str(text))
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return set(re.findall(r"[a-z0-9]+", plain.lower()))


def distinctive(tokens):
    """The tokens that actually identify a title, minus filler words."""
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


VOLUME_RE = re.compile(
    r"(?:^|\s|\[|#|:|-)(?:book|vol|volume|part|no\.?|number)?\s*(\d{1,2})(?:\s|\]|:|-|$)"
    r"|#\s*(\d{1,2})\b|\b(\d{1,2})\s*:\s|\bseries\s+(\d{1,2})\b",
    re.I,
)


def volume_number(text):
    """Extract a series/volume number from a title, or None.

    Used to prefer book 1 over book 2 when both match the same request.
    """
    if not text:
        return None
    m = VOLUME_RE.search(text)
    if not m:
        return None
    for group in m.groups():
        if group:
            try:
                num = int(group)
            except ValueError:
                continue
            if 0 < num < 40:
                return num
    return None


def title_ok(want_title, row_title, relaxed=False):
    """True when a row's title denotes the book that was requested.

    Strict mode: the requested title's tokens must be contained in the row's
    title (or the reverse, for a subtitle on the wanted side).

    Relaxed mode is the fallback for when nothing matched strictly. It allows
    a bundle ("Conan the Barbarian: The Complete Collection") but only if
    every distinctive token of the requested title is present in it. That
    still cannot match a different book, because the distinctive words have
    to match; it only stops the check being brittle about packaging.
    """
    want = fold(want_title)
    got = fold(row_title)
    if not want or not got:
        return False
    hay = " ".join(sorted(got))
    is_bundle = any(word in hay for word in BUNDLE_WORDS)
    if want <= got or got <= want:
        return True
    if relaxed and is_bundle:
        return bool(distinctive(want)) and distinctive(want) <= got
    # Tolerate a subtitle on the wanted side ("Prince of Thorns" vs
    # "Prince of Thorns (The Broken Empire, #2)").
    return len(got - want) <= 2


def row_matches(row, want_title, want_author):
    """True when a row denotes the requested book.

    Z-Library's eAPI splits "Author - Title" and occasionally puts the TITLE
    in the author field ("The Shadow Campaigns 01" with author "The Thousand
    Names"), so a title is allowed to be found in either field, and the
    author is allowed to be found in either field too.
    """
    title_tokens = fold(row.get("title"))
    author_tokens = fold(row.get("author"))
    hay = title_tokens | author_tokens

    want_t = fold(want_title)
    want_a = fold(want_author) if want_author else set()

    title_found = bool(want_t) and (want_t <= title_tokens or want_t <= author_tokens)
    if not title_found:
        return False
    if not want_a:
        return True
    return (want_a <= author_tokens or want_a <= title_tokens
            or names_match(want_author, row.get("author"))
            or names_match(want_author, row.get("title")))


def names_match(want, got):
    """True when two names denote the same thing, ignoring order.

    "Joe Hill" and "Hill, Joe" are the same author, so compare token sets.
    """
    a, b = fold(want), fold(got)
    if not a or not b:
        return False
    return a == b or a <= b or b <= a


def pick_row(rows, want_title, want_author):
    """Best row for a requested book.

    Ranking, in order:
      1. a single book beats a bundle (the dry run showed a 3-book bundle
         winning over the single book it contained);
      2. book 1 beats book 2 (a request for "The Shadow Campaigns" was
         picking "The Shadow Campaigns 2: The Shadow Throne");
      3. the closest title wins, measured by token overlap: an exact title
         beats a subtitled or series-annotated one;
      4. EPUB beats MOBI/AZW3, because the Scribe cannot open those;
      5. a row carrying a hash wins, since a bare id cannot resolve a file.
    """
    best = None
    best_score = None
    want_t = fold(want_title)
    for row in rows:
        if not row_matches(row, want_title, want_author):
            continue
        title = row.get("title") or ""
        title_tokens = fold(title)

        hay = " ".join(sorted(title_tokens))
        is_bundle = 1 if (any(word in hay for word in BUNDLE_WORDS)
                          or BUNDLE_RANGE_RE.search(title)) else 0
        vol = volume_number(title)
        vol_penalty = 0 if vol in (None, 1) else 1

        # Overlap: how much of the wanted title the row carries, penalised
        # by the extra words the row adds. 1.0 is an exact title match.
        union = want_t | title_tokens
        overlap = len(want_t & title_tokens) / len(union) if union else 0.0

        ext = (row.get("extension") or "").lower()
        fmt_rank = zk.KINDLE_FORMAT_RANK.get(ext, 9)
        score = (is_bundle, vol_penalty, -round(overlap, 4), fmt_rank,
                 0 if row.get("hash") else 1)
        if best_score is None or score < best_score:
            best, best_score = row, score
    return best


# --------------------------------------------------------------------------
# Batch
# --------------------------------------------------------------------------

def load_state(path):
    if not os.path.isfile(path):
        return {"done": {}}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {"done": {}}
    data.setdefault("done", {})
    return data


def save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)


class QuotaExhausted(Exception):
    """Raised when Z-Library refuses a download because the daily cap is hit.

    The refusal is not a per-book failure: no later book in the batch will
    download either. The batch stops and leaves the resume file intact, so
    the next run picks up exactly where this one left off.
    """

    def __init__(self, reason: str, remaining: int):
        super().__init__(reason)
        self.reason = reason
        self.remaining = remaining


def deliver_one(opener, want_title, want_author, to_addrs, subject=None,
                library_dir=None, log=print, remaining=0):
    """Search, pick, download, verify and send one book.

    Returns (ok, message).
    """
    library_dir = library_dir or zk.LIBRARY_DIR

    # Two searches: the general one finds the book, the EPUB-filtered one
    # finds the edition the Scribe can actually open.
    rows = zk.zlib_search(want_title, limit=12, opener=opener)
    epub_rows = zk.zlib_search(want_title, limit=12, opener=opener,
                               extensions=["epub"])

    # Prefer an EPUB row above everything else: the Scribe cannot open
    # MOBI or AZW3, so a non-EPUB hit is a fallback, not a first choice.
    pick = pick_row(epub_rows, want_title, want_author)
    if pick is None:
        pick = pick_row(rows, want_title, want_author)
    if pick is None:
        return False, f"no Z-Library row matched {want_title!r}"

    if not pick.get("hash"):
        return False, f"row {pick.get('id')} has no hash; cannot resolve a file"

    files = zk.zlib_files(opener, pick["id"], pick.get("hash", ""))
    if not files:
        reason = zk.LAST_REFUSAL_REASON
        if zk.quota_exhausted(reason):
            raise QuotaExhausted(reason, remaining)
        return False, ("Z-Library withheld the download link "
                       "(daily cap reached, or no file offered)")

    files.sort(key=lambda f: zk.KINDLE_FORMAT_RANK.get(f.get("extension", ""), 9))
    chosen = files[0]
    ext = (chosen.get("extension") or pick.get("extension") or "epub").lower()

    subject = subject or want_title
    dest = os.path.join(library_dir, f"{zk.safe_name(subject)}.{ext}")
    if not zk.download_file(opener, chosen["url"], dest):
        return False, f"download failed for {subject!r}"
    dest = zk.retarget_ext(dest)
    if not os.path.isfile(dest):
        return False, f"file vanished after download: {dest}"
    size = os.path.getsize(dest)
    if size == 0:
        return False, f"downloaded file is empty: {dest}"
    log(f"  ✓ {size} bytes -> {os.path.basename(dest)}")

    # The row's own title is the expectation: this catches the failure that
    # bites hardest, where the server serves a different book than the row
    # advertised. The author was already checked against the curated list
    # when the row was picked; inside the file a MISMATCH is fatal, but a
    # missing creator is only a warning, because plenty of good EPUBs
    # simply do not carry one and refusing them would lose real books.
    expect_title = pick.get("title") or want_title
    if not zk.verify_book(dest, expect_title, None):
        return False, f"title in {os.path.basename(dest)} is not the requested book"
    creator = zk.epub_metadata(dest)[1] if dest.lower().endswith(".epub") else ""
    if creator and want_author and not names_match(want_author, creator):
        return False, f"author in file is {creator!r}, wanted {want_author!r}"
    if want_author and not creator:
        log(f"  · file states no author; row author {creator or want_author!r} "
            f"accepted on the row's word")

    ready, ok, notes = zk.ensure_kindle_ready(dest, expect_title, None,
                                             fallbacks=("pdf",))
    for note in notes:
        log(f"  · {note}")
    if not ok:
        return False, (f"refusing to send {os.path.basename(dest)}: "
                       f"{notes[-1] if notes else 'unknown reason'}")

    for addr in to_addrs:
        if not zk.send_to_kindle(ready, subject, addr):
            return False, f"send to {addr} failed for {subject!r}"
    return True, f"{os.path.basename(ready)} ({size} bytes) -> {', '.join(to_addrs)}"


def main():
    ap = argparse.ArgumentParser(description="Batch-deliver a curated book list.")
    ap.add_argument("--list", required=True,
                    help="JSON file: [{title, author, subject?}, ...]")
    ap.add_argument("--to", required=True,
                    help="comma-separated destination addresses")
    ap.add_argument("--state", required=True, help="resume file (JSON)")
    ap.add_argument("--dry-run", action="store_true",
                    help="search and report matches, download nothing")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N books delivered in this run")
    args = ap.parse_args()

    # The run output is announced to a chat. It is bounded here, inside the
    # script, so a long backlog, a verbose search, or a noisy failure can
    # never turn one run into a flood. The capture also covers the lines
    # printed by the shared zlib_kindle helpers, which do not go through
    # this module's own prints.
    with bounded.Bounded(log_path=LOG_PATH) as cap:
        rc, verdict = _run(args)
    cap.emit(verdict)
    return rc


def _run(args):
    with open(args.list, encoding="utf-8") as fh:
        books = json.load(fh)
    to_addrs = [a.strip() for a in args.to.split(",") if a.strip()]
    state = load_state(args.state)

    opener = zk.make_session()
    logged_in = zk.zlib_login(opener)
    if not logged_in:
        print("  ! zlib: sign-in failed; cannot resolve download links",
              file=sys.stderr)
        return 2, "=== could not start: zlib sign-in failed ==="
    print(f"  · zlib: signed in; {len(books)} titles queued")

    delivered = failed = skipped = 0
    quota_stopped = False
    for book in books:
        title = book.get("title")
        author = book.get("author")
        key = title.lower()
        if key in state["done"]:
            print(f"  = {title}: already sent, skipping")
            skipped += 1
            continue
        if args.limit and delivered >= args.limit:
            print(f"  · stopping: reached --limit {args.limit}")
            break

        print(f"\n→ {title}" + (f" — {author}" if author else ""))
        if args.dry_run:
            rows = zk.zlib_search(title, limit=6, opener=opener)
            epub_rows = zk.zlib_search(title, limit=6, opener=opener,
                                       extensions=["epub"])
            pick = pick_row(epub_rows, title, author) or pick_row(rows, title, author)
            print(f"  → would pick: {pick.get('title') if pick else 'NO MATCH'} "
                  f"[{pick.get('extension') if pick else '-'}] "
                  f"by {pick.get('author') if pick else '-'}")
            continue

        try:
            ok, msg = deliver_one(opener, title, author, to_addrs,
                                  subject=book.get("subject"),
                                  log=print,
                                  remaining=len(books) - delivered - skipped - 1)
        except QuotaExhausted as exc:
            # The cap is account-wide, not per-book. Stopping here keeps the
            # resume file truthful and avoids re-confirming the same refusal
            # once per remaining title.
            print(f"\n  ! zlib daily download cap reached: {exc.reason[:160]}",
                  file=sys.stderr)
            print(f"  · {exc.remaining} title(s) left for a later run; "
                  f"state file {args.state} is intact", file=sys.stderr)
            quota_stopped = True
            break
        if ok:
            print(f"  ✓ delivered: {msg}")
            state["done"][key] = ",".join(to_addrs)
            save_state(args.state, state)
            delivered += 1
        else:
            print(f"  ! FAILED {title}: {msg}", file=sys.stderr)
            failed += 1

    verdict = f"=== delivered {delivered}, failed {failed}, skipped {skipped} ==="
    if quota_stopped:
        verdict += "\n=== stopped early: zlib daily download cap reached ==="
    rc = 3 if quota_stopped else (0 if failed == 0 else 1)

    # A run that delivered nothing and failed nothing has nothing to say.
    # The announce path is only silenced when the final line is exactly the
    # token NO_REPLY, so that token is printed last and on its own. Progress
    # chatter above it is for the log, not for the announcement.
    if delivered == 0 and failed == 0:
        verdict += "\nNO_REPLY"
    return rc, verdict


if __name__ == "__main__":
    sys.exit(main())
