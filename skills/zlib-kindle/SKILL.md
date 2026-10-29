---
name: zlib-kindle
description: Find a book on Z-Library, download it to the Mac, and email it to the Kindle address as an attachment via AgentMail. Use when Amre asks for a book, a download, a Kindle delivery, or a horror book pick.
metadata:
  {
    "openclaw": {
      "requires": {
        "bins": ["python3"]
      }
    }
  }
---

# Z-Library → Mac → Kindle

Find a book, download it locally, and deliver it to the Kindle send-to
address as an email attachment.

**Delivery path: AgentMail** (the Dross inbox, `thedross@agentmail.to`).
AgentMail accepts base64 attachments, which is exactly what Amazon's
Send-to-Kindle address wants. Do **not** use raw SMTP for this — the
`send-kindle.py` script in `scripts/engagement/` does, and it works, but
AgentMail is the requested path and gives a clean message-id receipt.

## The script

Everything is driven by one script: `{baseDir}/scripts/zlib_kindle.py`

```bash
export PATH="/opt/homebrew/bin:$PATH"   # Homebrew python has the agentmail module
cd {baseDir}/scripts
```

## Commands

| Command | What it does |
|---|---|
| `python3 zlib_kindle.py search "<query>"` | List Z-Library matches with format, year, id, hash, URL |
| `python3 zlib_kindle.py search "<query>" --json` | Same, as JSON rows |
| `python3 zlib_kindle.py fetch <book-id> --hash <hash>` | Download one book to `~/Downloads/dross-books/` |
| `python3 zlib_kindle.py send <file> --title "..."` | Email a file to the Kindle address |
| `python3 zlib_kindle.py deliver "<query>"` | **The whole pipeline** — search → fetch → send |
| `python3 zlib_kindle.py account` | Check whether Z-Library credentials are configured |
| `python3 zlib_kindle.py books` | List curated titles with their Project Gutenberg ids |
| `python3 zlib_kindle.py verify <file> --title "..."` | Check that an EPUB is the book that was requested |
| `python3 zlib_kindle.py preflight <file> --title "..."` | Check a file against every delivery guard |

`search` prints the **hash** next to each id. Pass it to `fetch` with
`--hash` — the eAPI resolves a book by the (id, hash) pair, so a bare id
is not enough.

## Typical flow

```bash
cd {baseDir}/scripts
python3 zlib_kindle.py search "The Fisherman John Langan" --limit 6
python3 zlib_kindle.py deliver "The Fisherman John Langan" --index 1
```

`deliver` picks the first result, downloads it, and emails it to
`amrekin@kindle.com`. Use `--index N` to choose a different hit and
`--to <address>` to override the destination.

**Kindle Scribe reads EPUB, not MOBI/AZW3.** When the destination is a
`@kindle.com` address, `deliver` looks for the same title as an EPUB and
switches to it automatically; PDF is the only other format it falls back
to. MOBI and AZW3 are deliberately ranked *last* for Kindle destinations
because the Scribe cannot open them — sending one produces a book that
silently never appears on the device. Override with
`--format epub|pdf|mobi|azw3`.

The Kindle format rank lives in `KINDLE_FORMAT_RANK`; the general one in
`FORMAT_RANK`. Both `cmd_deliver` and `cmd_send` branch on the
destination address, so a non-Kindle destination keeps the old
MOBI/AZW3 behaviour.

**Trust the bytes, not the label.** Z-Library's advertised extension is
often wrong — an "AZW3" row can serve MOBI bytes, and a MOBI downloaded
as `.txt` is exactly what Amazon refuses to convert. `sniff_ext()` reads
magic bytes and `retarget_ext()` renames the file to match, so check the
printed filename after every download. MOBI/AZW3 are PalmDB containers:
the `BOOKMOBI`/`TPZ3` marker sits at **byte 60**, not byte 0.

