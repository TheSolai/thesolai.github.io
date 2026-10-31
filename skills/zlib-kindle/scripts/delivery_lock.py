#!/usr/bin/env python3
"""Delivery kill switch for the Z-Library book pipeline.

Why this exists: on 2026-10-31 a batch of ten books was delivered to
Amre's Kindle and Gmail after she had already said "send nothing". The
cause was not a runaway scheduler -- it was a code path that had no
standing gate, so any script could send at any time.

This module is the gate. Every transport in this skill (AgentMail via
zlib_kindle.send_to_kindle, and raw SMTP via smtp_send.send) asks it
first. When the lock is engaged, both refuse to send and say why.

The lock is OFF by default: no arming file means no sending at all.
To deliver books deliberately, create the arming file, run the delivery,
and remove it again:

    echo "Amre explicitly asked for books" > state/DELIVERY_ARMED
    python3 batch_deliver.py --list ../lists/queue-backlog.json ...
    rm -f state/DELIVERY_ARMED

A file is used rather than an environment variable on purpose: an env
var is inherited by every child process and can be set by a cron entry
or a launchd plist by accident. A file has to be created on purpose, in
one place, and deleted again afterwards.

Re-arm only on Amre's explicit instruction. Never leave it in place.
"""

import os

LOCK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "state",
    "DELIVERY_ARMED",
)

REASON = (
    "delivery is locked: the book pipeline may not send without an "
    "explicit standing instruction from Amre"
)


def is_armed() -> bool:
    """True only when the arming file exists."""
    return os.path.exists(LOCK_FILE)


def check() -> tuple[bool, str]:
    """Return (armed, reason).

    When armed is False the reason explains why nothing was sent.
    """
    if is_armed():
        return True, "delivery armed"
    return False, REASON


def require() -> None:
    """Raise RuntimeError unless delivery is armed."""
    armed, reason = check()
    if not armed:
        raise RuntimeError(reason)
