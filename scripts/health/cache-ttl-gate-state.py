#!/usr/bin/env python3
"""
cache-ttl-gate-state.py — is the cache-TTL gate EFFECTIVE in the RUNNING
gateway process?

WHY THIS EXISTS
  The launchd restart agent (ai.sol.gateway-restart-if-idle) was written to
  restart the gateway "when the lane is idle". That was wrong: idle is the
  NORMAL state. On 2026-11-04 and 2026-11-05 it restarted the gateway 255
  times, roughly every nine minutes, for two days — churning the Telegram
  plugin's polling, reloading the runtime for no reason, and keeping the
  restart race (the one that killed messageId 2547) permanently armed.

  A restart must have a REASON. There are exactly two:

    1. A session is WEDGED — the gateway classified the run
       stalled_agent_run with recovery=none. That run can never deliver a
       reply and it blocks the compaction. Restarting is the release.

    2. THE GATE IS NOT EFFECTIVE — a cache-TTL marker was written AFTER the
       running gateway started. The patch is on disk but the running
       process still has the old code, so the markers keep growing. A
       restart is the only way to load it.

  This script answers (2). It compares the newest marker's timestamp against
  the gateway process's own start time.

HOW IT FINDS THE NEWEST MARKER
  Markers live in the agent database as zstd-compressed transcript events.
  The `zstandard` python module is NOT installed on this machine, so the
  zstd CLI is used to decompress. Events are read newest-first and the
  first one containing `openclaw.cache-ttl` wins.

Usage:
  cache-ttl-gate-state.py          # human-readable
  cache-ttl-gate-state.py --json   # machine-readable
  cache-ttl-gate-state.py --pid N  # test another process's start time

Exit codes:
  0  the gate is effective (no marker newer than the gateway start)
  1  the gate is NOT effective — a restart would load it
  2  it could not be determined
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

DB = os.path.expanduser("~/.openclaw/agents/main/agent/openclaw-agent.sqlite")
ZSTD = "/opt/homebrew/bin/zstd"
MARKER = "openclaw.cache-ttl"


def gateway_pid():
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True,
                             text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "ai.openclaw.gateway":
            try:
                return int(parts[0])
            except ValueError:
                return None
    return None


def gateway_start_epoch(pid):
    """Start time of the gateway process, as a unix epoch."""
    if not pid:
        return None
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="],
                             capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not out:
        return None
    # "Tue Nov  3 18:16:13 2026" -> epoch
    try:
        return int(subprocess.run(
            ["date", "-j", "-f", "%a %b %e %H:%M:%S %Y", out, "+%s"],
            capture_output=True, text=True, timeout=20).stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def decompress(blob):
    if not blob:
        return None
    with tempfile.NamedTemporaryFile(delete=False) as fh:
        fh.write(blob)
        src = fh.name
    dst = src + ".out"
    try:
        res = subprocess.run([ZSTD, "-d", "-f", "-q", src, "-o", dst],
                             capture_output=True, timeout=60)
        if res.returncode != 0:
            return None
        with open(dst, "r", errors="replace") as fh:
            return fh.read()
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        for p in (src, dst):
            try:
                os.unlink(p)
            except OSError:
                pass


def newest_marker():
    """(created_at_ms, session_id, seq) of the newest marker, or None."""
    if not os.path.exists(DB):
        return None
    con = sqlite3.connect(DB)
    try:
        rows = con.execute(
            "SELECT session_id, seq, created_at, event_zstd FROM transcript_events "
            "WHERE event_zstd IS NOT NULL ORDER BY created_at DESC LIMIT 400"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    for sid, seq, created_at, blob in rows:
        text = decompress(blob)
        if text and MARKER in text:
            return (created_at, sid, seq)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pid", type=int, default=None,
                    help="use this pid's start time instead of the gateway's")
    args = ap.parse_args()

    pid = gateway_pid() if args.pid is None else args.pid
    start = gateway_start_epoch(pid)
    marker = newest_marker()

    result = {
        "gateway_pid": pid,
        "gateway_start_epoch": start,
        "newest_marker": None,
        "state": "unknown",
        "detail": "",
    }

    if start is None:
        result["detail"] = "could not determine the gateway start time"
    elif marker is None:
        # No marker anywhere: nothing is writing them, so the gate is
        # either effective or irrelevant. Effective.
        result["state"] = "effective"
        result["detail"] = "no cache-TTL marker found in the last 400 events"
    else:
        created_at, sid, seq = marker
        result["newest_marker"] = {
            "created_at_ms": created_at,
            "created_at_epoch": created_at / 1000,
            "session_id": sid,
            "seq": seq,
        }
        age = created_at / 1000 - start
        result["marker_age_seconds"] = round(age, 1)
        if age > 0:
            result["state"] = "pending"
            result["detail"] = (f"a marker was written {age:.0f}s AFTER the "
                                f"gateway started (pid {pid}) — the running "
                                f"process does not have the gate")
        else:
            result["state"] = "effective"
            result["detail"] = (f"the newest marker predates the gateway start "
                                f"by {-age:.0f}s — the gate is effective")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"state:   {result['state']}")
        print(f"detail:  {result['detail']}")
        if result["newest_marker"]:
            print(f"marker:  seq={result['newest_marker']['seq']} "
                  f"session={result['newest_marker']['session_id'][:8]}")
        print(f"gateway: pid={pid} start={start}")

    return {"effective": 0, "pending": 1}.get(result["state"], 2)


if __name__ == "__main__":
    sys.exit(main())
