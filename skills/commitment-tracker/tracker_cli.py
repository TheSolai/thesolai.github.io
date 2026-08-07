#!/usr/bin/env python3
"""
Dross's Commitment Tracker — CLI
Detects, stores, and reminds on promises made in agent replies.
"""

import argparse
import csv
import datetime
import json
import os
import re
import sqlite3
import sys
import textwrap
from pathlib import Path

DEFAULT_DB = os.environ.get(
    "PROGRESS_COMMIT_DB",
    Path.home() / ".openclaw" / "progress_commits.db",
)

# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS commitments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id      TEXT    NOT NULL,
    session_id   TEXT    NOT NULL,
    agent_id     TEXT    NOT NULL,
    text         TEXT    NOT NULL,
    phrase       TEXT,
    eta_minutes  INTEGER,
    message      TEXT,
    created_at   TEXT    NOT NULL,
    last_activity TEXT,
    completed_at  TEXT,
    missed       INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_task_id   ON commitments(task_id);
CREATE INDEX IF NOT EXISTS idx_completed ON commitments(completed_at);
"""

# ── Detection patterns ────────────────────────────────────────────────────────

CH_PATTERNS = [
    # "等会给你更新" — wait N minutes then give you X
    (r"等[会儿会]?\s*\S{0,20}?\S{0,10}?\s*给?你\s*(\S{1,30})",          "给你",   None),
    (r"稍[后候]\s*\S{0,20}?\S{0,10}?\s*给?你\s*(\S{1,30})",            "给你",   None),
    (r"等\s*下\s*给?你\s*(\S{1,30})",                                  "给你",   None),
    # "N分钟后" / "N分钟后给你"
    (r"(\d+)\s*分\S?\s*钟?\s*后?\s*(?:给?你|再|然后|再给你|给你)?\s*(\S{0,30})", None, None),
    # "回头给你" / "等会再说"
    (r"(?:等[会儿会]|稍[后候]|回头|待[会儿])[:：]?\s*给?你\s*(\S{1,30})",  "给你",   None),
    # "先跑N分钟" — running a script for N minutes
    (r"先跑\s*(\d+)\s*分\S?\s*钟?\s*的?\s*(\S{1,20})",                None,   None),
    (r"先跑\s*(\d+)\s*分\S?\s*钟",                                      None,   None),
    # "先做X，完给你" / "先XX，完了给你"
    (r"先\s*\S{1,20}\s*[，,]\s*(?:完|完成|结束|好了)\s*给?你\s*(\S{1,30})", "给你", None),
    # "给你更新" / "给你结果" standalone
    (r"给?你\s*(?:更新|进展|结果|报告|回复|消息|答案)\s*",             None,    None),
]

EN_PATTERNS = [
    (r"(?:give you|send you|get back to you|tell you|p给你)\s+(\S{1,30}?)\s+(?:in|within|after)\s+(\d+)\s*(?:minutes?|mins?|mins?\.?)\.?", "update", None),
    (r"(?:give you|send you)\s+an?\s*update\s+(?:in|within|after)\s+(\d+)\s*(?:minutes?|mins?)\.?", "update", None),
    (r"(?:ping|hit|msg|email)\s+you\s+(?:back\s+)?(?:in|after)\s+(\d+)\s*(?:minutes?|mins?)\.?", "ping", None),
    (r"(?:check|follow[- ]?up)\s+(?:back\s+)?(?:in|after)\s+(\d+)\s*(?:minutes?|mins?)\.?", "follow up", None),
    (r"(?:running|exec(?:ute)?|working)\s+(?:on\s+)?(?:it\s+)?(?:for|about)\s+(\d+)\s*(?:minutes?|mins?)\.?", "running", None),
    (r"(?:just|be)\s+(?:right|rightly)\s*back", "brb", None),
]

ALL_PATTERNS = [(p, "zh", g, h) for p, g, h in CH_PATTERNS] + \
               [(p, "en", g, h) for p, g, h in EN_PATTERNS]

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db(path: str = DEFAULT_DB) -> sqlite3.Connection:
    os.makedirs(Path(path).parent, exist_ok=True)
    conn = sqlite3.connect(path)
    # Split on semicolons, strip, skip empty lines
    for stmt in SCHEMA.split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()
    return conn

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def parse_minutes(text: str) -> int | None:
    """Try to pull a number of minutes out of matched groups."""
    for g in text.split():
        g = re.sub(r"[^\d]", "", g)
        if g.isdigit() and 1 <= int(g) <= 10000:
            return int(g)
    return None

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_record(args) -> None:
    """Detect a commitment in free-form text and store it."""
    conn = get_db(args.db)
    text = args.text or ""
    detected = False
    phrase   = None
    minutes  = None

    for pattern, lang, group_key, hard_code in ALL_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            detected = True
            phrase   = (group_key if group_key else
                        (m.group(1).strip() if m.lastindex and m.lastindex >= 1 else None))
            minutes  = parse_minutes(m.group(0)) or hard_code
            break

    cur = conn.execute(
        """
        INSERT INTO commitments
            (task_id, session_id, agent_id, text, phrase, eta_minutes, message, created_at, last_activity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (args.task_id, args.session_id, args.agent_id, text,
         phrase, minutes, args.message, now_iso(), now_iso()),
    )
    conn.commit()
    row_tuple = conn.execute("SELECT * FROM commitments WHERE id = ?", (cur.lastrowid,)).fetchone()
    cols = [d[0] for d in conn.execute("SELECT * FROM commitments LIMIT 0").description]
    row = dict(zip(cols, row_tuple))
    row["detected"] = detected

    if args.json:
        print(json.dumps(row, ensure_ascii=False, indent=2))
    else:
        status = "✓ commitment detected" if detected else "— no clear commitment found"
        pid    = f"[{phrase}]" if phrase else ""
        mins   = f" (~{minutes}min)" if minutes else ""
        print(f"  {status}  task={args.task_id}  {pid}{mins}")
        if not detected:
            print("  (store with --no-detect to force-save anyway)")


