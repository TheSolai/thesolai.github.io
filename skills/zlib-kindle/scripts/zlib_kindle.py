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

ZLIB_BASE = "https://z-lib.id"
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
# Z-Library: search
# --------------------------------------------------------------------------
def _parse_row(book_id: str, chunk: str) -> dict:
    """Pull title/author/format/year out of one Z-Library search row.

    The live markup uses schema.org attributes: itemprop="name" for the
    title link, itemprop="author" for the author, and a
    property__file / property_year block for the format and year.
    """
    def prop(pattern, group=1):
        m = re.search(pattern, chunk, re.S)
        return re.sub(r"\s+", " ", m.group(group)).strip() if m else ""

    title = prop(r'<h3[^>]*itemprop="name"[^>]*>\s*<a[^>]*>([^<]{1,200})</a>')
    if not title:
        title = prop(r'<a href="/book/[^"]*"[^>]*>([^<]{1,200})</a>')
    author = prop(r'itemprop="author"[^>]*>([^<]{1,120})</a>')
    publisher = prop(r'itemprop="publisher"[^>]*>([^<]{1,120})</a>')
    # Each property block is: <div class="bookProperty property_X"> <div
    # class="property_label">Label:</div> <div class="property_value ">VALUE</div>
    # so the value div is not adjacent to the property name.
    ext = prop(r'property__file".*?property_value[^"]*"[^>]*>([^<]{1,12})<')
    year = prop(r'property_year".*?property_value[^"]*"[^>]*>([^<]{1,12})<')
    language = prop(r'property_language".*?property_value[^"]*"[^>]*>([^<]{1,24})<')
    size = prop(r'([\d.]+\s?(?:KB|MB|GB))')
    return {
        "id": book_id,
        "title": title,
        "author": author,
        "publisher": publisher,
        "extension": ext.upper(),
        "size": size,
        "year": year,
        "language": language,
        # "archive/" ids are bibliographic-only records with no file list.
        "has_files": not book_id.startswith("archive/"),
        "url": f"{ZLIB_BASE}/book/{book_id}",
        "source": "zlib",
    }


def _row_blocks(html: str) -> list[tuple[str, str]]:
    """Split a search page into per-result (book_id, markup) chunks.

    A result row nests a table inside the outer <tr>, so a non-greedy
    </tr> match truncates before the format/year property block. Slice
    between successive row starts instead.
    """
    starts = [m.start() for m in re.finditer(r'<tr[^>]*class="bookRow"', html)]
    out: list[tuple[str, str]] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(len(html), start + 9000)
        chunk = html[start:end]
        bid = re.search(r'data-book_id="([^"]+)"', chunk)
        if bid:
            out.append((bid.group(1), chunk))
    return out


def zlib_search(query: str, limit: int = 10) -> list[dict]:
    """Search Z-Library and return parsed book rows."""
    opener = make_session()
    url = f"{ZLIB_BASE}/s/?q={urllib.parse.quote(query)}"
    status, body, _ = fetch(opener, url)
    if status != 200:
        print(f"  ! zlib search failed: http={status}", file=sys.stderr)
        return []
    html = text_of(body)

    rows: list[dict] = []
    for book_id, chunk in _row_blocks(html):
        rows.append(_parse_row(book_id, chunk))
        if len(rows) >= limit:
            break

    # Z-Library paginates; the second page uses ?page=
    if len(rows) < limit:
        status2, body2, _ = fetch(opener, f"{url}&page=2")
        if status2 == 200:
            for book_id, chunk in _row_blocks(text_of(body2)):
                if any(r["id"] == book_id for r in rows):
                    continue
                rows.append(_parse_row(book_id, chunk))
                if len(rows) >= limit:
                    break
    return rows


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
    """Sign in to Z-Library. Returns True on success."""
    creds = read_zlib_creds()
    if not creds:
        return False
    email, password = creds
    status, body, _ = fetch(opener, f"{ZLIB_BASE}/login")
    if status != 200:
        return False
    token = ""
    m = re.search(r'name="_token"\s+value="([^"]+)"', text_of(body))
    if m:
        token = m.group(1)
    data = urllib.parse.urlencode(
        {"_token": token, "email": email, "password": password, "remember": "1"}
    ).encode()
    status, _, _ = fetch(
        opener,
        f"{ZLIB_BASE}/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    status, body, _ = fetch(
        opener, f"{ZLIB_BASE}/api/auth-status", headers={"Accept": "application/json"}
    )
    if status == 200 and '"authenticated":true' in text_of(body).replace(" ", ""):
        print("  · zlib: signed in")
        return True
    print("  · zlib: sign-in did not take", file=sys.stderr)
    return False


