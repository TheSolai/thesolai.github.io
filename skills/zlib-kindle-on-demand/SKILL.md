---
name: zlib-kindle-on-demand
description: On-demand Z-Library book delivery to Kindle. Find a book on Z-Library, download it to the Mac, and email it to the Kindle address via AgentMail. Invoke explicitly when Amre asks for a specific book right now.
disable-model-invocation: true
user-invocable: true
metadata:
  {
    "openclaw": {
      "requires": {
        "bins": ["python3"]
      }
    }
  }
---

# Z-Library → Kindle (on demand)

Explicit-invocation variant of the `zlib-kindle` skill. This one is hidden
from the model's normal prompt, so it only runs when Amre asks for a book
directly. The machinery is shared — same script, same rules.

## Run it

```bash
export PATH="/opt/homebrew/bin:$PATH"
cd {baseDir}/../zlib-kindle/scripts

# Full pipeline: search → download → email to amrekin@kindle.com
python3 zlib_kindle.py deliver "<title> <author>" --index 1

# Or step by step
python3 zlib_kindle.py search "<title> <author>" --limit 6
python3 zlib_kindle.py fetch <book-id> --hash <hash-from-search>
python3 zlib_kindle.py send ~/Downloads/dross-books/<file> --title "<Title> by <Author>"
```

## What it does

1. Searches Z-Library for the title through the eAPI on `z-lib.by`.
2. Picks the requested result (default: the first).
3. For a `@kindle.com` destination, switches to the same title in a
   Kindle-native format (AZW3/MOBI) when one exists.
4. Downloads it to `~/Downloads/dross-books/`, renaming the file to match
   its real bytes.
5. Emails it to `amrekin@kindle.com` as an attachment, via the AgentMail
   inbox `thedross@agentmail.to`.

**Check the printed filename after the download.** Z-Library's advertised
extension is unreliable, and a file with the wrong extension is exactly
what Amazon will refuse to convert. MOBI/AZW3 carry their `BOOKMOBI`/
`TPZ3` marker at byte 60, not byte 0.

**The extension also picks the MIME type, and Python's `mimetypes` does
not know the ebook formats Kindle cares about.** It returns `None` for
`.azw3` and `.epub3`, so a naive send goes out as
`application/octet-stream` and Amazon replies `E009 - No Attachment` —
which reads like a missing file but is really a mislabelled or empty
attachment. The script maps the extensions explicitly and refuses an
empty file locally, before anything is sent.

**Amazon accepts a file silently or not at all, so every check happens
before the send.** On 2026-10-29 a valid, DRM-free EPUB of *The
Haunting of Hill House* was sent and never arrived: its OPF package root
used a prefixed `<opf:package xmlns:opf="...">` instead of the default
`<package xmlns="http://www.idpf.org/2007/opf">`, which Amazon's
converter drops without a word. Every EPUB that *did* arrive used the
default form. The guards now enforce this on every send: magic bytes,
filename extension, content type and EPUB namespace must all agree, the
file must be non-empty, and title and author must be readable from inside
it. A file that fails is repaired (OPF namespace rewritten) or converted
with Calibre; one that cannot be rescued is never sent. Check any file
by hand with:

```bash
python3 zlib_kindle.py preflight ~/Downloads/dross-books/BOOK.epub \
  --title "The Haunting of Hill House" --author "Shirley Jackson"
```

**The `PK` zip check does not prove the file is the right book.** A wrong
Gutenberg id resolves to a real EPUB of a completely different book.
`deliver` and `fetch` check `dc:title`/`dc:creator` inside the EPUB
before sending, and `verify` runs the same check on demand:

```bash
python3 zlib_kindle.py verify ~/Downloads/dross-books/BOOK.epub \
  --title "The Great God Pan" --author "Arthur Machen"
```

If the title inside the file is not the book that was requested, treat
the fallback as failed — do not send it, and do not quietly substitute a
different book with the same title.

**The sent record is the receipt.** A script that printed "sent" is not
proof. Read the sent record and check the attachment's filename,
content type and byte count:

```bash
~/.openclaw/tools/node-v24.21.0/bin/openclaw agentmail inboxes:messages list \
  --inbox-id thedross@agentmail.to --subject "<title>" --format json
```

Use the **gateway's own binary**, not `openclaw` from `PATH` — the
`agentmail` command does not exist in the stale PATH build
(`/opt/homebrew/bin/openclaw`, 2026.6.35), which fails with
`Unknown command: openclaw agentmail`.

## Before you start

Z-Library serves file lists only to signed-in accounts. Check:

```bash
python3 zlib_kindle.py account
```

If it reports **NOT configured**, downloads of in-copyright titles will
fail. Amre needs to create `~/.openclaw/workspace/secrets/zlib-account.txt`
containing `email:password` (mode `600`, inside a git-ignored directory).
Public-domain titles still work without an account — the script falls back
to Project Gutenberg.

The account is currently configured and the eAPI sign-in works, so the
download step should succeed. If it does not, report the failing step
rather than retrying blindly.

## Rules

- Never print the Z-Library password or the AgentMail API key.
- Use `/opt/homebrew/bin/python3` (Homebrew); system python lacks the
  `agentmail` module.
- Do not email a file that failed to download. The script verifies EPUB
  zip magic bytes before saving, and verifies the title inside the EPUB
  before sending.
- Never print the Z-Library password or the AgentMail API key.
- Do not loop the script to test it — one run is one Z-Library login, and
  repeated runs trip the login rate limit.
- Report which step failed if anything breaks — do not claim a delivery
  that did not happen.
