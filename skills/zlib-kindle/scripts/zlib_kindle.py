#!/usr/bin/env python3
"""zlib_kindle.py — find a book, fetch it, deliver it to a Kindle address.

Pipeline: search -> pick -> download to the Mac -> email as an attachment.

Subcommands
-----------
  search   <query>            list Z-Library matches for a query
  fetch    <book-id|url>      download one book file to the local library dir
  send     <file>             email a file to the Kindle address via AgentMail
  deliver  <query>            the full pipeline: search -> fetch -> send
  books                        show the curated horror list with IDs

Delivery uses AgentMail (the Dross inbox), not raw SMTP. The AgentMail API
accepts base64 attachments, which is what Amazon's Send-to-Kindle address
expects. Credentials are read from the local secrets dir and never logged.

Z-Library requires a signed-in account to serve file lists. If no account is
configured, the fetcher falls back to Project Gutenberg for public-domain
titles, so the pipeline still works end to end for those.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.cookiejar import CookieJar

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import bookmeta
except ImportError:  # pragma: no cover - bookmeta ships with the skill
    bookmeta = None

HOME = os.path.expanduser("~")
WORKSPACE = os.path.join(HOME, ".openclaw", "workspace")
SECRETS = os.path.join(WORKSPACE, "secrets")
LIBRARY_DIR = os.path.join(HOME, "Downloads", "dross-books")

KINDLE_ADDR = "amrekin@kindle.com"
AGENTMAIL_INBOX = "thedross@agentmail.to"

# Z-Library's authenticated eAPI. The public HTML pages on the "z-lib.id"
# family now render a "Lifetime Premium" upsell instead of a download
# button and their /papi/ endpoints 404, so the web path is a dead end.
# The eAPI on z-lib.by is the working route: log in, POST /eapi/book/search,
# then GET /eapi/book/<id>/<hash>/file which returns a signed CDN link.
ZLIB_BASE = "https://z-lib.by"
EAPI_LOGIN = "/eapi/user/login"
EAPI_SEARCH = "/eapi/book/search"
EAPI_FILE = "/eapi/book/{id}/{hash}/file"
GUTENBERG = "https://www.gutenberg.org"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# PROJECT GUTENBERG IS BANNED (Amre, 2026-10-30).
#
# "22 books of pure shit. Do not use project guthenburg again."
#
# The Gutenberg pipeline delivered omnibus compilations of 19th-century
# novel cycles -- Dumas, Trollope, Zola, Bulwer-Lytton, the collected Tarzan
# -- in dry, dated translations, at doorstopper length. Twenty-two of those
# went out in one evening and every one of them was unwanted.
#
# The Gutenberg fallback in cmd_fetch() and every Gutenberg build script
# are now dead. New material must come from Z-Library.
#
# The GUTENBERG_IDS map below is retained ONLY so the existing, already
# delivered horror titles stay verifiable. It must not be used to source
# anything new.
# ---------------------------------------------------------------------------
GUTENBERG_BANNED = True

# Curated horror list -> Project Gutenberg id where the title is public domain.
# KEPT FOR VERIFICATION ONLY. Do not use to source new material.
GUTENBERG_IDS = {
    "The King in Yellow": 8492,
    "Carmilla": 10007,
    "The Call of Cthulhu": 68283,
    "At the Mountains of Madness": 70652,
    "The Great God Pan": 389,
    "The House of Souls": 25016,
    "The Turn of the Screw": 209,
    "The Yellow Wallpaper": 1952,
    "The Picture of Dorian Gray": 174,
    "Dracula": 345,
    "The Time Machine": 35,
    "The War of the Worlds": 36,
    "Frankenstein": 84,
    "The Metamorphosis": 5200,
    "The Canterville Ghost": 14522,
    "The Woman in White": 583,
    "The Moonstone": 155,
    "The Invisible Man": 5230,
}

FORMAT_RANK = {"epub": 0, "epub3": 0, "mobi": 1, "azw3": 2, "pdf": 3, "djvu": 4, "txt": 5}

# A Kindle-bound fetch prefers EPUB. Kindle Scribe (Amre's device) reads
# EPUB, PDF and DOCX; it does NOT read MOBI or AZW3, so preferring those
# here produced books that silently never appeared on the device.
KINDLE_FORMAT_RANK = {"epub": 0, "epub3": 0, "pdf": 1, "azw3": 2, "mobi": 3, "txt": 4, "djvu": 5}

# Set by zlib_files() when the eAPI withholds a download link because the
# account has hit its daily download cap (10/day). The refusal message is the
# only signal the server gives, and it is transient: the cap resets on a
# rolling window, so a batch that keeps hammering after the refusal just
# burns time re-confirming the same wall.
LAST_REFUSAL_REASON = ""

# Z-Library's phrasing for the daily cap, as observed in the wild.
QUOTA_MARKERS = ("daily limit", "download counter being reset",
                 "already reached for today")


def quota_exhausted(reason: str = "") -> bool:
    """True if the given refusal (or the last one seen) is the daily cap."""
    text = (reason or LAST_REFUSAL_REASON or "").lower()
    return any(marker in text for marker in QUOTA_MARKERS)


# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------
def make_session() -> urllib.request.OpenerDirector:
    """Opener with a cookie jar so a Z-Library login survives across calls."""
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar()),
        urllib.request.HTTPSHandler(context=ctx),
    )
    opener.addheaders = [("User-Agent", UA), ("Accept-Language", "en-US,en;q=0.9")]
    return opener


def fetch(opener, url, data=None, headers=None, timeout=45):
    """Return (status, body_bytes, final_url). HTTP errors return the status."""
    req = urllib.request.Request(url, data=data)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.geturl()
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return exc.code, body, url
    except Exception as exc:  # noqa: BLE001
        print(f"  ! network error for {url}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0, b"", url


def text_of(body: bytes) -> str:
    return body.decode("utf-8", "replace")


# --------------------------------------------------------------------------
# Z-Library: search (eAPI)
# --------------------------------------------------------------------------
def _eapi_row(item: dict) -> dict:
    """Normalise one eAPI search result into the shared book-row shape."""
    title = (item.get("title") or "").strip()
    author = (item.get("author") or "").strip()
    # eAPI titles arrive as "Author - Title"; split them so the row reads
    # "Title by Author" like every other source in this script. The author
    # field often carries a bracketed duplicate ("Hill, Joe [Hill, Joe]"),
    # so match the head against it before trusting the split.
    if " - " in title:
        head, _, tail = title.partition(" - ")
        head, tail = head.strip(), tail.strip()
        head_norm = re.sub(r"\s*\[[^\]]*\]\s*$", "", head).strip().lower()
        author_norm = re.sub(r"\s*\[[^\]]*\]\s*$", "", author).strip().lower()
        if tail and (head_norm == author_norm or len(tail) > len(head)):
            title, author = tail, head
        elif head and not author:
            author = head
    ext = (item.get("extension") or "").strip().lower()
    return {
        "id": str(item.get("id") or ""),
        "hash": (item.get("hash") or "").strip(),
        "title": title,
        "author": author,
        "publisher": (item.get("publisher") or "").strip(),
        "extension": ext.upper(),
        "size": (item.get("filesizeString") or "").strip(),
        "bytes": item.get("filesize"),
        "year": str(item.get("year") or ""),
        "language": (item.get("language") or "").strip(),
        "md5": (item.get("md5") or "").strip(),
        "has_files": bool(item.get("hash")),
        "url": (item.get("href") or f"{ZLIB_BASE}/book/{item.get('id')}").strip(),
        "source": "zlib",
    }


def _eapi_call(opener, path, data=None, timeout=60):
    """Call an eAPI endpoint and return the parsed JSON envelope.

    The eAPI answers failures with a JSON body carrying the real reason
    ("Too many logins #2. Try again later.", the daily download cap, a
    bad password). That body is discarded on a non-200 status, which
    leaves the caller with a bare "http 400" and no idea what went
    wrong. Parse the body first and keep its error message.
    """
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    status, body, _ = fetch(opener, ZLIB_BASE + path, data=data, headers=headers, timeout=timeout)
    envelope = None
    try:
        envelope = json.loads(text_of(body))
    except ValueError:
        envelope = None
    if status != 200:
        detail = ""
        if isinstance(envelope, dict):
            detail = str(envelope.get("error") or envelope.get("message") or "")
        return {"success": 0, "error": detail or f"http {status}"}
    if envelope is None:
        return {"success": 0, "error": "non-JSON response"}
    return envelope


def zlib_search(query: str, limit: int = 10, opener=None, extensions=None) -> list[dict]:
    """Search Z-Library via the authenticated eAPI and return book rows."""
    own = opener is None
    opener = opener or make_session()
    if own and not zlib_login(opener):
        print("  ! zlib: no usable account; search will be unauthenticated",
              file=sys.stderr)
    payload = [("message", query), ("page", "1"), ("limit", str(max(1, limit)))]
    for ext in extensions or []:
        payload.append(("extensions[]", ext))
    env = _eapi_call(opener, EAPI_SEARCH, urllib.parse.urlencode(payload).encode())
    if not env.get("success"):
        print(f"  ! zlib search failed: {str(env.get('error'))[:80]}", file=sys.stderr)
        return []
    rows = [_eapi_row(item) for item in env.get("books", [])]
    return rows[:limit]


# --------------------------------------------------------------------------
# Z-Library: account + file list
# --------------------------------------------------------------------------
def read_zlib_creds():
    """Read (email, password) from secrets/zlib-account.txt if present."""
    path = os.path.join(SECRETS, "zlib-account.txt")
    if not os.path.isfile(path):
        return None
    try:
        text = open(path, encoding="utf-8").read().strip()
    except Exception:
        return None
    if ":" in text:
        email, password = text.split(":", 1)
    else:
        parts = [p.strip() for p in text.splitlines() if p.strip()]
        if len(parts) < 2:
            return None
        email, password = parts[0], parts[1]
    return email.strip(), password.strip()


def zlib_login(opener) -> bool:
    """Sign in to Z-Library's eAPI. Returns True on success."""
    creds = read_zlib_creds()
    if not creds:
        return False
    email, password = creds
    payload = urllib.parse.urlencode({"email": email, "password": password}).encode()
    env = _eapi_call(opener, EAPI_LOGIN, payload)
    if env.get("success"):
        print("  · zlib: signed in")
        return True
    reason = str(env.get("error") or "unknown error").strip()
    print(f"  · zlib: sign-in failed: {reason[:160]}", file=sys.stderr)
    if "too many logins" in reason.lower():
        print("  · zlib: the account is rate-limited on sign-ins; wait before "
              "retrying (each script run is one login)", file=sys.stderr)
    return False