def zlib_files(opener, book_id: str) -> list[dict]:
    """Return the downloadable file list for a book id (needs a session)."""
    status, body, final = fetch(opener, f"{ZLIB_BASE}/book/{book_id}")
    if status != 200:
        return []
    html = text_of(body)
    if 'href="/login"' in html and "dlButton" in html:
        return []  # not signed in
    found = []
    for m in re.finditer(
        r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*addDownloadedBook[^"]*"[^>]*'
        r'(?:.*?book-property__extension[^>]*>([^<]{1,12})<)?',
        html,
        re.S,
    ):
        href = m.group(1)
        if not any(href.lower().endswith(ext) for ext in (".epub", ".mobi", ".pdf", ".azw3", ".djvu")):
            continue
        ext = (m.group(2) or href.rsplit(".", 1)[-1]).strip().lower()
        found.append({"url": urllib.parse.urljoin(final, href), "extension": ext})
    if not found:
        # Fall back to any direct file hrefs in the page.
        for m in re.finditer(r'href="([^"]+\.(?:epub|mobi|pdf|azw3|djvu)[^"]*)"', html):
            found.append(
                {
                    "url": urllib.parse.urljoin(final, m.group(1)),
                    "extension": m.group(1).rsplit(".", 1)[-1].lower(),
                }
            )
    return found


def download_file(opener, url: str, dest: str) -> bool:
    status, body, _ = fetch(opener, url, timeout=300)
    if status != 200 or not body:
        print(f"  ! download failed http={status}: {url}", file=sys.stderr)
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
    if head[:4] == b"BOOKMOBI":
        return "mobi"
    if head[58:62] == b"TPZ3" or head[60:64] == b"TPZ3":
        return "azw3"
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
    if ext.lower() in ("epub", "pdf", "mobi", "azw3", "djvu", "zip", "txt", "html"):
        new = f"{stem}.{real}"
        try:
            os.rename(path, new)
            return new
        except OSError:
            return path
    return path


def cmd_search(args) -> int:
    rows = zlib_search(args.query, limit=args.limit)
    if not rows:
        print("  no zlib results")
        return 1
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
        print(f"      {meta}  {row['id']}")
        print(f"      {row['url']}")
    return 0


def cmd_fetch(args) -> int:
    book_id = args.book_id
    if "z-lib." in book_id or book_id.startswith("http"):
        parsed = urllib.parse.urlparse(book_id)
        book_id = parsed.path.rstrip("/").split("/book/")[-1]
    title = args.title or book_id
    dest = args.out or os.path.join(LIBRARY_DIR, f"{safe_name(title)}.epub")
    opener = make_session()

    files = []
    if not zlib_login(opener):
        print("  · zlib: no account configured (secrets/zlib-account.txt)")
    else:
        files = zlib_files(opener, book_id)
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


def cmd_deliver(args) -> int:
    """search -> pick -> fetch -> send."""
    rows = zlib_search(args.query, limit=args.limit)
    if not rows:
        print("  ! nothing found on zlib", file=sys.stderr)
        return 1
    for i, row in enumerate(rows, 1):
        print(f"  {i:>2}. {row['title'] or '(untitled)'}  [{row['extension'] or '?'} {row['year'] or '?'}]")

    pick = None
    if args.match:
        needle = re.sub(r"[^a-z0-9]+", " ", args.match.lower()).strip()
        for row in rows:
            hay = re.sub(r"[^a-z0-9]+", " ", (row["title"] or "").lower()).strip()
            if needle and (needle in hay or hay in needle):
                pick = row
                break
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
    # Start with the advertised extension; retarget_ext() corrects it from
    # the real magic bytes once the file is on disk.
    dest = os.path.join(
        LIBRARY_DIR, f"{safe_name(subject)}.{pick['extension'].lower() or 'epub'}"
    )
    opener = make_session()
    logged_in = zlib_login(opener)
    if not logged_in:
        print("  · zlib: no account configured (secrets/zlib-account.txt)")
    files = zlib_files(opener, pick["id"]) if logged_in else []
    if files:
        files.sort(key=lambda f: FORMAT_RANK.get(f["extension"], 9))
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
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("fetch", help="download one book to the local library")
    p.add_argument("book_id")
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
