"""Format-agnostic book metadata extraction for the Kindle delivery pipeline.

The delivery guard must answer one question before a file leaves for
amrekin@kindle.com: *is this attachment actually the book we meant to
send?* Magic bytes only prove the container format. A wrong Z-Library
row or a wrong Project Gutenberg id resolves to a perfectly valid
EPUB/MOBI of a completely different title, and Amazon silently converts
it into the reader. So the title has to come from inside the file.

Three container families are handled:

* EPUB  — a zip; ``dc:title`` / ``dc:creator`` in the OPF package
  document. Authoritative.
* MOBI / AZW3 — a PalmDB container. The MOBI header's EXTH records
  carry the title (type 503) and author (type 100), but the "EXTH
  present" flag is frequently zeroed by the tools that produce these
  files, so the EXTH block is probed positionally rather than trusted
  via the flag. When EXTH is absent or empty, the internal full-name
  field and a scan of printable strings recover the title.
* Anything else — no metadata; the guard falls back to the filename.

Every extractor returns ``(title, author)`` with either value possibly
``None``. Callers must treat a missing title as "unverifiable", never as
"matches".
"""

from __future__ import annotations

import re
import struct
import zipfile

__all__ = [
    "extract_metadata",
    "title_matches",
    "author_matches",
    "normalise",
]

# How much of the file to scan for printable strings. The MOBI header,
# EXTH block and the first content records all live in the first few
# hundred kilobytes; the cover blurb and the internal title string are
# within that window in every file seen so far.
_SCAN_BYTES = 400_000

# Longest string considered as a title candidate. Book blurbs and
# descriptions are hundreds of characters long and are not titles.
_MAX_TITLE_LEN = 160

_PRINTABLE_RUN = re.compile(rb"[\x20-\x7e]{3,}")


def normalise(text: str) -> str:
    """Lowercase and collapse punctuation to single spaces.

    "Hill, Joe - NOS4A2" and "NOS4A2" both need to compare equal, so
    every non-alphanumeric run becomes a single space.
    """
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