def zlib_files(opener, book_id: str, book_hash: str = "") -> list[dict]:
    """Return downloadable file entries for a book id (needs a session).

    The eAPI resolves a book by the pair (id, hash). Search results carry
    both; a bare id is looked up by trying the book detail endpoint.
    """
    if not book_hash:
        env = _eapi_call(opener, f"/eapi/book/{book_id}")
        book = env.get("book") or {}
        book_hash = (book.get("hash") or "").strip()
    if not book_hash:
        return []
    env = _eapi_call(opener, EAPI_FILE.format(id=book_id, hash=book_hash))
    if not env.get("success"):
        return []
    info = env.get("file") or {}
    link = info.get("downloadLink")
    if not link:
        # The eAPI answers 200 with success:1 but withholds the link when
        # the account cannot download — most often the daily download cap
        # (10/day). It explains itself in disallowDownloadMessage; print
        # that, stripped of the HTML, instead of failing anonymously.
        reason = info.get("disallowDownloadMessage") or ""
        reason = re.sub(r"<[^>]+>", " ", reason)
        reason = (reason.replace("&nbsp;", " ").replace("&amp;", "&")
                        .replace("&quot;", '"').replace("&#39;", "'"))
        reason = re.sub(r"\s+", " ", reason).strip()
        global LAST_REFUSAL_REASON
        LAST_REFUSAL_REASON = reason
        if reason:
            print(f"  ! zlib refused the download: {reason[:200]}", file=sys.stderr)
        else:
            print("  ! zlib returned no download link for this book", file=sys.stderr)
        return []
    return [{
        "url": link,
        "extension": (info.get("extension") or "").lower(),
        "description": info.get("description") or "",
        "author": info.get("author") or "",
        "allow_download": info.get("allowDownload", True),
    }]


def download_file(opener, url: str, dest: str) -> bool:
    status, body, _ = fetch(opener, url, timeout=300)
    if status != 200 or not body:
        print(f"  ! download failed http={status}: {url[:120]}", file=sys.stderr)
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(body)
    return True