**The extension also picks the MIME type, and Python's `mimetypes` does
not know the ebook formats Kindle cares about.** It returns `None` for
`.azw3` and `.epub3`, so a naive send goes out as
`application/octet-stream`. Amazon's reply to that is `E009 - No
Attachment` — which reads like a missing file but is really a mislabelled
or empty attachment. The script maps the extensions explicitly and
refuses an empty file locally, before anything is sent:

| Extension | Content type |
|---|---|
| `.azw3` | `application/vnd.amazon.ebook` |
| `.mobi` | `application/x-mobipocket-ebook` |
| `.epub`, `.epub3` | `application/epub+zip` |
| `.pdf` | `application/pdf` |
| `.txt` | `text/plain` |

Verified 2026-09-29: the Amazon rejection dated `Tue, 29 Sep 2026
19:59:52 +0000`, subject "There was a problem with the document(s) that
you sent to Kindle", carried `E009 - No Attachment`. That is an
attachment-labelling failure, not an invalid book format — when you see
E009, look at the content type and the file size, not at the book's
format.

## The delivery guards — why a book can vanish with no error

**Amazon's Send-to-Kindle accepts a file silently or not at all.** It
sends no confirmation and no rejection. A file it will not take simply
never appears on the device, and nothing in the mail tells you. So every
check has to happen *before* the send, not after.

On 2026-10-29 this cost a real book: *The Haunting of Hill House* was
sent as an EPUB and never arrived. The EPUB was a valid zip, parsed
cleanly, carried correct metadata, had no DRM, and had a perfectly good
`META-INF/container.xml`. Its defect was one line in the OPF package
document:

```xml
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" ...>
```

The package root carried the OPF namespace as a **prefix** instead of as
the **default** namespace:

```xml
<package xmlns="http://www.idpf.org/2007/opf" ...>
```

Every EPUB that *did* arrive (NOS4A2, The Fisherman, The Great God Pan,
The King in Yellow) used the default form. The one that did not arrive
used the prefixed form. An XML parser expands prefixes and reports both
as "in the OPF namespace", which is exactly why this hides from a
normal validity check — and Amazon's converter drops the prefixed form
without a word.

The guards now run on every `send` and every `deliver`. A file must
pass all of these or it is never sent:

| Guard | What it enforces |
|---|---|
| `preflight_book` | Magic bytes, filename extension, and the content type Amazon receives all agree |
| `preflight_book` | The file is non-empty |
| `preflight_book` | The EPUB's OPF root uses the **default** OPF namespace |
| `preflight_book` | Title and author are readable **from inside** the file, and match what was asked for |
| `preflight_book` | An expected author that the file cannot state is a **failure**, not a pass |

The content type is derived from the format proven by the magic bytes,
never from the filename. An EPUB named `.mobi` is refused rather than
mislabelled, because a mislabelled attachment is exactly what produced
Amazon's `E009 - No Attachment`.

**A bad file is repaired, not just refused.** `ensure_kindle_ready()`
runs before the send:

1. If the EPUB's OPF root is prefixed, `repair_epub_namespace()` writes a
   corrected copy with the default namespace (the original file is never
   modified) and the book is sent as that copy.
2. If repair is not enough, `calibre_convert()` converts the book with
   Calibre's `ebook-convert`. The fallback format depends on the
   destination: **PDF for a Kindle address** (Scribe-readable), MOBI or
   AZW3 elsewhere. Never let a Kindle-bound repair fall back to MOBI or
   AZW3 — the file would send cleanly and still never reach the device.
3. If neither rescues the file, the send is **refused**. Nothing is
   emailed, and the book is not recorded as delivered.

Check a file by hand any time:

```bash
python3 zlib_kindle.py preflight ~/Downloads/dross-books/BOOK.epub \
  --title "The Haunting of Hill House" --author "Shirley Jackson"