# --------------------------------------------------------------------------
# EPUB
# --------------------------------------------------------------------------
def _epub_metadata(path: str):
    """Return (title, creator) from an EPUB's OPF package document.

    The .opf path is not fixed across books: it is ``content.opf`` at
    the archive root in some and ``OEBPS/content.opf`` in others, so it
    is located by suffix. ``dc:creator`` frequently carries attributes
    (``opf:file-as=``, ``opf:role=``, ``id=``), so the tag pattern must
    tolerate them or the author silently disappears.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            opf = None
            for name in zf.namelist():
                if name.lower().endswith(".opf"):
                    opf = name
                    break
            if not opf:
                return None, None
            data = zf.read(opf).decode("utf-8", "replace")
    except (OSError, zipfile.BadZipFile, KeyError):
        return None, None

    def _grab(tag: str):
        match = re.search(r"<dc:%s\b[^>]*>(.*?)</dc:%s>" % (tag, tag), data, re.S)
        if not match:
            return None
        text = re.sub(r"<[^>]+>", "", match.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        return text or None

    return _grab("title"), _grab("creator")


# --------------------------------------------------------------------------
# MOBI / AZW3
# --------------------------------------------------------------------------
def _palmdb_records(data: bytes):
    """Return the record offsets of a PalmDB container."""
    if len(data) < 78:
        return []
    count = struct.unpack(">H", data[76:78])[0]
    if count == 0 or count > 10000:
        return []
    offsets = []
    for i in range(count):
        entry = 78 + i * 8
        if entry + 4 > len(data):
            break
        offsets.append(struct.unpack(">I", data[entry:entry + 4])[0])
    return offsets


def _mobi_header(data: bytes):
    """Return (mobi_offset, header_length) for a PalmDB/MOBI file."""
    offsets = _palmdb_records(data)
    if not offsets:
        return None, None
    record0 = offsets[0]
    if data[record0 + 16:record0 + 20] != b"MOBI":
        return None, None
    mobi = record0 + 16
    header_len = struct.unpack(">I", data[mobi + 4:mobi + 8])[0]
    return mobi, header_len


def _mobi_exth_flag(data: bytes, mobi: int) -> bool:
    """Whether the MOBI header claims an EXTH block (bit 0x40 at +0x70).

    Read for information only: the block is still probed positionally,
    because several converters leave the flag unset while writing a
    perfectly good EXTH.
    """
    try:
        flags = struct.unpack(">I", data[mobi + 0x70:mobi + 0x74])[0]
    except struct.error:
        return False
    return bool(flags & 0x40)


def _exth_records(data: bytes, mobi: int, header_len: int):
    """Parse the EXTH block that follows the MOBI header.

    The MOBI header's "EXTH present" bit is unreliable — several
    conversion tools leave it zeroed while still writing a valid EXTH
    block — so the block is probed at its documented position instead.
    """
    start = mobi + header_len
    if data[start:start + 4] != b"EXTH":
        return []
    if start + 12 > len(data):
        return []
    count = struct.unpack(">I", data[start + 8:start + 12])[0]
    if count > 1000:
        return []
    records = {}
    pos = start + 12
    for _ in range(count):
        if pos + 8 > len(data):
            break
        rec_type, rec_len = struct.unpack(">II", data[pos:pos + 8])
        # The record length counts its own 8-byte header, so the value
        # runs to pos + rec_len and the next record starts there too.
        if rec_len < 8:
            break
        value = data[pos + 8:pos + rec_len].decode("utf-8", "replace")
        value = value.replace("\x00", "").strip()
        pos += rec_len
        if value and rec_type not in records:
            records[rec_type] = value
    return records


def _mobi_fullname(data: bytes, mobi: int) -> str | None:
    """The MOBI header's internal full-name field ("author - title").

    The full-name offset lives at MOBI header + 0x44 and its length at
    +0x48. The offset is relative to the start of record 0, which is
    the 16-byte PalmDOC header that precedes the MOBI header.
    """
    try:
        offset = struct.unpack(">I", data[mobi + 0x44:mobi + 0x48])[0]
        length = struct.unpack(">I", data[mobi + 0x48:mobi + 0x4C])[0]
    except struct.error:
        return None
    if not length or length > 1024:
        return None
    # Resolve against record 0 first (the documented base), then
    # against the MOBI header's own start, keeping whichever lands on
    # printable text.
    for base in (mobi - 16, mobi):
        start = base + offset
        if 0 <= start <= len(data) - length:
            text = data[start:start + length].decode("utf-8", "replace")
            text = text.replace("\x00", "").strip()
            if text and all(32 <= ord(c) < 127 for c in text):
                return text
    return None


def _printable_strings(data: bytes):
    """Printable ASCII runs from the head of the file."""
    for match in _PRINTABLE_RUN.finditer(data[:_SCAN_BYTES]):
        try:
            yield match.group().decode("ascii")
        except UnicodeDecodeError:
            continue


# Container markers that appear as printable runs inside a MOBI/AZW3.
# They must never be mistaken for a title: "MOBI" and "BOOKMOBI" both
# read as plausible one-word titles.
_STRUCTURAL_MARKERS = {
    "BOOKMOBI", "MOBI", "EXTH", "TEXtREAd", "TXT", "PDF", "EXE",
    "TPZ1", "TPZ2", "TPZ3", "PDB", "AZW",
}


def _looks_like_name(text: str) -> bool:
    """True when a short string has the shape of a person's name.

    Every word is capitalised and there are two to four of them, which
    excludes prose, slogans and headings. "Silvia Moreno-Garcia"
    qualifies; "The Haunting of Hill House" does not, because "of" and
    "Hill House" break the capitalisation rule.
    """
    words = text.split()
    if not 2 <= len(words) <= 4:
        return False
    for word in words:
        if not word[:1].isalpha() or not word[:1].isupper():
            return False
        if any(ch.isdigit() for ch in word):
            return False
    return True


def _candidate_strings(data: bytes):
    """Printable runs that could plausibly be title or author metadata.

    Container markers and tool banners are dropped: they are printable,
    short, and would otherwise win the first slot.
    """
    for raw in _printable_strings(data):
        text = raw.strip()
        if not text or len(text) > _MAX_TITLE_LEN:
            continue
        if text in _STRUCTURAL_MARKERS:
            continue
        if "<" in text and ">" in text:
            continue  # markup fragment, not metadata
        if re.match(r"^\d+calibre\b", text, re.I):
            continue  # converter banner
        if text.lower().endswith((".epub", ".mobi", ".azw3")):
            continue
        yield text


def _strings_title_author(data: bytes):
    """Recover a title (and author) by scanning printable strings.

    Used when the structured metadata paths come up empty. In the real
    files the order is: an internal name, then the container markers,
    then the title, then the author. So the title is the first
    plausible candidate, and the author is the first name-like
    candidate after it that is not a second spelling of the title.
    """
    title = None
    author = None
    for text in _candidate_strings(data):
        # "Hill, Joe - NOS4A2" style names carry both parts.
        if " - " in text:
            head, _, tail = text.partition(" - ")
            head = re.sub(r"\s+", " ", head.replace(",", " ")).strip()
            tail = tail.strip()
            if head and tail:
                if title is None:
                    title = tail
                if author is None and _looks_like_name(head):
                    author = head
                continue
        if title is None:
            # Underscored internal titles ("Mexican_Gothic") are one
            # whitespace token, so count words after normalising.
            words = normalise(text).split()
            if 1 <= len(words) <= 12:
                title = text
            continue
        if author is None and _looks_like_name(text):
            # The title is often stored twice in two spellings
            # ("Mexican_Gothic" and "Mexican Gothic"). A second
            # spelling of the title is not the author.
            title_words = _tokens(title)
            candidate_words = _tokens(text)
            if candidate_words and title_words:
                if candidate_words <= title_words or title_words <= candidate_words:
                    continue
            author = text
    return title, author


def _mobi_metadata(path: str):
    """Return (title, author) for a MOBI/AZW3 file."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(_SCAN_BYTES + 200_000)
    except OSError:
        return None, None

    mobi, header_len = _mobi_header(data)
    if mobi is None:
        return _strings_title_author(data)

    records = _exth_records(data, mobi, header_len)
    title = records.get(503)
    author = records.get(100)

    if not title:
        fullname = _mobi_fullname(data, mobi)
        if fullname:
            if "," in fullname and " - " in fullname:
                head, _, tail = fullname.partition(" - ")
                title = tail.strip()
                author = author or head.strip().replace(",", "").strip()
            elif " - " in fullname:
                title = fullname.split(" - ", 1)[1].strip()
            else:
                title = fullname

    if not title:
        scanned_title, scanned_author = _strings_title_author(data)
        title = scanned_title
        author = author or scanned_author

    return title, author