# --------------------------------------------------------------------------
# Project Gutenberg fallback
# --------------------------------------------------------------------------
def gutenberg_lookup(title: str):
    """Project Gutenberg is banned as a source (Amre, 2026-10-30).

    Returns None unconditionally. Every caller treats None as "no id",
    so no path in this script can reach Gutenberg any more.
    """
    if GUTENBERG_BANNED:
        return None
    """Find a Gutenberg id for a title via gutendex, else the curated map.

    Z-Library serves titles lowercased, so the curated map is matched
    case-insensitively and on normalised punctuation.
    """
    key = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    for known, gid in GUTENBERG_IDS.items():
        if re.sub(r"[^a-z0-9]+", " ", known.lower()).strip() == key:
            return gid
    # "The King in Yellow by Robert W. Chambers" -> "The King in Yellow"
    head = re.split(r"\s+by\s+", title, maxsplit=1)[0]
    hkey = re.sub(r"[^a-z0-9]+", " ", head.lower()).strip()
    for known, gid in GUTENBERG_IDS.items():
        if re.sub(r"[^a-z0-9]+", " ", known.lower()).strip() == hkey:
            return gid
    try:
        url = "https://gutendex.com/books?search=" + urllib.parse.quote(title)
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        for result in data.get("results", []):
            formats = result.get("formats", {})
            if "application/epub+zip" in formats or "text/html" in formats:
                return result.get("id")
    except Exception:
        pass
    return None


