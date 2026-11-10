#!/usr/bin/env python3
"""
drossctl — one command that tells the truth about this machine.

WHY THIS EXISTS
---------------
Amre's host runs THREE independent schedulers that nothing reconciles:

  1. OpenClaw crons   (16 jobs, gateway scheduler)
  2. macOS launchd     (26 ai.sol.* agents)
  3. launchd "app" agents (sloth-inbox, while-i-was-away, fridge-list)

Each one has its own failure mode, and until now each one had its own
one-off script to check it: scripts/health/claw-doctor.py (runtime),
scripts/cron-health-check.py (crons only), scripts/site-cron-watchdog.sh
(launchd *loaded* only), scripts/verify-local-services.sh (a hardcoded
list of three ports). Nothing told you the truth about the whole thing at
once, and several checks looked at the wrong question.

The concrete failure that proved it: on 2026-11-09 and 2026-11-10 the
"Daily Workspace Git Backup" cron failed twice in a row because the
publish gate flagged a false-positive credential (the *path* of a token
file, harvested from a launchd plist, matched against a script that
contained that path but no secret). Two days of backup, nobody knew.
scripts/backup_failure.log only records "not found" errors from August.

So drossctl answers four questions in one screen:

  crons    Which scheduled jobs are failing, and since when?
  launchd  Which launchd agents have stopped producing output? (The
           existing watchdog only checks that an agent is *loaded* — an
           agent that runs and fails every night is "loaded" forever.)
  models   Which configured model endpoints are actually alive, and
           which alive endpoints are NOT wired into the gateway config?
  serve    Which local model servers should be running, and aren't?

It is READ-ONLY by default. It never mutates config, never restarts a
service, and never prints a credential. Every verdict names the evidence
it used. It is stdlib-only so it still runs when everything else is broken.

Usage:
    drossctl                # the board (same as `status`)
    drossctl status         # the board
    drossctl crons          # scheduled jobs only
    drossctl launchd        # launchd agents only
    drossctl models         # model endpoints + gateway wiring
    drossctl serve status   # local model servers
    drossctl serve start <name>
    drossctl serve stop <name>
    drossctl json           # everything, machine-readable

Exit codes:
    0  the board ran (findings may still be present — read the report)
    1  drossctl itself could not run
    2  the board ran AND found at least one FAIL
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
OPENCLAW_HOME = os.path.join(HOME, ".openclaw")
WORKSPACE = os.path.join(OPENCLAW_HOME, "workspace")
PLIST_DIR = os.path.join(HOME, "Library", "LaunchAgents")
CONFIG_PATH = os.path.join(OPENCLAW_HOME, "openclaw.json")

CLI_CANDIDATES = [
    os.path.join(OPENCLAW_HOME, "tools", "current-bin", "openclaw"),
    os.path.join(OPENCLAW_HOME, "tools", "node-v24.21.0", "bin", "openclaw"),
]

# Local model servers drossctl knows how to supervise. `port` is what
# drossctl probes; `cmd` is how it starts one.
SERVICES = {
    "splash-qwen36": {
        "port": 8000,
        "model": "mlx-community/Qwen3.6-35B-A3B-4bit",
        "desc": "MLX Qwen3.6-35B-A3B + DFlash2 draft (~186 tok/s measured 2026-11-10)",
        "cmd": [
            "/opt/homebrew/Cellar/splash/1.6.0/bin/splash", "serve",
            "--model", "mlx-community/Qwen3.6-35B-A3B-4bit",
            "--port", "8000", "--max-memory", "90G",
            "--draft-model", os.path.join(HOME, ".cache", "splash-drafts",
                                          "Qwen3.6-35B-A3B-DFlash2"),
        ],
    },
    "splash-qwen38": {
        "port": 8200,
        "model": "mlx-community/Qwen3.8-27B-4bit",
        "desc": "MLX Qwen3.8-27B + DFlash2 draft (~46-58 tok/s measured 2026-11-10)",
        "cmd": [
            "/opt/homebrew/Cellar/splash/1.6.0/bin/splash", "serve",
            "--model", "mlx-community/Qwen3.8-27B-4bit",
            "--port", "8200", "--max-memory", "60G",
            "--draft-model", os.path.join(HOME, ".cache", "splash-drafts",
                                          "Qwen3.8-27B-DFlash2"),
        ],
    },
}

# ── presentation ────────────────────────────────────────────────────────────
C = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "red": "\033[31m", "yellow": "\033[33m", "green": "\033[32m",
    "cyan": "\033[36m", "magenta": "\033[35m",
}
COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(text: str, *styles: str) -> str:
    if not COLOR or not styles:
        return text
    return "".join(C[s] for s in styles) + text + C["reset"]


VERDICT_STYLE = {
    "PASS": ("green", "ok"),
    "WARN": ("yellow", "warn"),
    "FAIL": ("red", "FAIL"),
    "INFO": ("cyan", "info"),
}


def verdict_line(name: str, status: str, detail: str) -> str:
    style, tag = VERDICT_STYLE.get(status, ("dim", status))
    return f"  [{c(tag, style)}] {name:<26} {detail}"


class Board:
    def __init__(self) -> None:
        self.sections: list[dict] = []
        self.fails = 0
        self.warns = 0

    def section(self, title: str) -> None:
        self.sections.append({"title": title, "rows": []})

    def row(self, status: str, name: str, detail: str) -> None:
        if not self.sections:
            self.section("General")
        self.sections[-1]["rows"].append({"status": status, "name": name, "detail": detail})
        if status == "FAIL":
            self.fails += 1
        elif status == "WARN":
            self.warns += 1

    def render(self) -> str:
        out = []
        out.append(c("╔══ DROSSCTL — host truth", "bold", "magenta"))
        out.append(c(f"║ {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}", "dim"))
        for sec in self.sections:
            out.append("")
            out.append(c(f"── {sec['title']} ", "bold", "cyan") + c("─" * max(0, 60 - len(sec['title'])), "dim"))
            for r in sec["rows"]:
                out.append(verdict_line(r["name"], r["status"], r["detail"]))
        out.append("")
        summary = f"{self.fails} fail, {self.warns} warn"
        style = "red" if self.fails else ("yellow" if self.warns else "green")
        out.append(c(f"══ {summary}", "bold", style))
        return "\n".join(out)


# ── helpers ─────────────────────────────────────────────────────────────────

def run_cmd(argv, timeout=45):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as exc:
        return 125, "", str(exc)


def run_cli(args, timeout=60):
    for cand in CLI_CANDIDATES:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return run_cmd([cand] + args, timeout=timeout)
    return 127, "", "no gateway-aligned openclaw CLI found"


def http_json(url: str, timeout=8):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def http_code(url: str, timeout=8) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def load_plist(path: str):
    """Tolerant plist reader. Some LaunchAgents have trailing junk after
    the root element, which makes plistlib raise. We take the first
    document only."""
    try:
        with open(path, "rb") as fh:
            return plistlib.load(fh)
    except Exception:
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
            end = raw.find(b"</plist>")
            if end == -1:
                return None
            return plistlib.loads(raw[: end + len(b"</plist>")])
        except Exception:
            return None


def age_hours(ts: float) -> float:
    return (time.time() - ts) / 3600.0


def fmt_age(hours: float) -> str:
    if hours < 1:
        return f"{int(hours * 60)}m ago"
    if hours < 48:
        return f"{int(hours)}h ago"
    return f"{int(hours / 24)}d ago"


def git(*args, cwd=WORKSPACE, timeout=30):
    rc, out, err = run_cmd(["git", "-C", cwd] + list(args), timeout=timeout)
    return rc, out.strip(), err.strip()


# ── section: OpenClaw crons ────────────────────────────────────────────────

def section_crons(board: Board) -> None:
    board.section("OpenClaw crons")
    rc, out, err = run_cli(["cron", "list", "--json"])
    if rc != 0:
        board.row("FAIL", "cron list", f"could not list: {(err or out)[:120]}")
        return
    try:
        data = json.loads(out)
    except ValueError:
        board.row("FAIL", "cron list", "invalid JSON from CLI")
        return
    jobs = data.get("jobs") or []
    if not jobs:
        board.row("WARN", "cron list", "no jobs returned")
        return
    ok = 0
    for job in jobs:
        name = job.get("name", "?")
        status = job.get("lastRunStatus")
        enabled = job.get("enabled", True)
        if not enabled:
            board.row("INFO", name, "disabled")
            continue
        if status == "error":
            errs = job.get("lastRunError") or "unknown error"
            nxt = job.get("nextRunAt") or "?"
            board.row("FAIL", name, f"last run failed: {errs[:70]} (next {nxt[:19]})")
        elif status == "ok":
            ok += 1
        elif status is None:
            board.row("WARN", name, "has never run")
        else:
            board.row("WARN", name, f"lastRunStatus={status}")
    if ok:
        board.row("PASS", "healthy jobs", f"{ok} of {len(jobs)} jobs last ran ok")


# ── section: launchd agents ────────────────────────────────────────────────

def schedule_cadence_hours(d: dict):
    """Return (kind, expected_max_gap_hours) for a launchd plist."""
    if d.get("StartInterval"):
        return ("interval", max(0.05, d["StartInterval"] / 3600.0))
    cal = d.get("StartCalendarInterval")
    if not cal:
        return ("runatload", None)
    entries = cal if isinstance(cal, list) else [cal]
    gaps = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if "Weekday" in entry:
            gaps.append(24 * 7)
        else:
            gaps.append(24)
    if not gaps:
        return ("calendar", 24)
    return ("calendar", float(max(gaps)))


def section_launchd(board: Board) -> None:
    board.section("launchd agents")
    if not os.path.isdir(PLIST_DIR):
        board.row("FAIL", "LaunchAgents", f"{PLIST_DIR} missing")
        return
    files = sorted(f for f in os.listdir(PLIST_DIR) if f.endswith(".plist"))
    stale_cutoff = 30 * 24  # 30 days = certainly dead
    checked = 0
    for fname in files:
        path = os.path.join(PLIST_DIR, fname)
        label = fname[: -len(".plist")]
        if not (label.startswith("ai.sol.") or label.startswith("com.dross.")
                or label.startswith("com.oz.") or label.startswith("com.stfinder.")):
            continue
        d = load_plist(path)
        if not d:
            board.row("WARN", label, "plist unreadable")
            continue
        checked += 1
        # launchd state: the authoritative "is it alive right now" signal.
        rc2, pout, _ = run_cmd(["launchctl", "print", f"gui/501/{label}"], timeout=15)
        loaded = rc2 == 0
        state = "?"
        exit_code = "?"
        runs = "?"
        pid = "?"
        if loaded:
            m = re.search(r"^\s*state = (\S+)", pout, re.M)
            if m:
                state = m.group(1)
            m = re.search(r"last exit code = (.+)", pout)
            if m:
                exit_code = m.group(1).strip()
            m = re.search(r"^\s*runs = (\d+)", pout, re.M)
            if m:
                runs = m.group(1)
            m = re.search(r"^\s*pid = (\d+)", pout, re.M)
            if m:
                pid = m.group(1)

        # run evidence: stdout mtime. This is the PRIMARY signal, because
        # launchd's "runs" counter resets every time the plist is reloaded
        # (the site-cron-watchdog reloads missing agents), so a healthy
        # daily agent can legitimately report runs = 0.
        out_path = d.get("StandardOutPath")
        mtime = None
        if out_path and os.path.exists(out_path):
            mtime = os.path.getmtime(out_path)
        kind, gap = schedule_cadence_hours(d)
        hours = age_hours(mtime) if mtime else None

        if not loaded:
            # A one-shot RunAtLoad job legitimately leaves the launchd list
            # once it has completed. That is not a failure. But a job that
            # is supposed to be a long-lived daemon and is absent IS.
            retired = any(
                os.path.exists(os.path.join(PLIST_DIR, fname + ".bak"))
                or any(n.startswith(fname + ".bak")
                       for n in os.listdir(PLIST_DIR))
                for _ in [0]
            )
            if retired:
                board.row("INFO", label, "not loaded (backup plist present — retired?)")
            elif d.get("KeepAlive") and not d.get("StartCalendarInterval"):
                board.row("FAIL", label, "NOT LOADED, but it is a KeepAlive daemon")
            else:
                board.row("WARN", label, "not in launchd (one-shot or retired?)")
            continue

        if state == "running":
            board.row("PASS", label, f"running, pid {pid} — daemon alive")
            continue

        # A numeric non-zero exit code is a genuine failure. "(never exited)"
        # is NOT a failure: it means the job has not exited yet, which is
        # the normal state for a calendar job that is waiting for its slot.
        if exit_code not in ("0", "?", "(never exited)"):
            board.row("FAIL", label, f"last exit code {exit_code} (runs={runs})")
            continue

        if hours is None:
            board.row("WARN", label, f"{kind}, never produced output (runs={runs}, exit={exit_code})")
            continue

        # An EMPTY stdout file means the agent does not write to stdout at
        # all (solscribe sends its own output to ~/Projects/solscribe/
        # backups/ and leaves stdout empty). Calling that "stale" is a lie:
        # on 2026-11-10 drossctl flagged ai.sol.solscribe as 141 days dead
        # while it had in fact run at 02:00 that very morning. When stdout
        # is empty we have no evidence, so we say so instead of guessing.
        if os.path.getsize(out_path) == 0:
            board.row("INFO", label,
                      f"{kind}, stdout empty — liveness unknown from stdout (runs={runs})")
            continue

        if gap and hours > max(gap * 2.5, 72):
            board.row("FAIL", label,
                      f"stale: {kind} expected every ~{gap:.0f}h, last output {fmt_age(hours)}")
            continue
        if gap and hours > max(gap * 1.5, 36):
            board.row("WARN", label, f"late: {kind} ~{gap:.0f}h cadence, last output {fmt_age(hours)}")
            continue
        if hours > stale_cutoff:
            board.row("WARN", label, f"very stale: last output {fmt_age(hours)}")
            continue
        board.row("PASS", label, f"{kind}, last output {fmt_age(hours)} (runs={runs}, exit={exit_code})")


# ── section: model endpoints ───────────────────────────────────────────────

def configured_providers():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception:
        return {}
    return (cfg.get("models") or {}).get("providers") or {}


def section_models(board: Board) -> None:
    board.section("model endpoints")
    providers = configured_providers()
    if not providers:
        board.row("FAIL", "gateway config", "no model providers found in openclaw.json")
    wired = set()
    for pname, prov in providers.items():
        base = (prov.get("baseUrl") or "").rstrip("/")
        if not base:
            continue
        wired.add(base)
        api = prov.get("api") or ""
        ids = []
        if api == "anthropic-messages":
            # Anthropic-compatible APIs have no /models endpoint. Probing it
            # returns 404 and used to be reported as "provider DEAD" — a
            # confident lie about a provider that was working fine. For a
            # remote API, prove reachability instead of a model list.
            code = http_code(base + "/v1/models", timeout=8)
            if code == 0:
                board.row("FAIL", pname, f"configured but UNREACHABLE: {base}")
            else:
                board.row("PASS", pname, f"alive {base} (anthropic-messages, remote API)")
            continue
        # OpenAI-compatible providers: try /models, and for Ollama's native
        # API try /api/tags too, because baseUrl may omit the /v1 prefix.
        data = http_json(base + "/models", timeout=8)
        if data is None and "11434" in base:
            tags = http_json(base + "/api/tags", timeout=8)
            if tags is not None:
                ids = [m.get("name") for m in (tags.get("models") or [])][:4]
                board.row("PASS", pname, f"alive {base} (ollama native) -> {', '.join(map(str, ids))}")
                continue
        if data is None:
            board.row("FAIL", pname, f"configured but DEAD: {base}")
            continue
        ids = [m.get("id") for m in (data.get("data") or [])][:4]
        shown = ", ".join(str(i) for i in ids) or "(no models)"
        board.row("PASS", pname, f"alive {base} -> {shown}")
    # ollama native
    tags = http_json("http://127.0.0.1:11434/api/tags", timeout=8)
    if tags is None:
        board.row("FAIL", "ollama", "127.0.0.1:11434 unreachable")
    else:
        board.row("PASS", "ollama", f"{len(tags.get('models') or [])} models installed")
    # splash services
    for name, svc in SERVICES.items():
        data = http_json(f"http://127.0.0.1:{svc['port']}/v1/models", timeout=8)
        if data is None:
            board.row("WARN", name, f"port {svc['port']} down — {svc['desc']}")
            continue
        ids = [m.get("id") for m in (data.get("data") or [])]
        board.row("PASS", name, f"port {svc['port']} alive -> {', '.join(map(str, ids)) or '?'}")
    # alive but unwired
    unwired = []
    for port in (8000, 8200, 8300):
        if http_json(f"http://127.0.0.1:{port}/v1/models", timeout=4) is not None:
            if not any(str(port) in w for w in wired):
                unwired.append(str(port))
    if unwired:
        board.row("WARN", "unwired endpoints",
                  f"live on :{', :'.join(unwired)} but not in gateway models.providers")


# ── section: serve ─────────────────────────────────────────────────────────

def section_serve(board: Board, command=None, target=None):
    board.section("local model servers")
    for name, svc in SERVICES.items():
        alive = http_json(f"http://127.0.0.1:{svc['port']}/v1/models", timeout=6) is not None
        if command == "start" and target == name and not alive:
            binary = svc["cmd"][0]
            if not os.path.exists(binary):
                board.row("FAIL", name, f"cannot start: {binary} missing")
                continue
            log = os.path.join(OPENCLAW_HOME, "tmp", f"{name}.log")
            os.makedirs(os.path.dirname(log), exist_ok=True)
            rc, out, err = run_cmd(
                ["/bin/bash", "-c",
                 f"nohup {binary} serve --model {svc['model']} --port {svc['port']} "
                 f"--max-memory 90G > {log} 2>&1 & disown"],
                timeout=20)
            time.sleep(2)
            board.row("INFO", name, f"start issued (log: {log})")
        elif command == "stop" and target == name:
            rc, out, err = run_cmd(["/bin/bash", "-c",
                                    f"pkill -f 'splash serve --model {svc['model']}' || true"],
                                   timeout=20)
            board.row("INFO", name, "stop issued")
        else:
            state = "alive" if alive else "DOWN"
            style = "PASS" if alive else "WARN"
            board.row(style, name, f"{state} on :{svc['port']} — {svc['desc']}")


# ── section: git / publishing ──────────────────────────────────────────────

def section_git(board: Board) -> None:
    board.section("git & publishing")
    if not os.path.isdir(os.path.join(WORKSPACE, ".git")):
        board.row("INFO", "workspace", "not a git repo")
        return
    rc, out, _ = git("status", "--porcelain")
    dirty = len([l for l in out.splitlines() if l.strip()]) if rc == 0 else -1
    rc2, unpushed, _ = git("log", "--oneline", "origin/main..HEAD")
    n_unpushed = len(unpushed.splitlines()) if rc2 == 0 else -1
    if n_unpushed > 0:
        board.row("WARN", "unpushed commits", f"{n_unpushed} commit(s) not on origin/main")
    elif n_unpushed == 0:
        board.row("PASS", "unpushed commits", "0 — local main matches origin/main")
    if dirty > 0:
        board.row("INFO", "working tree", f"{dirty} uncommitted change(s)")
    # last backup log verdict
    log = os.path.join(WORKSPACE, "scripts", "backup.log")
    if os.path.exists(log):
        try:
            with open(log, encoding="utf-8", errors="ignore") as fh:
                tail = [l.rstrip() for l in fh.readlines()[-60:]]
            verdict = None
            for line in reversed(tail):
                if "SUCCESS" in line or "BLOCKED" in line or "FAILED" in line:
                    verdict = line
                    break
            if verdict:
                if "SUCCESS" in verdict:
                    board.row("PASS", "last backup", verdict.split("|", 1)[-1].strip()[:80])
                else:
                    board.row("FAIL", "last backup", verdict.split("|", 1)[-1].strip()[:80])
            else:
                board.row("WARN", "last backup", "no verdict line found in backup.log")
        except OSError:
            pass
    # stale failure log (the one nobody reads)
    flog = os.path.join(WORKSPACE, "scripts", "backup_failure.log")
    if os.path.exists(flog):
        try:
            mtime = os.path.getmtime(flog)
            age = age_hours(mtime)
            if age > 24 * 7:
                board.row("INFO", "backup_failure.log",
                          f"stale by {int(age / 24)}d — the failure log nobody watches")
        except OSError:
            pass


# ── main ───────────────────────────────────────────────────────────────────

def build_board() -> Board:
    board = Board()
    section_crons(board)
    section_launchd(board)
    section_models(board)
    section_serve(board)
    section_git(board)
    return board


def main() -> int:
    parser = argparse.ArgumentParser(prog="drossctl", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("status")
    sub.add_parser("crons")
    sub.add_parser("launchd")
    sub.add_parser("models")
    sub.add_parser("git")
    p_serve = sub.add_parser("serve")
    p_serve.add_argument("action", choices=["status", "start", "stop"])
    p_serve.add_argument("name", nargs="?", choices=sorted(SERVICES.keys()))
    sub.add_parser("json")
    args = parser.parse_args()

    cmd = args.cmd or "status"
    if cmd == "serve":
        if args.action in ("start", "stop") and not args.name:
            print("serve start/stop needs a service name", file=sys.stderr)
            return 1
        board = Board()
        section_serve(board, args.action, args.name)
        print(board.render())
        return 0

    board = build_board()

    if cmd == "json":
        print(json.dumps({"sections": board.sections,
                          "fails": board.fails, "warns": board.warns}, indent=2))
        return 0

    if cmd != "status":
        keep = {"crons": "OpenClaw crons", "launchd": "launchd agents",
                "models": "model endpoints", "git": "git & publishing"}[cmd]
        board.sections = [s for s in board.sections if s["title"] == keep]
        board.fails = sum(1 for s in board.sections for r in s["rows"] if r["status"] == "FAIL")
        board.warns = sum(1 for s in board.sections for r in s["rows"] if r["status"] == "WARN")

    print(board.render())
    return 2 if board.fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
