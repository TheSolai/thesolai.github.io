#!/usr/bin/env python3
"""Send an ebook to a delivery recipient over raw SMTP.

Why this exists: the AgentMail API enforces a hard daily send ceiling
(100/day for the organisation plan). When that ceiling is reached the API
answers HTTP 429 and nothing is delivered. The SMTP route has no such
per-day ceiling, so it is the fallback that keeps a backlog moving.

It reuses zlib_kindle's delivery guards unchanged -- preflight_book(),
epub_namespace_ok(), epub_metadata() and the KINDLE_CONTENT_TYPES map --
so a file that AgentMail would refuse is refused here too. The guards are
the thing that matters: Amazon accepts a bad file silently, so a
mislabelled or malformed attachment produces a book that simply never
appears on the device.

Credentials come from the local himalaya config (~/.config/himalaya/config.toml).
The password is never printed and never logged.

Usage:
    python3 smtp_send.py <file> --title "..." --to <address>
    python3 smtp_send.py <file> --title "..." --to <addr> --expect-title "..." --expect-author "..."
"""

import argparse
import json
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zlib_kindle as zk  # noqa: E402
import recipient_config  # noqa: E402

HIMALAYA_CONFIG = os.path.expanduser("~/.config/himalaya/config.toml")
ACCOUNTS = ("gmail", "icloud")
STATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "state",
    "backlog-state.json",
)


def read_account(path, account):
    """Pull smtp username/password/host/port out of an account block."""
    text = open(path, encoding="utf-8").read()
    blocks = text.split("[[accounts]]")
    block = next((b for b in blocks if re.search(rf'name\s*=\s*"{account}"', b)), "")
    if not block:
        raise KeyError(account)

    scope = block.split(f"[accounts.{account}.smtp]", 1)[-1].split(f"[accounts.{account}", 1)[0]

    def field(name, default=None):
        m = re.search(rf'^\s*{name}\s*=\s*"?([^"\n]+)"?', scope, re.M)
        return m.group(1).strip() if m else default

    username = field("username")
    password = field("password")
    if not username or not password:
        raise KeyError(account)

    port = int(field("port", "587"))
    host = field("host") or ("smtp.gmail.com" if account == "gmail" else "smtp.mail.me.com")
    return username, password, host, port


def smtp_connect(username, password, host, port):
    ctx = ssl.create_default_context()
    smtp = smtplib.SMTP(host, port, timeout=60)
    try:
        smtp.ehlo("annmarie.local")
        if smtp.has_extn("starttls"):
            smtp.starttls(context=ctx)
            smtp.ehlo("annmarie.local")
        smtp.login(username, password)
    except Exception:
        try:
            smtp.quit()
        except Exception:
            pass
        raise
    return smtp


def guards_ok(path, expect_title=None, expect_author=None):
    """Run the full delivery guard suite. Returns (ok, reason)."""
    ok, detail = zk.preflight_book(path, expect_title, expect_author)
    if not ok:
        return False, detail
    if not zk.epub_namespace_ok(path):
        return False, "OPF namespace is not the default form"
    if not os.path.getsize(path):
        return False, "file is empty"
    return True, detail


def content_type_for(path):
    """The content type Amazon receives, derived from the proven format."""
    ok, detail = zk.preflight_book(path)
    if not ok:
        return None, detail
    ext = zk.FORMAT_EXT.get(detail)
    return zk.KINDLE_CONTENT_TYPES.get(ext), detail


def send(path, title, to_addr):
    """Send one file to one address. Returns (ok, message).

    Delivery is locked by default. Unless state/DELIVERY_ARMED exists,
    nothing is sent and the reason is returned. See delivery_lock.py.
    """
    import delivery_lock

    armed, why = delivery_lock.check()
    if not armed:
        return False, why

    ctype, detail = content_type_for(path)
    if not ctype:
        return False, f"no content type for {detail}"

    with open(path, "rb") as fh:
        raw = fh.read()
    if not raw:
        return False, "file is empty"

    maintype, subtype = ctype.split("/", 1)
    last_error = None

    for account in ACCOUNTS:
        try:
            username, password, host, port = read_account(HIMALAYA_CONFIG, account)
        except (KeyError, FileNotFoundError) as exc:
            last_error = f"{account}: config unavailable ({exc})"
            continue

        msg = EmailMessage()
        msg["From"] = f"Annemarie <{username}>"
        msg["To"] = to_addr
        msg["Subject"] = title
        msg.set_content(f"{title}\n\nSent from the Dross library desk. Enjoy it.\n")
        msg.add_attachment(raw, maintype=maintype, subtype=subtype,
                           filename=os.path.basename(path))

        try:
            smtp = smtp_connect(username, password, host, port)
            try:
                smtp.send_message(msg)
            finally:
                try:
                    smtp.quit()
                except Exception:
                    pass
        except Exception as exc:
            last_error = f"{account}: {type(exc).__name__}: {exc}"
            print(f"  · {account} failed -> {last_error}", file=sys.stderr)
            continue

        return True, (f"SENT to {to_addr} | via {account} | subject={title!r} | "
                      f"attachment={os.path.basename(path)} "
                      f"({len(raw):,} bytes, {ctype})")

    return False, f"all accounts failed; last error -> {last_error}"


def mark_state(key, addr, state_path=STATE):
    """Record the delivery so the AgentMail pipeline does not re-send it."""
    state = {"done": {}}
    if os.path.isfile(state_path):
        try:
            with open(state_path, encoding="utf-8") as fh:
                state = json.load(fh)
        except (OSError, ValueError):
            state = {"done": {}}
    state.setdefault("done", {})
    raw = state["done"].get(key) or ""
    have = {a.strip() for a in str(raw).split(",") if a.strip()}
    have.add(addr)
    state["done"][key] = ",".join(sorted(have))
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, state_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--title", required=True)
    ap.add_argument("--to", required=True)
    ap.add_argument("--expect-title")
    ap.add_argument("--expect-author")
    ap.add_argument("--state-key", help="state key to mark (defaults to gap:<file>)")
    ap.add_argument("--no-state", action="store_true",
                    help="do not touch the delivery state file")
    args = ap.parse_args()

    path = os.path.abspath(args.file)
    if not os.path.isfile(path):
        raise SystemExit(f"no such file: {path}")

    ok, reason = guards_ok(path, args.expect_title, args.expect_author)
    if not ok:
        print(f"  ! refusing to send {os.path.basename(path)}: {reason}", file=sys.stderr)
        return 1

    ok, message = send(path, args.title, args.to)
    print(message, flush=True)
    if not ok:
        return 1

    if not args.no_state:
        key = args.state_key or ("gap:" + os.path.basename(path))
        mark_state(key, args.to)
        print(f"  · state marked: {key} -> {args.to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