```

The guard suite lives at `tests/test_delivery_guards.py` and runs
offline against synthetic files and the real library:

```bash
python3 tests/test_delivery_guards.py
```

## Z-Library needs an account

Z-Library serves its **file list only to signed-in users**. Search works
without an account, but resolving a download link does not: the eAPI
`/eapi/book/<id>/<hash>/file` call only returns a link for a session that
signed in. The script signs in on every run, before searching.

To enable downloads, put the account in:

```
~/.openclaw/workspace/secrets/zlib-account.txt
```

Format — one line, `email:password` (or email on line 1, password on line 2).
The file is inside `secrets/`, which is git-ignored, so it will never be
committed. `secrets/zlib-account.txt` is mode `600`.

Check it with `python3 zlib_kindle.py account` — that command reports
whether an account exists and never prints the password.

**Without an account**, the fetcher falls back to Project Gutenberg for
public-domain titles, so the pipeline still completes end to end for those.
In-copyright titles will fail at the download step with a clear error
rather than silently producing nothing.

## Project Gutenberg fallback

Titles in `GUTENBERG_IDS` map to numeric Gutenberg ids and are fetched
directly from `gutenberg.org`. The script also queries `gutendex.com` to
resolve ids it does not know. EPUB is preferred; the fetch verifies the
file starts with the `PK` zip magic bytes before saving.

**Verify the book's content, not just its bytes.** The `PK` check proves
the file is a zip; it does not prove it is the book that was requested. A
wrong Gutenberg id resolves to a real EPUB of a completely different
book. Four curated ids did exactly that before the fix — Canterville
Ghost, Woman in White, Moonstone and Invisible Man each pointed at an
unrelated title.

`deliver` and `fetch` now check the title inside the EPUB before sending
it, and `verify` runs the same check on demand:

```bash
python3 zlib_kindle.py verify ~/Downloads/dross-books/BOOK.epub \
  --title "The Great God Pan" --author "Arthur Machen"
