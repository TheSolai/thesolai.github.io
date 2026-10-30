#!/usr/bin/env python3
"""Count the AgentMail sends made in the current UTC day.

The AgentMail API has no quota endpoint, so the only reliable source of
truth for "how many sends have I made today" is the sent-message log of
the sending inbox. This walks every page of that inbox, keeps the
messages labelled `sent`, and counts the ones whose UTC timestamp falls
on the given day.

The daily cap is a hard ceiling enforced by the mail service, so a
delivery run has to know its remaining budget *before* it starts, not
after it has been rejected mid-batch.

Usage:
    python3 send_cap.py                 # count today's sends, print JSON
    python3 send_cap.py --day 2026-10-30
    python3 send_cap.py --budget 5      # exit 0 if >=5 sends remain

Exit codes:
    0: budget available (or no budget requested)
    3: budget exhausted
    1: the counter itself failed
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipient_config  # noqa: E402

INBOX = "thedross@agentmail.to"
API = "https://api.agentmail.to"
SECRETS = os.path.expanduser("~/.openclaw/workspace/secrets")
CAP = 100


def default_recipients():
    """The two delivery recipients, read from runtime configuration.

    They are not built into this file: see recipient_config.py for why.
    """
    try:
        return recipient_config.load()
    except recipient_config.ConfigError as exc:
        print("send_cap: %s" % exc, file=sys.stderr)
        raise SystemExit(2)


def agentmail_key() -> str:
    for name in ("agentmail-api-key.txt", "sol-agentmail-api-key.txt",
                 "the-dross-agentmail-api-key.txt"):
        path = os.path.join(SECRETS, name)
        if os.path.isfile(path):
            key = open(path, encoding="utf-8").read().strip()
            if key:
                return key
    raise SystemExit("no AgentMail API key found in secrets/")


def fetch_all(inbox: str = INBOX) -> list:
    """Every message in the inbox, following pagination to the end."""
    key = agentmail_key()
    msgs: list = []
    token = None
    while True:
        path = f"/v0/inboxes/{inbox}/messages?limit=100"
        if token:
            path += "&page_token=" + urllib.parse.quote(token)
        req = urllib.request.Request(
            API + path, headers={"Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        batch = data.get("messages", []) if isinstance(data, dict) else data
        msgs.extend(batch)
        token = data.get("next_page_token") if isinstance(data, dict) else None
        if not token or not batch:
            return msgs


def sent_messages(inbox: str = INBOX) -> list:
    return [m for m in fetch_all(inbox) if "sent" in (m.get("labels") or [])]


def day_of(msg: dict) -> str:
    ts = msg.get("timestamp") or msg.get("created_at") or ""
    return str(ts)[:10]


def count_day(sent: list, day: str) -> tuple:
    """Return (total, {recipient: count}) for sends made on `day`."""
    per: dict = {}
    total = 0
    for m in sent:
        if day_of(m) != day:
            continue
        total += 1
        to = m.get("to") or []
        if isinstance(to, str):
            to = [to]
        for addr in to:
            per[addr] = per.get(addr, 0) + 1
    return total, per


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None,
                    help="UTC day to count, YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--budget", type=int, default=0,
                    help="exit 3 if fewer than this many sends remain")
    ap.add_argument("--out", default=None, help="write the JSON report here")
    args = ap.parse_args()

    day = args.day or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    try:
        sent = sent_messages()
    except Exception as exc:
        print(f"send_cap: failed to read the sent log: {exc}", file=sys.stderr)
        return 1

    total, per = count_day(sent, day)
    known = {a: per.get(a, 0) for a in default_recipients()}
    report = {
        "day": day,
        "total_sent_today": total,
        "cap": CAP,
        "remaining": max(0, CAP - total),
        "by_recipient": known,
        "other_recipients": {k: v for k, v in per.items() if k not in known},
        "total_sent_all_time": len(sent),
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")

    if args.budget and report["remaining"] < args.budget:
        print(f"send_cap: only {report['remaining']} send(s) remain on {day}, "
              f"need {args.budget}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