def gutenberg_fetch(gid, dest: str) -> bool:
    """Project Gutenberg is banned as a source (Amre, 2026-10-30).

    Returns False unconditionally: no Gutenberg file is ever downloaded.
    """
    if GUTENBERG_BANNED:
        return False
    opener = make_session()
    for suffix in (f"https://www.gutenberg.org/ebooks/{gid}.epub3.images",
                   f"https://www.gutenberg.org/ebooks/{gid}.epub",
                   f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.epub"):
        status, body, _ = fetch(opener, suffix, timeout=300)
        if status == 200 and body and body[:2] == b"PK":
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(body)
            return True
    return False


# --------------------------------------------------------------------------
# EPUB content verification
# --------------------------------------------------------------------------
def epub_metadata(path):
    """Return (title, creator) from an EPUB's OPF metadata.

    The .opf path is not fixed across books: it is content.opf at the
    archive root in some and OEBPS/content.opf in others, so locate it.
    dc:creator often carries attributes (opf:file-as=, opf:role=, id=),
    so the tag pattern must tolerate them or the author silently
    disappears from the result.
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
    except (OSError, zipfile.BadZipFile):
        return None, None

    def _grab(tag):
        m = re.search(r"<dc:%s\b[^>]*>(.*?)</dc:%s>" % (tag, tag), data, re.S)
        if not m:
            return None
        text = re.sub(r"<[^>]+>", "", m.group(1))
        return re.sub(r"\s+", " ", text).strip() or None

    return _grab("title"), _grab("creator")


def _tokens(text):
    """Lowercase word tokens, for order-insensitive name comparison."""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _title_candidates(raw_title):
    """Plausible titles for an EPUB, given how sources store them.

    A Z-Library EPUB carries the eAPI's combined form in dc:title, so
    "NOS4A2" arrives as "Hill, Joe - NOS4A2". Offer the whole string and
    each side of the separator as candidates.
    """
    cands = [raw_title]
    if " - " in raw_title:
        head, _, tail = raw_title.partition(" - ")
        if tail.strip():
            cands.append(tail.strip())
        if head.strip():
            cands.append(head.strip())
    return [c for c in cands if c]


def _names_match(want, got):
    """True when two names denote the same thing, ignoring order.

    "Joe Hill" and "Hill, Joe" are the same author, so compare token
    sets rather than substrings.
    """
    a, b = _tokens(want), _tokens(got)
    if not a or not b:
        return False
    return a == b or a <= b or b <= a


# --------------------------------------------------------------------------
# Metadata repair for EPUBs with malformed OPF metadata
# --------------------------------------------------------------------------
# Two defects turn up in real Z-Library EPUBs, and both produce a false
# negative against an otherwise-correct file:
#
#   1. dc:creator echoes the title with a version suffix appended, e.g.
#      "The King of Elfland's Daughter v2.0". The creator field names no
#      author at all, and the title is right.
#   2. dc:title and dc:creator are swapped: the creator holds the title
#      and the title holds the author.
#
# The repair is evidence-based and stays fail-closed. A defect is only
# repaired when the metadata itself proves it — the echo pattern, or a
# clean swap against the expectations — and an author that the metadata
# cannot state is only accepted when the author's name is actually found
# in the book's own text. Anything that is not provably one of these two
# defects still fails exactly as before.

_VERSION_TOKEN = re.compile(r"v\d+|\d+")


def _title_matches(expect_title, found):
    """True when a file's title is the requested title.

    A Z-Library EPUB carries the eAPI's combined form in dc:title, so
    "NOS4A2" arrives as "Hill, Joe - NOS4A2"; each side of the separator
    is offered as a candidate and the token sets are compared.
    """
    if not expect_title:
        return True
    want = _tokens(expect_title)
    return any(want == _tokens(c) or want <= _tokens(c) or _tokens(c) <= want
               for c in _title_candidates(found))


def _creator_is_title_echo(title, creator):
    """True when dc:creator merely repeats the title plus version junk."""
    ct, cc = _tokens(title), _tokens(creator)
    if not ct or not cc or ct == cc:
        return False
    if not ct <= cc:
        return False
    # Only a version suffix may be extra ("v2", "0" from "v2.0").
    return all(_VERSION_TOKEN.fullmatch(t) for t in cc - ct)


def _metadata_is_swapped(expect_title, expect_author, title, creator):
    """True when dc:title and dc:creator are demonstrably swapped.

    Both halves must hold: the creator carries the requested title and
    the title carries the requested author. One half alone is not proof.
    """
    if not (expect_title and expect_author and title and creator):
        return False
    return (_title_matches(expect_title, creator)
            and _names_match(expect_author, title)
            and not _names_match(expect_author, creator))


def _epub_text(path, limit=600_000):
    """Plain text of an EPUB's HTML documents, for metadata cross-checks."""
    parts = []
    total = 0
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if not name.lower().endswith((".html", ".xhtml", ".htm")):
                    continue
                try:
                    raw = zf.read(name)
                except (OSError, KeyError, zipfile.BadZipFile):
                    continue
                data = raw.decode("utf-8", "replace")
                data = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", data)
                data = re.sub(r"(?s)<[^>]+>", " ", data)
                parts.append(data)
                total += len(data)
                if total >= limit:
                    break
    except (OSError, zipfile.BadZipFile):
        return ""
    return " ".join(parts)[:limit]


def _phrase_in(text, phrase):
    """True when every word of phrase appears, in order, inside text."""
    want = re.findall(r"[a-z0-9]+", (phrase or "").lower())
    hay = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not want or not hay:
        return False
    span = len(want)
    for i in range(len(hay) - span + 1):
        if hay[i:i + span] == want:
            return True
    return False


def _metadata_check(path, expect_title=None, expect_author=None):
    """Check a file's identity, repairing provable metadata defects.

    Returns (ok, title, creator, errors, notes). `errors` holds failure
    kinds ("title_mismatch", "no_author", "author_mismatch") and `notes`
    describes any repair applied. Each caller formats its own message,
    so the wording of the existing failures is unchanged.
    """
    if bookmeta is not None:
        title, creator = bookmeta.extract_metadata(path)
    else:
        title, creator = epub_metadata(path)
    if title is None:
        return False, title, creator, ["no_metadata"], []

    errors = []
    notes = []

    if _metadata_is_swapped(expect_title, expect_author, title, creator):
        title, creator = creator, title
        notes.append("dc:title and dc:creator were swapped; using the corrected pair")

    if expect_title and not _title_matches(expect_title, title):
        errors.append("title_mismatch")

    if expect_author:
        if _creator_is_title_echo(title, creator):
            notes.append(f"dc:creator echoes the title ({creator!r}) and names no author")
            creator = None
            if _phrase_in(_epub_text(path), expect_author):
                creator = expect_author
                notes.append(f"author {expect_author!r} confirmed in the book's own text")
            else:
                errors.append("no_author")
        elif not creator:
            errors.append("no_author")
        elif not _names_match(expect_author, creator):
            errors.append("author_mismatch")

    return (not errors), title, creator, errors, notes


def verify_book(path, expect_title=None, expect_author=None):
    """Check that a book file is the book that was requested.

    The magic bytes prove the container format, not that it is the
    right book. A wrong Project Gutenberg id resolves to a real EPUB of
    a completely different title, and a Z-Library row can advertise one
    edition while serving another, so the title inside the file is the
    only reliable check.

    EPUBs are read from their OPF metadata; MOBI and AZW3 files are read
    from the MOBI header, EXTH records and the internal title string.
    """
    ok, title, creator, errors, notes = _metadata_check(path, expect_title, expect_author)
    if title is None:
        print(f"  ! no readable book metadata in {os.path.basename(path)}")
        return False
    for note in notes:
        print(f"  · {note}")
    print(f"  · title:  {title}")
    print(f"  · author: {creator or '(none)'}")

    for kind in errors:
        if kind == "title_mismatch":
            print(f"  ! title mismatch: wanted {expect_title!r}, file says {title!r}",
                  file=sys.stderr)
        elif kind == "no_author":
            print(f"  ! no author metadata in file; wanted {expect_author!r}",
                  file=sys.stderr)
        elif kind == "author_mismatch":
            print(f"  ! author mismatch: wanted {expect_author!r}, file says {creator!r}",
                  file=sys.stderr)
    print("  ✓ metadata matches" if ok else "  ! metadata does not match")
    return ok


# --------------------------------------------------------------------------
# Delivery preflight
# --------------------------------------------------------------------------
# Nothing reaches Amazon until it has passed these checks. They are the
# difference between a book that arrives and a book that vanishes with no
# error anywhere: Amazon's Send-to-Kindle accepts a file silently or not
# at all, and it never tells you which one happened.
#
# The namespace rule is not pedantry. An EPUB whose package document is
# <opf:package xmlns:opf="..."> is well-formed XML but is NOT the form
# Amazon's converter takes, and such a file is dropped without a word.
# Every EPUB that arrived used the default namespace; the one that did
# not arrive used the prefixed form.

OPF_NS = "http://www.idpf.org/2007/opf"


def epub_opf_info(path):
    """Return (root_tag, default_ns, opf_member) for an EPUB's OPF.

    The .opf path is not fixed across books, so it is located by suffix.
    The default namespace is read from the raw root tag's attributes
    rather than from a parsed tree: an XML parser expands prefixes and
    would report <opf:package> as being in the OPF namespace, hiding
    exactly the defect this check exists to catch.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            opf = None
            for name in zf.namelist():
                if name.lower().endswith(".opf"):
                    opf = name
                    break
            if not opf:
                return None, None, None
            data = zf.read(opf).decode("utf-8", "replace")
    except (OSError, zipfile.BadZipFile, KeyError):
        return None, None, None
    match = re.search(r"<([A-Za-z_][\w.\-]*(?::[\w.\-]+)?)\b([^>]*)>", data)
    if not match:
        return None, None, None
    tag, attrs = match.group(1), match.group(2)
    default_ns = re.search(r'xmlns\s*=\s*"([^"]+)"', attrs)
    return tag, (default_ns.group(1) if default_ns else None), opf


def epub_namespace_ok(path) -> bool:
    """True when the OPF package document uses the default OPF namespace."""
    import xml.etree.ElementTree as ET

    tag, default_ns, opf = epub_opf_info(path)
    if not opf or default_ns != OPF_NS:
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            root = ET.fromstring(zf.read(opf))
    except Exception:
        return False
    return root.tag == "{%s}package" % OPF_NS


def canonical_format(path) -> str | None:
    """Return the real format of a file, read from its magic bytes.

    Only formats Amazon's Send-to-Kindle accepts are recognised. The
    extension a Z-Library row advertises is not evidence: the row can
    say EPUB and serve a MOBI, and the Gutenberg fallback always serves
    EPUB. Anything unrecognised returns None so the file is refused
    rather than quietly mislabelled.
    """
    raw = sniff_ext(path)
    if raw in ("epub", "mobi", "azw3", "pdf"):
        return raw
    if raw == "txt":
        # sniff_ext falls back to "txt" for anything it cannot place, so
        # confirm the bytes really are text before trusting that answer.
        try:
            with open(path, "rb") as fh:
                head = fh.read(4096)
        except OSError:
            return None
        if not head:
            return None
        try:
            head.decode("utf-8")
        except UnicodeDecodeError:
            return None
        control = sum(1 for b in head if b < 9 or 13 < b < 32)
        if control > len(head) * 0.05:
            return None
        return "txt"
    return None


def preflight_book(path, expect_title=None, expect_author=None):
    """Fail-closed checks a book must pass before Amazon sees it.

    Returns (ok, reason). On success the reason is the real format.
    """
    if not os.path.isfile(path):
        return False, "file does not exist"
    if os.path.getsize(path) == 0:
        return False, "file is empty"

    fmt = canonical_format(path)
    if fmt is None:
        return False, "magic bytes are not a format Amazon's converter accepts"

    ext = os.path.splitext(path)[1].lower()
    want_ext = FORMAT_EXT.get(fmt)
    if ext != want_ext:
        return False, (f"extension {ext or '(none)'} disagrees with the real "
                       f"format ({fmt})")

    if fmt == "epub" and not epub_namespace_ok(path):
        return False, ("EPUB package document does not use the default OPF "
                       "namespace (prefixed opf: root); Amazon drops these")

    ok, title, creator, errors, notes = _metadata_check(path, expect_title, expect_author)
    if not title:
        return False, "no readable title metadata inside the file"
    for kind in errors:
        if kind == "title_mismatch":
            return False, f"title mismatch: wanted {expect_title!r}, file says {title!r}"
        if kind == "no_author":
            return False, f"no author metadata inside the file (wanted {expect_author!r})"
        if kind == "author_mismatch":
            return False, f"author mismatch: wanted {expect_author!r}, file says {creator!r}"
    return True, fmt


def _default_ns_opf(data: str) -> str:
    """Rewrite a prefixed-namespace OPF into the default-namespace form.

    The root becomes <package xmlns="...opf">, the prefixed child
    elements are unprefixed, and the xmlns:opf declaration is kept so
    prefixed attributes (opf:role, opf:file-as) stay valid.
    """
    root_match = re.search(r"<opf:package\b([^>]*)>", data)
    if root_match:
        attrs = root_match.group(1)
        if "xmlns=" not in attrs:
            attrs = f' xmlns="{OPF_NS}"' + attrs
        data = (data[:root_match.start()] + "<package" + attrs + ">"
                + data[root_match.end():])
    return data.replace("<opf:", "<").replace("</opf:", "</")


def repair_epub_namespace(src, dest=None) -> str | None:
    """Write a copy of an EPUB whose OPF root uses the default namespace.

    Returns the repaired path, or None when the file cannot be repaired.
    The original file is never modified.
    """
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(src) as zin:
            entries = [(i, zin.read(i.filename)) for i in zin.infolist()]
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"  ! cannot read {os.path.basename(src)}: {type(exc).__name__}",
              file=sys.stderr)
        return None

    opf_member = None
    for info, _ in entries:
        if info.filename.lower().endswith(".opf"):
            opf_member = info.filename
            break
    if not opf_member:
        print("  ! no OPF package document to repair", file=sys.stderr)
        return None

    fixed = []
    for info, blob in entries:
        if info.filename == opf_member:
            text = blob.decode("utf-8", "replace")
            blob = _default_ns_opf(text).encode("utf-8")
        fixed.append((info, blob))

    dest = dest or f"{os.path.splitext(src)[0]}-repaired.epub"
    try:
        with zipfile.ZipFile(dest, "w") as zout:
            for info, blob in fixed:
                out_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                out_info.compress_type = info.compress_type
                out_info.external_attr = info.external_attr
                zout.writestr(out_info, blob)
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"  ! could not write repaired EPUB: {type(exc).__name__}", file=sys.stderr)
        return None

    try:
        with zipfile.ZipFile(dest) as zf:
            ET.fromstring(zf.read(opf_member))
    except Exception as exc:
        print(f"  ! repaired EPUB is not readable: {type(exc).__name__}", file=sys.stderr)
        return None
    return dest


def calibre_convert(src, fmt="mobi", dest=None) -> str | None:
    """Convert a book file with Calibre's ebook-convert.

    Conversion is the dependable fallback for a file Amazon's converter
    will not take: Calibre rewrites the book into a format Amazon reads
    natively, so no Amazon-side conversion is needed at all.
    """
    exe = shutil.which("ebook-convert") or "/opt/homebrew/bin/ebook-convert"
    if not exe or not os.path.isfile(exe):
        print("  · calibre not available; cannot convert", file=sys.stderr)
        return None
    dest = dest or f"{os.path.splitext(src)[0]}.{fmt}"
    # The Friday cron gives the whole script 300 seconds, so a
    # conversion that hangs must not eat the entire budget and get the
    # job killed with no report. Bounded well below the cron timeout.
    try:
        proc = subprocess.run([exe, src, dest], capture_output=True,
                              text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("  ! conversion timed out", file=sys.stderr)
        return None
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  ! conversion failed: {type(exc).__name__}", file=sys.stderr)
        return None
    if proc.returncode != 0 or not os.path.isfile(dest) or os.path.getsize(dest) == 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        print(f"  ! conversion failed: {detail[-1][:120] if detail else proc.returncode}",
              file=sys.stderr)
        return None
    return dest


def ensure_kindle_ready(path, expect_title=None, expect_author=None,
                        fallbacks=("mobi", "azw3")):
    """Make a downloaded file safe to send, repairing or converting it.

    Returns (ready_path, ok, notes). The original file is left in place.

    `fallbacks` are the formats to try when an EPUB cannot be repaired.
    Pass fallbacks=() to refuse rather than send a format the target
    device cannot read (Kindle Scribe rejects MOBI and AZW3).
    """
    ok, reason = preflight_book(path, expect_title, expect_author)
    if ok:
        return path, True, []

    notes = [reason]
    if os.path.splitext(path)[1].lower() == ".epub":
        repaired = repair_epub_namespace(path)
        if repaired:
            ok2, reason2 = preflight_book(repaired, expect_title, expect_author)
            if ok2:
                return repaired, True, notes + [f"repaired OPF namespace -> {os.path.basename(repaired)}"]
            notes.append(f"repair did not satisfy preflight: {reason2}")
        for fmt in fallbacks:
            converted = calibre_convert(path, fmt)
            if not converted:
                continue
            ok3, reason3 = preflight_book(converted, expect_title, expect_author)
            if ok3:
                return converted, True, notes + [f"converted to {fmt.upper()} -> {os.path.basename(converted)}"]
            notes.append(f"{fmt.upper()} conversion failed preflight: {reason3}")
    return path, False, notes


# --------------------------------------------------------------------------
# AgentMail delivery
# --------------------------------------------------------------------------
def agentmail_key():
    for name in ("sol-agentmail-api-key.txt", "the-dross-agentmail-api-key.txt"):
        path = os.path.join(SECRETS, name)
        if os.path.isfile(path):
            key = open(path, encoding="utf-8").read().strip()
            if key:
                return key
    raise SystemExit("no AgentMail API key found in secrets/")


# Python's mimetypes does not know the ebook formats that matter to Kindle,
# so it silently returns None for .azw3 and .epub3 and the attachment would
# go out as application/octet-stream. Amazon's Send-to-Kindle is picky
# about this: a mislabelled or empty attachment comes back as "E009 - No
# Attachment". These types are mapped explicitly, and the type actually
# sent is derived from the format proven by the file's magic bytes rather
# than from its filename.
KINDLE_CONTENT_TYPES = {
    ".azw3": "application/vnd.amazon.ebook",
    ".mobi": "application/x-mobipocket-ebook",
    ".epub": "application/epub+zip",
    ".epub3": "application/epub+zip",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}

# The one true mapping of a real format (as read from magic bytes) to the
# extension it must carry. The content type is then derived from the
# extension through KINDLE_CONTENT_TYPES, so a file's bytes, its name and
# the MIME type Amazon sees can never drift apart.
FORMAT_EXT = {
    "azw3": ".azw3",
    "mobi": ".mobi",
    "epub": ".epub",
    "pdf": ".pdf",
    "txt": ".txt",
}


def send_to_kindle(path: str, title: str, to_addr: str = KINDLE_ADDR) -> bool:
    """Email a file to the Kindle address as an attachment, via AgentMail.

    The file must pass preflight_book() first: its magic bytes, its
    name and the content type Amazon receives all have to agree, and its
    metadata has to be readable from inside the file. A file that fails
    is never sent, because Amazon accepts a bad file silently.
    """
    from agentmail import AgentMail  # noqa: PLC0415
    from agentmail.attachments.types.send_attachment import SendAttachment  # noqa: PLC0415

    ok, detail = preflight_book(path)
    if not ok:
        print(f"  ! refusing to send {os.path.basename(path)}: {detail}", file=sys.stderr)
        return False

    # The content type comes from the format proven by the magic bytes,
    # never from the filename. A .epub that is really a MOBI is sent as
    # a MOBI, and Amazon sees the truth.
    ext = FORMAT_EXT[detail]
    ctype = KINDLE_CONTENT_TYPES.get(ext)
    if not ctype:
        print(f"  ! no Kindle content type for {detail}", file=sys.stderr)
        return False

    with open(path, "rb") as fh:
        raw = fh.read()
    if not raw:
        print(f"  ! refusing to send empty file {path}", file=sys.stderr)
        return False
    payload = base64.b64encode(raw).decode()

    attachment = SendAttachment(
        filename=os.path.basename(path),
        content_type=ctype,
        content_disposition="attachment",
        content=payload,
    )
    client = AgentMail(api_key=agentmail_key())
    resp = client.inboxes.messages.send(
        AGENTMAIL_INBOX,
        to=[to_addr],
        subject=title,
        text=f"{title}\n\nSent from the Dross library desk. Enjoy it.\n",
        attachments=[attachment],
    )
    # Keep the message id: it is the receipt. The sent record can be read
    # back with it to confirm the attachment left with the right
    # filename, content type and size.
    message_id = getattr(resp, "message_id", None)
    print(f"  · sent {os.path.basename(path)} ({len(payload)} b64 chars) to {to_addr}")
    if message_id:
        print(f"  · message_id: {message_id}")
    return True


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def safe_name(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "-")
    return re.sub(r"-{2,}", "-", cleaned)[:80] or "book"


def sniff_ext(path: str) -> str:
    """Detect the real format of a downloaded file from its magic bytes.

    The extension advertised by a Z-Library row is not always what you
    get, and the Gutenberg fallback always returns EPUB. Trust the bytes.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(2048)
    except Exception:
        return "bin"
    if head[:4] == b"%PDF":
        return "pdf"
    if head[:2] == b"PK":
        # EPUB is a zip whose first entry is the mimetype file.
        try:
            import zipfile

            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()[:5]
                if "mimetype" in zf.namelist():
                    with zf.open("mimetype") as mf:
                        if b"epub" in mf.read(64).lower():
                            return "epub"
                if any(n.lower().endswith(".epub") for n in names):
                    return "epub"
        except Exception:
            return "epub"
        return "zip"
    # MOBI/AZW3 are PalmDB containers: the "BOOKMOBI" or "TPZ3" marker
    # lives at offset 60, NOT at byte 0. Byte 0 holds the title/creator
    # string. Checking byte 0 makes every MOBI look like plain text.
    if head[60:68] == b"BOOKMOBI":
        return "mobi"
    if head[60:64] in (b"TPZ3", b"TPZ2", b"TPZ1"):
        return "azw3"
    # PalmDOC without the MOBI wrapper, and the old PalmDoc format.
    if head[60:68] == b"TEXtREAd":
        return "mobi"
    if head[:5] == b"{\\rtf":
        return "rtf"
    if head[:3] == b"\xef\xbb\xbf" or head[:5].lower() in (b"<!doc", b"<html"):
        return "html"
    return "txt"


def retarget_ext(path: str) -> str:
    """Rename a file so its extension matches its actual content."""
    real = sniff_ext(path)
    stem, _, ext = path.rpartition(".")
    if ext.lower() == real.lower():
        return path
    if ext.lower() in ("epub", "pdf", "mobi", "azw3", "djvu", "zip", "txt", "html", "epub3"):
        new = f"{stem}.{real}"
        try:
            os.rename(path, new)
            return new
        except OSError:
            return path
    return path


def cmd_search(args) -> int:
    opener = make_session()
    zlib_login(opener)
    rows = zlib_search(args.query, limit=args.limit, opener=opener)
    if not rows:
        print("  no zlib results")
        return 1
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    for i, row in enumerate(rows, 1):
        bits = [f"{i:>2}.", row["title"] or "(untitled)"]
        if row["author"]:
            bits.append(f"by {row['author']}")
        print("  " + " ".join(bits))
        meta = f"{row['extension'] or '?'}"
        if row["year"]:
            meta += f"  {row['year']}"
        if row["size"]:
            meta += f"  {row['size']}"
        print(f"      {meta}  id={row['id']} hash={row['hash']}")
        print(f"      {row['url']}")
    return 0


def cmd_fetch(args) -> int:
    book_id = args.book_id
    book_hash = args.hash or ""
    if "z-lib." in book_id or book_id.startswith("http"):
        parsed = urllib.parse.urlparse(book_id)
        book_id = parsed.path.rstrip("/").split("/book/")[-1]
    # The eAPI ids are bare numerics; the old web ids carried a slug.
    if "-" in book_id:
        book_id = book_id.split("-", 1)[0]
    title = args.title or book_id
    dest = args.out or os.path.join(LIBRARY_DIR, f"{safe_name(title)}.epub")
    opener = make_session()

    files = []
    if not zlib_login(opener):
        print("  · zlib: no account configured (secrets/zlib-account.txt)")
    else:
        files = zlib_files(opener, book_id, book_hash)
        if not files:
            print("  · zlib: no file list returned (login may have failed)")

    if files:
        files.sort(key=lambda f: FORMAT_RANK.get(f["extension"], 9))
        chosen = files[0]
        print(f"  · zlib: {chosen['extension']} -> {dest}")
        if download_file(opener, chosen["url"], dest):
            dest = retarget_ext(dest)
            print(f"  ✓ downloaded {os.path.getsize(dest)} bytes -> {dest}")
            return 0
        return 1

    if GUTENBERG_BANNED:
        print("  ! Project Gutenberg is banned as a source (Amre, 2026-10-30). "
              "Use Z-Library: zlib_kindle.py search then fetch.",
              file=sys.stderr)
        return 1
    gid = args.gutenberg_id or gutenberg_lookup(title)
    if not gid:
        print("  ! no zlib file and no Gutenberg id; cannot fetch", file=sys.stderr)
        return 1
    print(f"  · falling back to Project Gutenberg id {gid}")
    if gutenberg_fetch(gid, dest):
        dest = retarget_ext(dest)
        print(f"  ✓ downloaded {os.path.getsize(dest)} bytes -> {dest}")
        if dest.lower().endswith(".epub") and args.title:
            if not verify_book(dest, args.title):
                print("  ! fallback file is not the requested book", file=sys.stderr)
                return 1
        return 0
    print("  ! Gutenberg fetch failed", file=sys.stderr)
    return 1


def cmd_verify(args) -> int:
    if not os.path.isfile(args.file):
        raise SystemExit(f"no such file: {args.file}")
    return 0 if verify_book(args.file, args.title, args.author) else 1


def cmd_preflight(args) -> int:
    """Report whether a file would pass the delivery guards."""
    if not os.path.isfile(args.file):
        raise SystemExit(f"no such file: {args.file}")
    ok, detail = preflight_book(args.file, args.title, args.author)
    if ok:
        print(f"  ✓ passes preflight as {detail}")
        return 0
    print(f"  ! {detail}", file=sys.stderr)
    return 1


def cmd_send(args) -> int:
    if not os.path.isfile(args.file):
        raise SystemExit(f"no such file: {args.file}")
    title = args.title or os.path.splitext(os.path.basename(args.file))[0]
    # Repair or convert before sending. If neither rescues the file, the
    # send is refused rather than attempted.
    # A Kindle Scribe reads EPUB and PDF, never MOBI or AZW3, so a
    # Kindle-bound send must not fall back to those formats.
    fallbacks = ("pdf",) if args.to.lower().endswith("@kindle.com") else ("mobi", "azw3")
    ready, ok, notes = ensure_kindle_ready(args.file, args.expect_title,
                                            args.expect_author,
                                            fallbacks=fallbacks)
    for note in notes:
        print(f"  · {note}")
    if not ok:
        print(f"  ! refusing to send {os.path.basename(args.file)}: {notes[-1]}",
              file=sys.stderr)
        return 1
    if not send_to_kindle(ready, title, args.to):
        return 1
    return 0


def _norm_title(text: str) -> str:
    """Normalise a title for comparison: lowercase, punctuation to spaces."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


# A row that bundles several books must never win over a standalone title.
_BUNDLE_WORDS = (
    "collection", "omnibus", "box set", "boxset", "boxed set",
    "complete works", "anthology",
)


def _match_row(rows: list[dict], needle_text: str):
    """Pick the row that best matches a requested title.

    Tiers, strongest first:

    1. the title is exactly the requested title;
    2. the title starts with it ("NOS4A2" over "NOS4A2: A Novel");
    3. the title contains it, as long as it is not a bundle of books;
    4. the title contains it, bundles included.

    A plain substring test used to pick "Joe Hill Collection: Heart-Shaped
    Box, 20th Century Ghosts, Horns, and NOS4A2" for a request of
    "NOS4A2", because the collection title contains the needle.
    """
    needle = _norm_title(needle_text)
    if not needle:
        return None
    exact = starts = contains = loose = None
    for row in rows:
        hay = _norm_title(row.get("title"))
        if not hay:
            continue
        bundle = any(word in hay for word in _BUNDLE_WORDS)
        if hay == needle:
            if exact is None:
                exact = row
        elif hay.startswith(needle + " ") and not bundle:
            if starts is None:
                starts = row
        elif needle in hay:
            if bundle:
                if loose is None:
                    loose = row
            elif contains is None:
                contains = row
    return exact or starts or contains or loose


def cmd_deliver(args) -> int:
    """search -> pick -> fetch -> send."""
    opener = make_session()
    logged_in = zlib_login(opener)
    if not logged_in:
        print("  · zlib: no account configured (secrets/zlib-account.txt)")
    rows = zlib_search(args.query, limit=args.limit, opener=opener)
    if not rows:
        print("  ! nothing found on zlib", file=sys.stderr)
        return 1
    for i, row in enumerate(rows, 1):
        print(f"  {i:>2}. {row['title'] or '(untitled)'}  [{row['extension'] or '?'} {row['year'] or '?'}]")

    pick = None
    if args.match:
        pick = _match_row(rows, args.match)
        if pick is None:
            print(f"  ! no result matched {args.match!r}; using index {args.index}")
    if pick is None:
        idx = args.index or 1
        if idx < 1 or idx > len(rows):
            raise SystemExit(f"index {idx} out of range (1..{len(rows)})")
        pick = rows[idx - 1]
    print(f"  → picked: {pick['title']} ({pick['id']})")

    # A Kindle Scribe reads EPUB and PDF; it does not read MOBI or AZW3.
    # So when the destination is a Kindle address, never fall back to a
    # format the device cannot open. Elsewhere keep the old chain.
    fallbacks = ("pdf",) if args.to.lower().endswith("@kindle.com") else ("mobi", "azw3")

    # The lookup title and the email subject are separate concerns: the
    # lookup needs the bare book title, the subject may carry the author.
    lookup_title = pick["title"] or args.query
    subject = args.title or lookup_title

    # Look for a better format of the *same* title before settling for the
    # first hit. For a Kindle Scribe that format is EPUB, not AZW3: the
    # device cannot open MOBI or AZW3, so a file sent in either of those
    # formats arrives nowhere.
    if args.format:
        want = args.format.lower()
    elif args.to.lower().endswith("@kindle.com"):
        # Kindle Scribe cannot read MOBI or AZW3, so EPUB is the format
        # that actually reaches the device.
        want = "epub"
    else:
        want = ""
    if want and pick["extension"].lower() != want:
        alt_rows = zlib_search(args.query, limit=args.limit * 2, opener=opener,
                               extensions=[want])
        alts = [r for r in alt_rows if r["extension"].lower() == want]
        alt = _match_row(alts, pick["title"] or "")
        if alt is not None:
            print(f"  → same title available as {want.upper()}; switching")
            pick = alt
    # Start with the advertised extension; retarget_ext() corrects it from
    # the real magic bytes once the file is on disk.
    dest = os.path.join(
        LIBRARY_DIR, f"{safe_name(subject)}.{pick['extension'].lower() or 'epub'}"
    )
    files = zlib_files(opener, pick["id"], pick.get("hash", "")) if logged_in else []
    if files:
        # Rank the available formats for the destination. For a Kindle
        # address that means EPUB first — the Scribe reads EPUB natively,
        # and MOBI/AZW3 rank last because it cannot open them at all.
        rank = KINDLE_FORMAT_RANK if args.to.lower().endswith("@kindle.com") else FORMAT_RANK
        files.sort(key=lambda f: rank.get(f["extension"], 9))
        if download_file(opener, files[0]["url"], dest):
            dest = retarget_ext(dest)
            print(f"  ✓ {os.path.getsize(dest)} bytes -> {dest}")
            # The download is a real file of a real format, but it may
            # not be the book that was asked for. Confirm the title
            # inside the file before it goes to Amazon's converter.
            expect_title = args.expect_title or lookup_title
            expect_author = args.expect_author or pick.get("author")
            if not verify_book(dest, expect_title, expect_author):
                print("  ! downloaded file is not the requested book; not sending it",
                      file=sys.stderr)
                return 1
            # Preflight, repair and conversion happen here so that only a
            # file Amazon's converter will actually accept is sent.
            ready, ok, notes = ensure_kindle_ready(dest, expect_title, expect_author,
                                                 fallbacks=fallbacks)
            for note in notes:
                print(f"  · {note}")
            if not ok:
                print(f"  ! refusing to send {os.path.basename(dest)}: {notes[-1]}",
                      file=sys.stderr)
                return 1
            if not send_to_kindle(ready, subject, args.to):
                return 1
            return 0

    gid = gutenberg_lookup(lookup_title)
    if gid and gutenberg_fetch(gid, dest):
        dest = retarget_ext(dest)
        print(f"  ✓ Gutenberg id {gid}: {os.path.getsize(dest)} bytes -> {dest}")
        # A wrong Gutenberg id resolves to a real EPUB of a different book.
        # The zip magic bytes cannot catch that; the title inside can.
        if dest.lower().endswith(".epub") and not verify_book(dest, lookup_title):
            print("  ! fallback file is not the requested book; not sending it",
                  file=sys.stderr)
            return 1
        ready, ok, notes = ensure_kindle_ready(dest, lookup_title,
                                             fallbacks=fallbacks)
        for note in notes:
            print(f"  · {note}")
        if not ok:
            print(f"  ! refusing to send {os.path.basename(dest)}: {notes[-1]}",
                  file=sys.stderr)
            return 1
        if not send_to_kindle(ready, subject, args.to):
            return 1
        return 0
    print("  ! could not obtain a downloadable file", file=sys.stderr)
    return 1


def cmd_account(args) -> int:
    """Report whether Z-Library credentials are configured. Never prints them."""
    creds = read_zlib_creds()
    if not creds:
        print("  zlib account: NOT configured")
        print(f"  add it to {os.path.join(SECRETS, 'zlib-account.txt')} as email:password")
        return 1
    email, _ = creds
    print(f"  zlib account: configured ({email})")
    return 0


def cmd_books(args) -> int:
    for title, gid in sorted(GUTENBERG_IDS.items(), key=lambda kv: kv[0].lower()):
        print(f"  {title:<32} gutenberg={gid}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("search", help="search Z-Library")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true", help="emit JSON rows")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("fetch", help="download one book to the local library")
    p.add_argument("book_id")
    p.add_argument("--hash", default="", help="eAPI book hash (from search output)")
    p.add_argument("--title")
    p.add_argument("--out")
    p.add_argument("--gutenberg-id", type=int)
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("send", help="email a file to the Kindle address")
    p.add_argument("file")
    p.add_argument("--title")
    p.add_argument("--to", default=KINDLE_ADDR)
    p.add_argument("--expect-title", help="title the file must actually carry")
    p.add_argument("--expect-author", help="author the file must actually carry")
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("preflight", help="check a file against the delivery guards")
    p.add_argument("file")
    p.add_argument("--title", help="the title the book should have")
    p.add_argument("--author", help="the author the book should have")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("deliver", help="search, download, and send in one go")
    p.add_argument("query")
    p.add_argument("--index", type=int, default=1)
    p.add_argument("--match", help="pick the result whose title best matches this")
    p.add_argument("--title", help="override the email subject / filename")
    p.add_argument("--format", help="prefer this extension (default: azw3 for Kindle)")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--to", default=KINDLE_ADDR)
    p.add_argument("--expect-title",
                   help="title the downloaded file must actually contain")
    p.add_argument("--expect-author",
                   help="author the downloaded file must actually carry")
    p.set_defaults(func=cmd_deliver)

    p = sub.add_parser("verify", help="check that an EPUB is the book that was requested")
    p.add_argument("file")
    p.add_argument("--title", help="the title the book should have")
    p.add_argument("--author", help="the author the book should have")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("account", help="check whether zlib credentials are configured")
    p.set_defaults(func=cmd_account)

    p = sub.add_parser("books", help="list curated titles with Gutenberg ids")
    p.set_defaults(func=cmd_books)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