```

The check reads `dc:title` and `dc:creator` out of the EPUB's OPF file.
Two traps in that:

- The `.opf` path is not fixed. It is `content.opf` at the archive root in
  some books and `OEBPS/content.opf` in others, so locate it with
  `unzip -l` instead of hardcoding a path.
- `<dc:creator>` usually carries attributes — `<dc:creator
  opf:file-as="Langan, John" opf:role="aut">` or `<dc:creator
  id="author_0">`. The pattern has to tolerate them. A bare `<dc:creator>`
  pattern matches nothing and silently hides the author.

Compare names by token set, not by substring: Z-Library stores `Hill, Joe`
where the request says `Joe Hill`, and the eAPI packs title and author
together as `Hill, Joe - NOS4A2`. A check that rejects a correct book is
worse than no check, so the comparison accepts either ordering.

If the title inside the file is not the book that was requested, treat
the fallback as failed — do not send it.

## The Friday horror cron — the standing contract

The weekly book delivery is a scheduled job, not a manual run. Its
contract, verified against the live cron on 2026-10-24:

| Field | Required value |
|---|---|
| Command | `horror-book.sh --send` |
| Session | `isolated` |
| Enabled | yes |
| Command timeout | 300 seconds |
| Schedule | `0 18 * * 5` Europe/London |

`--send` is what makes the cron download the book and email it to
`amrekin@kindle.com`; without it the script only prints a
recommendation and delivers nothing.

**The weekly book announcement is the only cron permitted to deliver
user-facing Telegram output.** Other engagement crons may announce, but
if book delivery and another announcement job both speak for the books,
the pipeline starts talking over itself.

When the cron fires, the delivery is still only complete once the
attachment is right. The Friday job runs unattended, so the
content checks matter more there than anywhere else: a wrong book in the
Gutenberg fallback would go out silently, once a week, to the Kindle
address. `deliver` verifies the title inside the EPUB before sending,
and every file passes the delivery guards before it is attached. A file
that fails is repaired or converted; a file that cannot be rescued is
not sent at all.

If the Friday run fails, report the failing step rather than retrying
the script in a loop — each run is a Z-Library login, and the login
rate limit will block the next attempt as well as the real delivery.

## Books that are public domain

These have known Gutenberg ids and work without any Z-Library account:

- The King in Yellow (8492), Carmilla (10007), The Call of Cthulhu (68283)
- At the Mountains of Madness (70652), The Great God Pan (389)
- The House of Souls (25016), The Turn of the Screw (209)
- The Yellow Wallpaper (1952), The Picture of Dorian Gray (174)
- Dracula (345), The Time Machine (35), Frankenstein (84)

## Account limits — the two that bite

The Z-Library account has hard limits, and both are enforced server-side
with a JSON body rather than an HTTP error code:

- **Daily download cap: 10 downloads/day.** When it is reached the eAPI
  still answers `success: 1` but withholds the download link, with
  `allowDownload: false` and a `disallowDownloadMessage` explaining the
  wait. The script prints that message.

  The cap is **account-wide and cumulative for the rolling day**, not
  per-title and not per-run. Reaching it is not a failure of the title
  that happened to trip it — every later title in the same batch would
  be refused too. `batch_deliver.py` therefore detects the refusal
  (`zlib_kindle.quota_exhausted()`), stops the run immediately, and
  **exits 3** with the resume file intact. Do not treat exit 3 as an
  error and do not re-run the batch to "retry" it: the next run will
  simply hit the same wall. Wait for the counter to reset instead.

  The resume file is what makes a multi-day backlog work: a re-run
  skips every title already marked done and picks up at the first
  undelivered one.
- **Login rate limit.** Every script run performs one sign-in, and too
  many in quick succession returns `Too many logins #N. Try again
  later.` Do not re-run the script in a loop to test it — one run is
  one login, and repeated probing trips the limit and blocks the real
  delivery as well.

When a run fails, read the stderr message before retrying. The script
surfaces the server's own explanation rather than a bare `http 400`.

## Rules

- **Never print the Z-Library password or the AgentMail API key.** The
  script reads both from disk and logs neither.
- **Use the Homebrew python** (`/opt/homebrew/bin/python3`). System python
  has no `agentmail` module.
- **Verify the download** before emailing: the script checks the zip magic
  bytes for EPUBs. Do not email a file that failed to download.
- **Report honestly.** If a title could not be downloaded, say which step
  failed rather than claiming delivery.
- A **no-bounce check** is the real delivery signal. SMTP sends do not
  appear in the IMAP Sent folder, so absence there proves nothing.
- **One script run is one Z-Library login.** Do not loop the script to
  test it — repeated runs trip the login rate limit.
- **Run long batches as a tracked foreground `exec`** and poll them with
  `process(poll)`. A detached (`nohup`/background) batch dies silently
  when the parent exec exits, and `setsid` does not exist on macOS.
- **Keep the resume state file in the skill directory**, not `/tmp`:
  `/tmp` is cleared on reboot and silently loses the done-markers,
  which makes a re-run re-deliver books Amre already has.
- **A fallback must never silently substitute a different book.** Confirm
  the EPUB's `dc:title` matches the title that was requested before
  sending it.
- **The AgentMail sent record is the receipt.** A script that printed
  "sent" is not proof. Read the sent record and check the attachment's
  filename, content type and byte count:

  ```bash
  ~/.openclaw/tools/node-v24.21.0/bin/openclaw agentmail inboxes:messages list \
    --inbox-id thedross@agentmail.to --subject "<title>" --format json
  ```

  Use the **gateway's own binary**, not `openclaw` from `PATH`. The
  `agentmail` command is provided by a plugin that only exists in the
  gateway build (2026.9.6). The `openclaw` first on `PATH`
  (`/opt/homebrew/bin/openclaw`, 2026.6.35) is stale: it rejects the
  live config as invalid *and* has no `agentmail` command at all, so it
  fails with `Unknown command: openclaw agentmail`. The Python SDK
  path in the `agentmail-email` skill avoids this entirely.

  The JSON output carries an `attachments` array with `filename`,
  `content_type` and `size` — read those three, not just the subject
  line, to confirm what actually went out.

  A sent record carrying the right `content_type` proves the attachment
  went out labelled correctly. The absence of a bounce then proves Amazon
  accepted it — and absence of a bounce, not presence in a Sent folder,
  is the delivery signal.

## Notes on the site

- **The eAPI on `z-lib.by` is the working route.** The public HTML pages
  now render a "Lifetime Premium" upsell instead of a download button,
  and their `/papi/` endpoints 404. The eAPI is a JSON API:
  `POST /eapi/user/login` (email + password) → `POST /eapi/book/search`
  (`message`, `page`, `limit`, optional `extensions[]`) →
  `GET /eapi/book/<id>/<hash>/file`, which returns a signed CDN link.
- eAPI titles arrive as `"Author - Title"`. The script splits them back
  into title/author, and the author field often carries a bracketed
  duplicate (`Hill, Joe [Hill, Joe]`).
- **A book's file is addressed by (id, hash), never by id alone.**
- The advertised extension and the served bytes can disagree — an "AZW3"
  row has been seen serving MOBI. Always let `retarget_ext()` have the
  last word on the filename.
- The `ego-browser` skill exists but the binary is not installed, so
  browser-driven login is not available. It is not needed: the eAPI
  signs in with the stored credentials directly.
