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

**Kindle prefers AZW3/MOBI.** When the destination is a `@kindle.com`
address, `deliver` looks for the same title in a Kindle-native format and
switches to it automatically. Override with `--format azw3|mobi|epub`.

**Trust the bytes, not the label.** Z-Library's advertised extension is
often wrong — an "AZW3" row can serve MOBI bytes, and a MOBI downloaded
as `.txt` is exactly what Amazon refuses to convert. `sniff_ext()` reads
magic bytes and `retarget_ext()` renames the file to match, so check the
printed filename after every download. MOBI/AZW3 are PalmDB containers:
the `BOOKMOBI`/`TPZ3` marker sits at **byte 60**, not byte 0.

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

## Books that are public domain

These have known Gutenberg ids and work without any Z-Library account:

- The King in Yellow (8492), Carmilla (10007), The Call of Cthulhu (68283)
- At the Mountains of Madness (70652), The Great God Pan (389)
- The House of Souls (25016), The Turn of the Screw (209)
- The Yellow Wallpaper (1952), The Picture of Dorian Gray (174)
- Dracula (345), The Time Machine (35), Frankenstein (84)

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
