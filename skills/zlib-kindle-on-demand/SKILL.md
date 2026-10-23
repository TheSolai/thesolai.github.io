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
python3 zlib_kindle.py fetch <book-id-or-url>
python3 zlib_kindle.py send ~/Downloads/dross-books/<file>.epub --title "<Title> by <Author>"
```

## What it does

1. Searches Z-Library for the title.
2. Picks the requested result (default: the first).
3. Downloads it to `~/Downloads/dross-books/`.
4. Emails it to `amrekin@kindle.com` as an attachment, via the AgentMail
   inbox `thedross@agentmail.to`.

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

## Rules

- Never print the Z-Library password or the AgentMail API key.
- Use `/opt/homebrew/bin/python3` (Homebrew); system python lacks the
  `agentmail` module.
- Do not email a file that failed to download. The script verifies EPUB
  zip magic bytes before saving.
- Report which step failed if anything breaks — do not claim a delivery
  that did not happen.
