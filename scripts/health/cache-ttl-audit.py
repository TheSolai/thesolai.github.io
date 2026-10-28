#!/usr/bin/env python3
"""Audit OpenClaw session transcripts for `openclaw.cache-ttl` marker bloat.

The marker itself is harmless, but each one re-lists EVERY frozen tool result
for the attempt, so N attempts produce O(N^2) bytes. On 2026-10-28 a single
cron session carried 30 markers / 961 KB — 72% of the window — purely as
bookkeeping, and the session overflowed its context budget because of it.

This script counts markers per session, including the COMPRESSED rows (whose
`event_json` is empty and whose payload lives in the `event_zstd` blob), so a
naive SQL LIKE over `event_json` silently reports zero.

Usage:
    cache-ttl-audit.py [--minutes N] [--session-key SUBSTR] [--json]

Exit code 0 = clean, 1 = markers found.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

DEFAULT_DB = os.path.expanduser("~/.openclaw/agents/main/agent/openclaw-agent.sqlite")
ZSTD = "/opt/homebrew/bin/zstd"
MARKER = "openclaw.cache-ttl"


def decompress(blob: bytes) -> str | None:
    with tempfile.NamedTemporaryFile(suffix=".zst", delete=False) as fh:
        fh.write(blob)
        path = fh.name
    out = path + ".json"
    try:
        subprocess.run([ZSTD, "-d", "-f", "-q", path, "-o", out], capture_output=True)
        with open(out, "rb") as fh:
            return fh.read().decode("utf-8", "replace")
    except Exception:
        return None
    finally:
        for candidate in (path, out):
            try:
                os.unlink(candidate)
            except OSError:
                pass


def audit(db_path: str, minutes: int, session_filter: str | None) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cutoff = int((time.time() - minutes * 60) * 1000)
    rows = conn.execute(
        """
        SELECT t.session_id, t.event_utf8_bytes, t.event_json, t.event_zstd,
               COALESCE(w.session_key, '')
        FROM transcript_events t
        LEFT JOIN session_windows w ON w.session_id = t.session_id
        WHERE t.created_at >= ?
        ORDER BY t.created_at
        """,
        (cutoff,),
    ).fetchall()

    sessions: dict[str, dict] = {}
    for session_id, size, event_json, event_zstd, session_key in rows:
        if session_filter and session_filter not in session_key:
            continue
        text = event_json
        if not text and event_zstd:
            text = decompress(event_zstd)
        if not text or MARKER not in text:
            continue
        bucket = sessions.setdefault(
            session_key or session_id,
            {
                "session_id": session_id,
                "session_key": session_key,
                "markers": 0,
                "marker_bytes": 0,
                "session_bytes": 0,
            },
        )
        bucket["markers"] += 1
        bucket["marker_bytes"] += size or 0

    for session_id, session_key in conn.execute(
        "SELECT DISTINCT ae.session_id, COALESCE(w.session_key, '') "
        "FROM session_transcript_active_events ae "
        "LEFT JOIN session_windows w ON w.session_id = ae.session_id"
    ):
        for bucket in sessions.values():
            if bucket["session_id"] == session_id:
                bucket["session_bytes"] = (
                    conn.execute(
                        "SELECT COALESCE(SUM(COALESCE(t.event_utf8_bytes,0)),0) "
                        "FROM session_transcript_active_events ae "
                        "JOIN transcript_events t ON t.session_id=ae.session_id AND t.seq=ae.event_seq "
                        "WHERE ae.session_id=?",
                        (session_id,),
                    ).fetchone()[0]
                    or 0
                )

    conn.close()
    return {
        "window_minutes": minutes,
        "sessions": sorted(sessions.values(), key=lambda b: b["marker_bytes"], reverse=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--minutes", type=int, default=120)
    parser.add_argument("--session-key", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = audit(args.db, args.minutes, args.session_key)
    if args.json:
        print(json.dumps(report, indent=2))
        return 1 if report["sessions"] else 0

    if not report["sessions"]:
        print(f"PASS  no {MARKER} markers in the last {report['window_minutes']} min")
        return 0

    print(f"WARN  {MARKER} markers found in the last {report['window_minutes']} min")
    for bucket in report["sessions"]:
        share = (bucket["marker_bytes"] / bucket["session_bytes"] * 100) if bucket["session_bytes"] else 0
        print(
            f"  {bucket['session_key'] or bucket['session_id'][:12]}: "
            f"{bucket['markers']} marker(s), {bucket['marker_bytes'] // 1024} KB "
            f"of {bucket['session_bytes'] // 1024} KB ({share:.0f}% of the window)"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