def cmd_activity(args) -> None:
    """Ping to show a commitment is still alive."""
    conn = get_db(args.db)
    now  = now_iso()
    n = conn.execute(
        "UPDATE commitments SET last_activity = ? WHERE task_id = ? AND completed_at IS NULL",
        (now, args.task_id),
    ).rowcount
    conn.commit()
    if args.json:
        print(json.dumps({"task_id": args.task_id, "activity_updated": n > 0, "rows": n}))
    else:
        print(f"  {'✓' if n else '—'} activity ping  task={args.task_id}  rows={n}")


def cmd_complete(args) -> None:
    """Mark a commitment fulfilled."""
    conn = get_db(args.db)
    now  = now_iso()
    n = conn.execute(
        "UPDATE commitments SET completed_at = ?, missed = 0 WHERE task_id = ? AND completed_at IS NULL",
        (now, args.task_id),
    ).rowcount
    conn.commit()
    if args.json:
        print(json.dumps({"task_id": args.task_id, "completed": n > 0, "rows": n}))
    else:
        print(f"  {'✓' if n else '—'} completed  task={args.task_id}  rows={n}")


def cmd_watchdog(args) -> None:
    """Scan for overdue commitments and fire notifications."""
    conn  = get_db(args.db)
    grace = args.activity_grace
    gsec  = args.grace_seconds

    rows = conn.execute(
        "SELECT * FROM commitments WHERE completed_at IS NULL AND missed = 0",
    ).fetchall()

    cols = [d[0] for d in conn.execute(
        "SELECT * FROM commitments LIMIT 0"
    ).description]
    now_dt = datetime.datetime.now(datetime.timezone.utc)

    overdue = []
    for row in rows:
        r    = dict(zip(cols, row))
        cdt  = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        ldt  = (datetime.datetime.fromisoformat(r["last_activity"].replace("Z", "+00:00"))
                if r["last_activity"] else cdt)
        diff = (now_dt - cdt).total_seconds()
        lag  = (now_dt - ldt).total_seconds()

        is_overdue = (r["eta_minutes"] and diff > r["eta_minutes"] * 60 + gsec)
        is_stale   = (grace and lag > grace)

        if args.verbose:
            print(
                f"  [{r['task_id']}] "
                f"eta={r['eta_minutes']}min "
                f"age={int(diff)}s "
                f"idle={int(lag)}s "
                f"overdue={is_overdue} "
                f"stale={is_stale}"
                f"  {r['phrase'] or r['text'][:40]!r}"
            )

        if is_overdue or is_stale:
            overdue.append((r, is_overdue, is_stale))

    if not overdue and not args.verbose:
        return  # silent OK

    for r, is_overdue, is_stale in overdue:
        phrase   = r["phrase"] or "承诺"
        task_tag = r["task_id"]
        msg = (f"⏰ 任务 {task_tag} 的承诺（{phrase}）已过期，请检查进度。"
               if is_overdue else
               f"💤 任务 {task_tag} 的承诺（{phrase}）似乎卡住了，最后活动 {int((now_dt - datetime.datetime.fromisoformat(r['last_activity'].replace('Z','+00:00'))).total_seconds())}s 前。")

        if args.mark_missed and is_overdue:
            conn.execute(
                "UPDATE commitments SET missed = 1 WHERE id = ?",
                (r["id"],),
            )
            conn.commit()

        notify = args.notify_command or ""
        if notify:
            cmd = notify.replace("{message}", msg).replace("{task_id}", task_tag).replace("{phrase}", phrase)
            os.system(cmd)  # nosec — caller controls the template

        if not args.quiet:
            print(msg)

    if args.json:
        print(json.dumps({"overdue": len(overdue), "tasks": [r["task_id"] for r, _, _ in overdue]}))


