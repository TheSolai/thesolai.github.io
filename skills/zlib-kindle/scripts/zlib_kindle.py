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
import mimetypes
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

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

# Curated horror list -> Project Gutenberg id where the title is public domain.
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
    "The Canterville Ghost": 158,
    "The Woman in White": 653,
    "The Moonstone": 645,
    "The Invisible Man": 35,
    "The Time Being": 35,
    "The Haunting of Hill House": 3,
}

FORMAT_RANK = {"epub": 0, "epub3": 0, "mobi": 1, "azw3": 2, "pdf": 3, "djvu": 4, "txt": 5}

# Kindle reads AZW3 natively and needs no conversion, so a Kindle-bound
# fetch prefers it over EPUB even though EPUB is the better general format.
KINDLE_FORMAT_RANK = {"azw3": 0, "epub": 1, "epub3": 1, "mobi": 2, "pdf": 3, "txt": 4, "djvu": 5}


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


def send_to_kindle(path: str, title: str, to_addr: str = KINDLE_ADDR) -> bool:
    """Email a file to the Kindle address as an attachment, via AgentMail."""
    from agentmail import AgentMail  # noqa: PLC0415
    from agentmail.attachments.types.send_attachment import SendAttachment  # noqa: PLC0415

    ctype, _ = mimetypes.guess_type(path)
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    payload = base64.b64encode(open(path, "rb").read()).decode()

    attachment = SendAttachment(
        filename=os.path.basename(path),
        content_type=ctype or "application/octet-stream",
        content_disposition="attachment",
        content=payload,
    )
    client = AgentMail(api_key=agentmail_key())
    client.inboxes.messages.send(
        AGENTMAIL_INBOX,
        to=[to_addr],
        subject=title,
        text=f"{title}\n\nSent from the Dross library desk. Enjoy it.\n",
        attachments=[attachment],
    )
    print(f"  · sent {os.path.basename(path)} ({len(payload)} b64 chars) to {to_addr}")
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

    gid = args.gutenberg_id or gutenberg_lookup(title)
    if not gid:
        print("  ! no zlib file and no Gutenberg id; cannot fetch", file=sys.stderr)
        return 1
    print(f"  · falling back to Project Gutenberg id {gid}")
    if gutenberg_fetch(gid, dest):
        dest = retarget_ext(dest)
        print(f"  ✓ downloaded {os.path.getsize(dest)} bytes -> {dest}")
        return 0
    print("  ! Gutenberg fetch failed", file=sys.stderr)
    return 1


def cmd_send(args) -> int:
    if not os.path.isfile(args.file):
        raise SystemExit(f"no such file: {args.file}")
    title = args.title or os.path.splitext(os.path.basename(args.file))[0]
    send_to_kindle(args.file, title, args.to)
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

    # The lookup title and the email subject are separate concerns: the
    # lookup needs the bare book title, the subject may carry the author.
    lookup_title = pick["title"] or args.query
    subject = args.title or lookup_title

    # Kindle wants AZW3 when the same edition exists in it, so look for a
    # better format of the *same* title before settling for the first hit.
    if args.format:
        want = args.format.lower()
    elif args.to.lower().endswith("@kindle.com"):
        want = "azw3"
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
        # A Kindle-native format avoids Amazon's conversion step, so rank
        # for it when the destination is a Kindle address.
        rank = KINDLE_FORMAT_RANK if args.to.lower().endswith("@kindle.com") else FORMAT_RANK
        files.sort(key=lambda f: rank.get(f["extension"], 9))
        if download_file(opener, files[0]["url"], dest):
            dest = retarget_ext(dest)
            print(f"  ✓ {os.path.getsize(dest)} bytes -> {dest}")
            send_to_kindle(dest, subject, args.to)
            return 0

    gid = gutenberg_lookup(lookup_title)
    if gid and gutenberg_fetch(gid, dest):
        dest = retarget_ext(dest)
        print(f"  ✓ Gutenberg id {gid}: {os.path.getsize(dest)} bytes -> {dest}")
        send_to_kindle(dest, subject, args.to)
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
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("deliver", help="search, download, and send in one go")
    p.add_argument("query")
    p.add_argument("--index", type=int, default=1)
    p.add_argument("--match", help="pick the result whose title best matches this")
    p.add_argument("--title", help="override the email subject / filename")
    p.add_argument("--format", help="prefer this extension (default: azw3 for Kindle)")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--to", default=KINDLE_ADDR)
    p.set_defaults(func=cmd_deliver)

    p = sub.add_parser("account", help="check whether zlib credentials are configured")
    p.set_defaults(func=cmd_account)

    p = sub.add_parser("books", help="list curated titles with Gutenberg ids")
    p.set_defaults(func=cmd_books)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