# --------------------------------------------------------------------------
# Public interface
# --------------------------------------------------------------------------
def extract_metadata(path: str):
    """Return (title, author) for a book file, or (None, None).

    The format is chosen from the file's magic bytes, not its
    extension: a download named ``.epub`` can be a MOBI and vice versa.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(80)
    except OSError:
        return None, None

    if head[:2] == b"PK":
        title, creator = _epub_metadata(path)
        if title:
            return title, creator
        try:
            with open(path, "rb") as fh:
                return _strings_title_author(fh.read(_SCAN_BYTES))
        except OSError:
            return None, None

    if head[60:68] == b"BOOKMOBI" or head[60:64] in (b"TPZ3", b"TPZ2", b"TPZ1"):
        return _mobi_metadata(path)

    if head[60:68] == b"TEXtREAd":
        return _mobi_metadata(path)

    return None, None


def title_matches(expected: str, found: str | None) -> bool:
    """True when *found* plausibly denotes *expected*.

    Matching is token-based and order-insensitive, and it tolerates the
    "author - title" composite form that Z-Library and EPUB producers
    both use. A missing *found* title is never a match: the guard must
    fail closed.
    """
    if not found:
        return False
    want = _tokens(expected)
    if not want:
        return False
    candidates = [found]
    if " - " in found:
        head, _, tail = found.partition(" - ")
        candidates.extend([head.strip(), tail.strip()])
    for candidate in candidates:
        got = _tokens(candidate)
        if not got:
            continue
        if want == got or want <= got or got <= want:
            return True
    return False


def author_matches(expected: str, found: str | None) -> bool:
    """True when two author names denote the same person.

    "Joe Hill" and "Hill, Joe" are the same author, so token sets are
    compared rather than substrings. A missing *found* author is not a
    match.
    """
    if not expected or not found:
        return False
    want = _tokens(expected)
    got = _tokens(found)
    if not want or not got:
        return False
    return want == got or want <= got or got <= want
