#!/usr/bin/env python3
"""Deliver the never-sent compilations over SMTP.

Twelve compilations sat in the pipeline's DELIVERIES list with no state
entry, so they were scheduled but never actually sent. Eleven of them are
genuinely new material (0-2% overlap with anything already delivered);
the twelfth, Three Narratives of the Old Gods, was delivered under the
alias The-Watched-Wood-Three-Panics and is skipped here.

Subjects and state keys are read straight from deliver_compilations.py so
the daily pipeline's own lookup (subject.lower()) matches what we record
and it does not re-send these tomorrow.

Usage: python3 send_new_batch.py [--only FILE ...]
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smtp_send  # noqa: E402
import deliver_compilations as dc  # noqa: E402
import recipient_config  # noqa: E402

# Never sent (no state entry) AND not covered by an alias already delivered.
TARGETS = [
    "Dumas-Celebrated-Crimes-Complete.epub",
    "Dumas-dArtagnan-Cycle-Part-One.epub",
    "Dumas-dArtagnan-Cycle-Part-Two.epub",
    "Lytton-The-Works-Part-One.epub",
    "Lytton-The-Works-Part-Two.epub",
    "Tarzan-The-Complete-Series-Volumes-One-to-Six.epub",
    "Tarzan-The-Complete-Series-Volumes-Seven-to-Twelve.epub",
    "Tarzan-The-Complete-Series-Volumes-Thirteen-to-Eighteen.epub",
    "Trollope-Barsetshire-Chronicles-Part-One.epub",
    "Trollope-Barsetshire-Chronicles-Part-Two.epub",
    "Zola-The-Three-Cities.epub",
]


def subject_for(filename):
    """The pipeline's own subject line for a compilation filename."""
    for fn, subj in dc.DELIVERIES:
        if fn == filename:
            return subj
    raise KeyError(filename)


def main():
    args = sys.argv[1:]
    targets = TARGETS
    if args:
        targets = [a for a in args if a.endswith(".epub")]

    # The recipients are read at run time, never stored in this file.
    # A missing or malformed configuration is a hard error: refusing to
    # guess is safer than delivering a library to an address nobody chose.
    try:
        RECIPIENTS = recipient_config.load()
    except recipient_config.ConfigError as exc:
        print(f"  ! refusing to run: {exc}", flush=True)
        return 1

    state = dc.load_state(smtp_send.STATE)
    sent = failed = skipped = 0

    for fn in targets:
        path = os.path.join(dc.COMPILATIONS, fn)
        if not os.path.isfile(path):
            print(f"  ! missing {path}", flush=True)
            failed += 1
            continue

        subj = subject_for(fn)
        key = subj.lower()
        have = dc.recipients_done(state, key)
        want = [a for a in RECIPIENTS if a not in have]
        if not want:
            print(f"  = {subj}: every recipient already has it, skipping", flush=True)
            skipped += 1
            continue

        ok, reason = smtp_send.guards_ok(path)
        if not ok:
            print(f"  ! refusing {fn}: {reason}", flush=True)
            failed += 1
            continue

        for addr in want:
            ok, message = smtp_send.send(path, subj, addr)
            if not ok:
                print(f"  ! FAILED {fn} -> {addr}: {message}", flush=True)
                failed += 1
                break
            smtp_send.mark_state(key, addr)
            state["done"][key] = ",".join(sorted(dc.recipients_done(state, key) | {addr}))
            dc.save_state(smtp_send.STATE, state)
            sent += 1
            print(f"  + delivered: {subj} -> {addr}", flush=True)
            time.sleep(1.5)

    print(f"\nDONE sent={sent} failed={failed} skipped={skipped}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