def cmd_list(args) -> None:
    """Show all commitments, optionally filtered."""
    conn = get_db(args.db)
    sql  = "SELECT * FROM commitments WHERE 1=1"
    params = []
    if args.active:
        sql += " AND completed_at IS NULL"
    if args.overdue:
        sql += " AND missed = 1"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(args.limit)

    rows = conn.execute(sql, params).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM commitments LIMIT 0").description]

    if args.json:
        print(json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, indent=2))
        return

    if not rows:
        print("  — no commitments found")
        return

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    print(f"  {'ID':>4}  {'TASK':20}  {'STATUS':8}  {'ETA':5}  {'PHRASE':15}  MESSAGE")
    print(f"  {'-'*4}  {'-'*20}  {'-'*8}  {'-'*5}  {'-'*15}  {'-'*30}")
    for row in rows:
        r    = dict(zip(cols, row))
        cdt  = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        age  = int((now_dt - cdt).total_seconds() / 60)
        if r["completed_at"]:
            status = "✓ done"
        elif r["missed"]:
            status = "✗ missed"
        else:
            status = f"○ {age}m ago"
        print(
            f"  {r['id']:>4}  "
            f"{r['task_id']:20}  "
            f"{status:8}  "
            f"{(str(r['eta_minutes']) + 'm') if r['eta_minutes'] else '—':5}  "
            f"{(r['phrase'] or '—'):15}  "
            f"{(r['message'] or r['text'])[:50]}"
        )


def cmd_brief(args) -> None:
    """Print a one-line summary for cron logs."""
    conn = get_db(args.db)
    now_dt = datetime.datetime.now(datetime.timezone.utc)

    active = conn.execute(
        "SELECT COUNT(*) FROM commitments WHERE completed_at IS NULL AND missed = 0"
    ).fetchone()[0]

    missed = conn.execute(
        "SELECT COUNT(*) FROM commitments WHERE missed = 1"
    ).fetchone()[0]

    overdue_rows = conn.execute(
        "SELECT * FROM commitments WHERE completed_at IS NULL AND missed = 0"
    ).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM commitments LIMIT 0").description]

    overdue_list = []
    gsec = getattr(args, "grace_seconds", 0) or 0
    for row in overdue_rows:
        r    = dict(zip(cols, row))
        cdt  = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        diff = (now_dt - cdt).total_seconds()
        if r["eta_minutes"] and diff > r["eta_minutes"] * 60 + gsec:
            overdue_list.append(r["task_id"])

    print(
        f"[commitment-tracker] "
        f"active={active}  missed={missed}  overdue={len(overdue_list)}  "
        + (f"overdue_tasks={overdue_list}" if overdue_list else "")
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dross's Commitment Tracker CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite path (default: {DEFAULT_DB})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # record
    p = sub.add_parser("record", help="Detect and store a commitment from free-form text")
    p.add_argument("--task-id",   required=True, help="Task identifier, e.g. task:astro-42")
    p.add_argument("--session-id", required=True, help="Session identifier")
    p.add_argument("--agent-id",  required=True, help="Agent identifier")
    p.add_argument("--text",      help="Free-form text to scan for commitments")
    p.add_argument("--message",   help="Short human-readable summary")
    p.add_argument("--json",      action="store_true", help="JSON output")
    p.set_defaults(func=cmd_record)

    # activity
    p = sub.add_parser("activity", help="Ping that a commitment is still alive")
    p.add_argument("--task-id",  required=True)
    p.add_argument("--json",     action="store_true")
    p.set_defaults(func=cmd_activity)

    # complete
    p = sub.add_parser("complete", help="Mark a commitment fulfilled")
    p.add_argument("--task-id",  required=True)
    p.add_argument("--json",     action="store_true")
    p.set_defaults(func=cmd_complete)

    # watchdog
    p = sub.add_parser("watchdog", help="Check for overdue commitments and fire notifications")
    p.add_argument("--notify-command",  help="Shell command template with {message}, {task_id}, {phrase}")
    p.add_argument("--activity-grace", type=int, default=120,   help="Seconds of inactivity before marking stale (default 120)")
    p.add_argument("--grace-seconds",  type=int, default=30,    help="Grace period beyond eta before overdue (default 30)")
    p.add_argument("--mark-missed",    action="store_true",   help="Flip overdue rows to missed=1")
    p.add_argument("--verbose",        action="store_true",   help="Show all tracked commitments")
    p.add_argument("--json",           action="store_true",   help="JSON summary")
    p.add_argument("--quiet",          action="store_true",   help="Suppress notification prints")
    p.set_defaults(func=cmd_watchdog)

    # list
    p = sub.add_parser("list", help="List all commitments")
    p.add_argument("--active",  action="store_true", help="Show only incomplete")
    p.add_argument("--overdue", action="store_true", help="Show only missed")
    p.add_argument("--limit",   type=int, default=50)
    p.add_argument("--json",    action="store_true")
    p.set_defaults(func=cmd_list)

    # brief (for cron)
    p = sub.add_parser("brief", help="One-line summary for cron log rotation")
    p.add_argument("--grace-seconds", type=int, default=30)
    p.set_defaults(func=cmd_brief)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
