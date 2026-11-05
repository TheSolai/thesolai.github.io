#!/usr/bin/env python3
"""
claw-doctor.py — reliability doctor for the Dross OpenClaw host.

Answers one question with evidence: "is the agent runtime healthy right now,
and is it getting healthier or sicker?"

It measures. It does not theorise. Every check reads a live source of truth
(the OpenClaw JSON log, the CLI, the skill catalogue, the git tree) and
reports PASS / WARN / FAIL with the specific evidence behind it. The point is
to replace "I think it's fine" with "here is the number, and here is how it
moved since last time".

Design rules (learned the hard way on 2026-10-24):
  * Read-only. It never mutates config, sessions, git, or the filesystem.
  * Stdlib only. No third-party imports — this must run when everything else
    is broken.
  * It resolves the OpenClaw CLI explicitly. A bare `openclaw` on PATH is the
    stale 2026.6.35 Homebrew build which rejects the current config as
    invalid, so every bare-CLI call in this repo has been a false failure.
  * It never prints secrets, and never prints a whole log line that might
    contain one. Evidence is redacted to the fields we care about.
  * It measures the *live* signal, not a proxy. "Compaction truncated" is read
    from the log because that is where the symptom actually shows up.
  * It tells the three failure modes apart, because they have different fixes:
      - provider-refused overflow   (error=400:)   -> compaction ran too late
      - locally-caught overflow     (error=Context) -> the precheck WORKING
      - lossy compaction artifact  (loss=...)       -> a separate axis entirely
    A doctor that lumps them together produces confident nonsense.

Usage:
    claw-doctor.py                 # full human report
    claw-doctor.py --json          # machine-readable
    claw-doctor.py --cron          # cron mode: NO_REPLY when healthy
    claw-doctor.py --window-hours 12
    claw-doctor.py --update-baseline   # accept current config as the baseline

Exit codes:
    0  the doctor ran (findings may still be present — see the report)
    1  the doctor itself could not run
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------
# Constants / paths
# --------------------------------------------------------------------------

HOME = os.path.expanduser("~")
OPENCLAW_HOME = os.path.join(HOME, ".openclaw")
WORKSPACE = os.path.join(OPENCLAW_HOME, "workspace")
STATE_DIR = os.path.join(OPENCLAW_HOME, "state", "claw-doctor")
BASELINE_PATH = os.path.join(STATE_DIR, "baseline.json")
HISTORY_PATH = os.path.join(STATE_DIR, "history.jsonl")
REPORT_PATH = os.path.join(STATE_DIR, "last-report.json")

# The structured log. JSON lines, named for the LOCAL date. Each record has
# `time` (local, with offset) and `_meta.date` (UTC). We read `time` and
# treat it as authoritative for event ordering.
LOG_DIR = "/tmp/openclaw"
LOG_GLOB = os.path.join(LOG_DIR, "openclaw-*.log")
# Fallback: the plain-text gateway log, same events, different format.
GATEWAY_LOG = os.path.join(HOME, "Library", "Logs", "openclaw", "gateway.log")

CONFIG_PATH = os.path.join(OPENCLAW_HOME, "openclaw.json")
SESSION_STORE = os.path.join(OPENCLAW_HOME, "agents", "main", "agent",
                             "openclaw-agent.sqlite")
IMPORT_ARCHIVE = os.path.join(OPENCLAW_HOME, "agents", "main",
                              "session-sqlite-import-archive")
MIGRATION_STUCK = os.path.join(
    OPENCLAW_HOME, "agents", "main", "agent",
    "openclaw-agent.sqlite.migration-stuck.184253")

# Gateway-aligned CLI. The PATH binary is 2026.6.35 and rejects this config.
CLI_CANDIDATES = [
    os.path.join(OPENCLAW_HOME, "tools", "current-bin", "openclaw"),
    os.path.join(OPENCLAW_HOME, "tools", "node-v24.21.0", "bin", "openclaw"),
]

# Compaction settings the runtime expects. From the workshop skill
# `context-overflow-recovery`, verified against the config schema:
#   keepRecentTokens  20000  (default)
#   recentTurnsPreserve    3  (default, max 12)
#
# The two knobs push in OPPOSITE directions on the loss axis, so they must be
# judged separately (see budgetCompactionSummary in the OpenClaw compaction
# module, which splits ONE char budget -- capped at 16000 -- between the
# summary body and the retained suffix):
#
#   keepRecentTokens   how many recent tokens stay RAW after compaction.
#                      LOW  -> more content is pushed into the summary body
#                              -> the body gets trimmed -> `summary-tail`.
#                      HIGH -> less in the body. Better on the loss axis.
#
#   recentTurnsPreserve  how many recent user turns are preserved VERBATIM in
#                      the retained suffix, together with every tool call and
#                      tool result they contain. A single turn can be hundreds
#                      of KB, so a high value makes the suffix enormous, the
#                      body gets squeezed to maxChars/2, and the loss is
#                      `summary-tail` (and `suffix-head`).
#                      LOW  -> smaller suffix -> body survives intact.
#                      HIGH -> worse on the loss axis.
#
# So: keepRecentTokens at or above its default is good; recentTurnsPreserve at
# or below its default is good. Setting recentTurnsPreserve to 0 is a
# deliberate, sanctioned deviation -- see SANCTIONED_COMPACTION.
EXPECTED_COMPACTION = {
    "keepRecentTokens": 20000,
    "recentTurnsPreserve": 3,
}

# Deviations from the documented defaults that are deliberate and safe, with
# the reason. The doctor must not cry wolf about these.
SANCTIONED_COMPACTION = {
    "recentTurnsPreserve": (
        0,
        "the preserved turns are the suffix hog: each preserved turn carries "
        "every tool call and tool result verbatim, so with a bot that runs "
        "dozens of tool calls per turn the suffix exceeds the 16000-char "
        "artifact budget, the summary body is squeezed to half of it and the "
        "artifact is cut (loss=summary-tail). With preserve=0 the suffix is "
        "only the structural sections plus the workspace context, so the body "
        "keeps the whole budget. Verified 2026-10-28: a compaction after this "
        "change completed with no loss line.",
    ),
}

# Cron contracts that must not silently regress.
CRON_MUST_BE_ENABLED = [
    ("Blog Post", "Weekly long-form post"),
    ("Agent Blog Network", "Blog network sync"),
]

# RULE 9 (permanent, set by Amre on 2026-10-31): "Books are finished."
# Do not recommend books, do not deliver books, and do not recreate any book
# skill, script, cron or launchd agent.
#
# The "Sol — Horror Book" cron was removed on 2026-10-31 as part of that
# instruction, so this Doctor must NOT demand it back. It used to, which
# turned a deliberate removal into a standing FAIL and would have pushed a
# future agent into recreating exactly what RULE 9 forbids. The check below
# is now inverted: it fails if a book delivery path REAPPEARS.
BOOK_DELIVERY_MARKERS = ("horror book", "kindle", "zlib", "book deliver",
                         "book-deliver", "daily book")

# Re-alert the same ongoing failure at most this often (seconds).
# 24h, not 6h: the doctor runs every 3h, so a 6h window re-woke Amre every
# other cycle for the same unresolved failure. That is a spam loop.
REALERT_SECONDS = 24 * 3600

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def now_utc():
    return datetime.now(timezone.utc)


def parse_ts(value):
    """Parse an ISO timestamp with offset. Returns tz-aware UTC or None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def run_cli(args, timeout=45):
    """Run the gateway-aligned OpenClaw CLI. Returns (rc, stdout, stderr)."""
    for cand in CLI_CANDIDATES:
        if not (os.path.isfile(cand) and os.access(cand, os.X_OK)):
            continue
        try:
            proc = subprocess.run([cand] + args, capture_output=True,
                                  text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, "", f"timeout running openclaw {' '.join(args)}"
        except OSError as exc:
            return 125, "", str(exc)
        return proc.returncode, proc.stdout, proc.stderr
    return 127, "", "no gateway-aligned openclaw CLI found"


def cli_json(args, timeout=45):
    """Run the CLI and parse JSON stdout. Returns (data, error)."""
    rc, out, err = run_cli(args, timeout=timeout)
    if rc != 0:
        return None, (err or out or f"rc={rc}").strip()[:300]
    try:
        return json.loads(out), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"


def dir_size(path):
    """Total size in bytes of a directory tree, or None if absent."""
    if not os.path.exists(path):
        return None
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def human_size(n):
    if n is None:
        return "n/a"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024.0
    return str(n)


def clip_text(text, limit):
    """Bound a rendered string to `limit` characters.

    Every string that reaches the chat goes through here. The 2026-10-29
    flood was 228,829 characters in one report, so an unbounded field is
    the whole problem: bounding only the evidence list leaves a single
    enormous `detail` free to flood on its own.
    """
    if text is None:
        return text
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + f" ... (+{len(text) - limit} chars)"


def git(args, cwd=WORKSPACE, timeout=30):
    try:
        proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (subprocess.TimeoutExpired, OSError) as exc:
        return 1, "", str(exc)


# --------------------------------------------------------------------------
# Log reading
# --------------------------------------------------------------------------

MARKERS = (
    "context-overflow-diag",
    "context-overflow-midturn-precheck",
    "Compaction safeguard",
    "config change detected",
    "config hot reload applied",
    "tool-search: cataloged",
)


def read_log_events(window_hours):
    """
    Return structured events for the window, from the JSON log if present,
    else from the plain-text gateway log.

    Event dicts: {kind, at (UTC datetime), text}
    """
    cutoff = now_utc() - timedelta(hours=window_hours)
    events = []
    files = sorted(glob.glob(LOG_GLOB))
    if files:
        for path in files:
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if not any(m in line for m in MARKERS):
                            continue
                        try:
                            rec = json.loads(line)
                        except (json.JSONDecodeError, ValueError):
                            continue
                        text = rec.get("message") or rec.get("1") or ""
                        if not text:
                            continue
                        ts = parse_ts(rec.get("time"))
                        if ts and ts < cutoff:
                            continue
                        kind = classify(text)
                        if kind:
                            events.append({"kind": kind, "at": ts, "text": text})
            except OSError:
                continue
        if events:
            return events, "json"

    # Fallback: plain-text gateway log.
    try:
        with open(GATEWAY_LOG, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not any(m in line for m in MARKERS):
                    continue
                ts = None
                m = re.match(r"^(\S+)", line)
                if m:
                    ts = parse_ts(m.group(1))
                if ts and ts < cutoff:
                    continue
                kind = classify(line)
                if kind:
                    events.append({"kind": kind, "at": ts, "text": line})
    except OSError:
        pass
    return events, "text"


def classify(text):
    if "context-overflow-midturn-precheck" in text:
        return "precheck"
    if "context-overflow-diag" in text:
        return "overflow"
    if "Compaction safeguard" in text:
        return "truncation"
    if "config change detected" in text or "config hot reload applied" in text:
        return "config-reload"
    if "tool-search: cataloged" in text:
        return "toolsearch"
    return None


def field(text, name, cast=str):
    m = re.search(rf"{re.escape(name)}=([^\s\"]+)", text)
    if not m:
        return None
    raw = m.group(1)
    try:
        return cast(raw)
    except (TypeError, ValueError):
        return raw


# --------------------------------------------------------------------------
# Check framework
# --------------------------------------------------------------------------

class Check:
    # Hard ceiling on evidence lines per check. A chat message that gets
    # chunked into 90 Telegram parts is a spam incident, not a report.
    MAX_EVIDENCE = 12
    # Same ceiling for the detail prose. Capping only the evidence list
    # leaves a hole: any check that builds one enormous detail string (a
    # pasted log, a long path list) still floods the chat.
    MAX_DETAIL = 400
    # The fix line gets a larger ceiling than the detail, because it carries
    # the actual remediation and truncating it mid-sentence makes it useless.
    # It is still bounded: an unbounded fix is the same flood, spelled
    # differently.
    MAX_FIX = 1500

    def __init__(self, cid, title, status, detail, evidence=None, fix=None):
        self.cid = cid
        self.title = title
        self.status = status          # PASS | WARN | FAIL | INFO
        self.detail = clip_text(detail, self.MAX_DETAIL)
        ev = list(evidence or [])
        if len(ev) > self.MAX_EVIDENCE:
            dropped = len(ev) - self.MAX_EVIDENCE
            ev = ev[:self.MAX_EVIDENCE] + [f"... and {dropped} more line(s)"]
        self.evidence = [clip_text(e, 200) for e in ev]
        self.fix = clip_text(fix, self.MAX_FIX) if fix else fix

    def to_dict(self):
        return {
            "id": self.cid,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "evidence": self.evidence,
            "fix": self.fix,
        }


# Build output and dependency trees are not "work in progress". Counting
# thousands of Rust target/ files as dirt produced a 2550-line report that
# Telegram split into ~90 messages on 2026-10-29.
NOISE_PATTERNS = ("/target/", "node_modules/", "/.venv/", "__pycache__/",
                  "/dist/", "/build/", ".pytest_cache/")


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_gateway_alive():
    ev = []
    ok = False
    if os.path.exists(GATEWAY_LOG):
        age = time.time() - os.path.getmtime(GATEWAY_LOG)
        ev.append(f"gateway.log last write {age / 60:.1f} min ago "
                  f"({human_size(os.path.getsize(GATEWAY_LOG))})")
        ok = age < 1800
    else:
        ev.append(f"gateway.log missing at {GATEWAY_LOG}")

    rc, out, _ = run_cli(["--version"], timeout=30)
    if rc == 0 and out.strip():
        ev.append(f"CLI: {out.strip().splitlines()[-1]}")
    else:
        ev.append(f"CLI not runnable (rc={rc})")

    if ok:
        return Check("gateway", "Gateway is alive and logging",
                     "PASS", "gateway.log is fresh", ev)
    return Check("gateway", "Gateway is alive and logging", "FAIL",
                 "gateway.log is stale or missing", ev,
                 "check the launchd service ai.openclaw.gateway")


def _at(e):
    """Sort key for an event; undated events sort oldest."""
    return e["at"] or datetime.min.replace(tzinfo=timezone.utc)


def split_overflows(events):
    """Partition overflow events into provider-refused, locally-caught, other."""
    ovs = [e for e in events if e["kind"] == "overflow"]
    refused, caught, other = [], [], []
    for e in ovs:
        if "error=400:" in e["text"]:
            refused.append(e)
        elif "error=Context" in e["text"]:
            caught.append(e)
        else:
            other.append(e)
    return refused, caught, other


def check_overflow(events, window_hours):
    """
    Provider-refused overflow is the failure. A locally-caught overflow
    (error=Context) means the mid-turn precheck did its job.

    The verdict is about NOW, not about history. Overflows that happened
    before the guard was switched on are history, not a live defect; a
    doctor that reports them as a current failure trains its reader to
    ignore it. So: the state is FAIL only if the most recent refusal came
    AFTER the most recent local catch.
    """
    refused, caught, other = split_overflows(events)

    ev = []
    for e in sorted(refused + caught + other, key=_at)[-8:]:
        tag = ("REFUSED" if e in refused
               else "caught" if e in caught else "other")
        ts = e["at"].isoformat() if e["at"] else "?"
        sess = str(field(e["text"], "sessionKey") or "?")[-46:]
        tok = field(e["text"], "compactionTokens", int)
        ev.append(f"{ts} {tag} tokens={tok} session=...{sess}")

    last_refused = max((_at(e) for e in refused), default=None)
    last_caught = max((_at(e) for e in caught), default=None)

    if refused and (last_caught is None or last_refused > last_caught):
        return Check(
            "overflow", "Overflows are caught before the provider sees them",
            "FAIL",
            f"the most recent overflow ({last_refused.isoformat()}) was "
            f"REFUSED by the provider — {len(refused)} refusal(s) in the last "
            f"{window_hours}h and the latest local catch is older",
            ev,
            "compaction is running too late; check that midTurnPrecheck is "
            "enabled and maxActiveTranscriptBytes trips before the wall")

    if caught:
        stale = ""
        if last_refused:
            age = (last_caught - last_refused).total_seconds() / 3600.0
            stale = (f" The last provider refusal was {age:.1f}h before the "
                     f"most recent local catch, so the guard has been working "
                     f"since then.")
        return Check(
            "overflow", "Overflows are caught before the provider sees them",
            "PASS",
            f"0 provider refusals since {last_caught.isoformat()}; "
            f"{len(caught)} overflow(s) caught locally by the precheck in the "
            f"last {window_hours}h.{stale}",
            ev)

    if other:
        return Check("overflow", "Overflows are caught before the provider sees them",
                     "WARN", f"{len(other)} unclassified overflow(s)", ev)
    return Check("overflow", "Overflows are caught before the provider sees them",
                 "PASS", f"0 overflows in the last {window_hours}h")


def check_precheck_coverage(events, window_hours):
    """
    The precheck must fire as often as it catches. A precheck line count that
    diverges from the local-catch count means the guard is not covering the
    path that is failing.
    """
    refused, caught, _other = split_overflows(events)
    last_refused = max((_at(e) for e in refused), default=None)
    prechecks = [e for e in events if e["kind"] == "precheck"]
    # Only the current regime counts: events after the last provider refusal.
    if last_refused:
        prechecks = [e for e in prechecks if _at(e) > last_refused]
        caught = [e for e in caught if _at(e) > last_refused]

    ev = []
    for e in prechecks[-5:]:
        ts = e["at"].isoformat() if e["at"] else "?"
        ev.append(f"{ts} route={field(e['text'], 'route')} "
                  f"est={field(e['text'], 'estimatedPromptTokens', int)} "
                  f"budget={field(e['text'], 'promptBudgetBeforeReserve', int)} "
                  f"reserve={field(e['text'], 'effectiveReserveTokens', int)}")

    if not prechecks and not caught:
        return Check("precheck", "Precheck covers every local catch", "PASS",
                     "no overflows to cover")
    if not caught:
        return Check("precheck", "Precheck covers every local catch", "FAIL",
                     f"the precheck fired {len(prechecks)} time(s) but no "
                     f"overflow was caught locally — the guard is not closing "
                     f"the path that is failing",
                     ev,
                     "lower maxActiveTranscriptBytes so the precheck trips "
                     "before the provider wall")
    if len(prechecks) < len(caught):
        return Check("precheck", "Precheck covers every local catch", "WARN",
                     f"{len(caught)} local catch(es) but only {len(prechecks)} "
                     f"precheck line(s)", ev)
    return Check("precheck", "Precheck covers every local catch", "PASS",
                 f"{len(prechecks)} precheck fire(s) for {len(caught)} local "
                 f"catch(es)", ev)


def last_knob_change(events):
    """
    Timestamp of the most recent config change to the compaction knobs.
    This is the boundary between "the configuration that produced the old
    failures" and "the configuration running now".
    """
    times = []
    for e in events:
        if e["kind"] != "config-reload":
            continue
        if "keepRecentTokens" in e["text"] or "recentTurnsPreserve" in e["text"]:
            if e["at"]:
                times.append(e["at"])
    return max(times) if times else None


def check_truncation(events, window_hours):
    """
    Lossy compaction — a SEPARATE axis from overflow. Tuning the overflow
    knobs does not remove it.

    The loss axis is NOT tunable by keepRecentTokens/recentTurnsPreserve.
    Verified 2026-10-24: it fired at 8000/2 (08:40, 08:59) AND again at
    the restored defaults 20000/3 (09:52, 10:17, 10:34) — i.e. after the
    hot reload at 09:19:40. Both directions lose, so neither knob is a fix.
    """
    trunc = [e for e in events if e["kind"] == "truncation"]

    # Same rule as the overflow check: judge the CURRENT regime. Truncations
    # that happened before keepRecentTokens was last changed describe the old
    # configuration, not the one running now. The boundary is the last config
    # change to the compaction knobs.
    boundary = last_knob_change(events)
    if boundary:
        current = [e for e in trunc if _at(e) > boundary]
        history = len(trunc) - len(current)
    else:
        current = trunc
        history = 0

    if not current:
        extra = (f" ({history} older truncation(s) before the last compaction "
                 f"config change are historical, not current)")
        return Check("truncation", "Compaction artifacts are intact", "PASS",
                     f"0 truncated compaction artifacts since the last "
                     f"compaction config change{extra}")

    trunc = current

    kinds = {}
    for e in trunc:
        loss = field(e["text"], "loss") or "?"
        for k in str(loss).split(","):
            kinds[k] = kinds.get(k, 0) + 1
    ev = [f"{e['at'].isoformat() if e['at'] else '?'} "
          f"loss={field(e['text'], 'loss')}" for e in trunc[-8:]]
    ev.append("loss kinds: " + ", ".join(f"{k}={v}" for k, v in kinds.items()))
    return Check(
        "truncation", "Compaction artifact loss detected", "WARN",
        f"{len(trunc)} lossy compaction(s) since the last compaction config "
        f"change — the artifact was cut, so content was silently dropped. "
        f"This is NOT the overflow axis and the overflow knobs do not fix it",
        ev,
        f"raising keepRecentTokens is not the fix for this axis, and the "
        f"overflow knobs do not fix it either — this axis is budget "
        f"competition between the summary body, the "
        f"retained suffix and the preserved turn inside one char budget "
        f"(cap 16000). budgetCompactionSummary() reserves min(suffix.length, "
        f"maxChars) for the suffix and floors the body at ceil(maxChars/2), "
        f"so a suffix that exceeds half the budget squeezes the body and the "
        f"artifact is cut. The suffix's bulk is preservedTurnsSection — the "
        f"last N user turns kept VERBATIM with every tool call and tool "
        f"result they contain, which for this agent is hundreds of KB per "
        f"turn. Fix: set recentTurnsPreserve=0 (and keepRecentTokens at or "
        f"above {EXPECTED_COMPACTION['keepRecentTokens']}), so the suffix "
        f"holds only the structural sections and the body keeps the whole "
        f"budget. Also keep agents.defaults.contextLimits."
        f"postCompactionMaxChars small so the injected workspace context "
        f"does not compete for the same budget.")


def check_compaction_config():
    data, err = cli_json(["config", "get", "agents.defaults.compaction"])
    if err:
        return Check("compaction-config", "Compaction config is sane",
                     "WARN", f"could not read config: {err}")
    problems = []
    if not data.get("midTurnPrecheck", {}).get("enabled"):
        problems.append("midTurnPrecheck is disabled")
    if not data.get("maxActiveTranscriptBytes"):
        problems.append("maxActiveTranscriptBytes is unset (no preflight guard)")
    ev = [f"{k}={v}" for k, v in sorted(data.items())
          if not isinstance(v, (dict, list))]
    if problems:
        return Check("compaction-config", "Compaction config is sane", "WARN",
                     "; ".join(problems), ev,
                     "openclaw config set agents.defaults.compaction.<key> <value>")
    return Check("compaction-config", "Compaction config is sane", "PASS",
                 "all compaction guards are in place", ev)


def check_config_drift():
    """
    Catch silent rewrites of the compaction config. This is how 12000/3
    became 8000/2 — an internal session tuned the knobs without asking,
    and the change made truncation worse.
    """
    try:
        with open(CONFIG_PATH) as fh:
            current = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return Check("config-drift", "Compaction knobs match the baseline",
                     "WARN", f"could not read {CONFIG_PATH}: {exc}")

    live = (current.get("agents", {}).get("defaults", {})
            .get("compaction", {}))

    state = load_state()
    baseline = state.get("baseline")

    # Two different questions:
    #   1. does the live config match the DOCUMENTED runtime defaults?
    #   2. did it change since the doctor last looked?
    # The first is a defect ONLY in the direction that hurts: keepRecentTokens
    # BELOW its default pushes more content into the summary body and makes
    # summary-tail loss MORE likely; recentTurnsPreserve ABOVE its default
    # makes the retained suffix huge and squeezes the body the same way.
    # The opposite directions are improvements, not defects, and the
    # deliberate ones are sanctioned (SANCTIONED_COMPACTION).
    # The second is only news.
    expected_diffs = []
    sanctioned = []
    for key, want in sorted(EXPECTED_COMPACTION.items()):
        have = live.get(key)
        if have == want:
            continue
        sanctioned_spec = SANCTIONED_COMPACTION.get(key)
        if sanctioned_spec and have == sanctioned_spec[0]:
            sanctioned.append(f"{key}: {have} (sanctioned deviation)")
            continue
        hurts = (have < want) if key == "keepRecentTokens" else (have > want)
        if hurts:
            expected_diffs.append(
                f"{key}: {have} (documented default {want}) — this direction "
                f"makes summary-tail loss MORE likely")
        else:
            sanctioned.append(
                f"{key}: {have} (documented default {want}) — this direction "
                f"reduces loss")

    changed = []
    if baseline:
        for key in sorted(set(baseline) | set(live)):
            old, new = baseline.get(key), live.get(key)
            if old != new:
                changed.append(f"{key}: {old} -> {new}")

    state["baseline"] = dict(live)
    state["reported"] = state.get("reported", {})
    save_state(state)

    ev = [f"live: {k}={live.get(k)}" for k in sorted(live)
          if not isinstance(live.get(k), (dict, list))]
    mtime = ""
    try:
        mtime = datetime.fromtimestamp(
            os.path.getmtime(CONFIG_PATH)).astimezone().strftime("%Y-%m-%d %H:%M")
    except OSError:
        pass
    if mtime:
        ev.append(f"config file last modified {mtime}")

    if expected_diffs:
        return Check(
            "config-drift", "Compaction knobs are in the safe direction",
            "WARN",
            f"{len(expected_diffs)} compaction knob(s) sit in the direction "
            f"that makes summary-tail loss more likely",
            ev + expected_diffs + sanctioned,
            f"keepRecentTokens must be >= {EXPECTED_COMPACTION['keepRecentTokens']} "
            f"and recentTurnsPreserve <= "
            f"{EXPECTED_COMPACTION['recentTurnsPreserve']}")

    if sanctioned:
        return Check(
            "config-drift", "Compaction knobs are in the safe direction",
            "INFO",
            f"{len(sanctioned)} compaction knob(s) differ from the documented "
            f"runtime default in the direction that REDUCES artifact loss",
            ev + sanctioned,
            "no action needed — see SANCTIONED_COMPACTION in "
            "scripts/health/claw-doctor.py for the reasoning")

    if changed:
        return Check(
            "config-drift", "Compaction knobs are in the safe direction",
            "INFO",
            f"{len(changed)} compaction setting(s) changed since the last "
            f"doctor run (the live values still match the documented "
            f"defaults)", ev + changed,
            "find the writer in the config-reload events below")

    return Check("config-drift", "Compaction knobs are in the safe direction",
                 "PASS",
                 f"keepRecentTokens={live.get('keepRecentTokens')}, "
                 f"recentTurnsPreserve={live.get('recentTurnsPreserve')} — "
                 f"both at the documented runtime defaults", ev)


def check_config_reload_events(events, window_hours):
    """Who changed the config, and when."""
    rel = [e for e in events if e["kind"] == "config-reload"]
    if not rel:
        return Check("config-reload", "No recent config rewrites", "PASS",
                     f"no config changes detected in {window_hours}h")
    ev = []
    for e in rel[-10:]:
        path = re.search(r"\((agents\.[^)]+)\)", e["text"])
        ev.append(f"{e['at'].isoformat() if e['at'] else '?'} "
                  f"{'applied' if 'applied' in e['text'] else 'detected'} "
                  f"{path.group(1) if path else '?'}")
    return Check("config-reload", "No recent config rewrites", "INFO",
                 f"{len(rel)} config reload event(s) in {window_hours}h", ev)


def check_skill_frontmatter():
    """Every SKILL.md needs a description, or the model never sees it."""
    roots = [
        os.path.join(OPENCLAW_HOME, "skills"),
        os.path.join(WORKSPACE, "skills"),
        os.path.join(WORKSPACE, ".agents", "skills"),
        os.path.join(OPENCLAW_HOME, "plugin-skills"),
        os.path.join(OPENCLAW_HOME, "agents", "main", "agent",
                     "workshop-skills"),
    ]
    broken = []
    scanned = 0
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if "SKILL.md" not in files:
                continue
            path = os.path.join(dirpath, "SKILL.md")
            scanned += 1
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not m:
                broken.append((path, "no YAML frontmatter"))
                continue
            dm = re.search(r"^description:\s*(.+)$", m.group(1), re.MULTILINE)
            if not dm:
                broken.append((path, "no description field"))
            elif not dm.group(1).strip().strip("\"'"):
                broken.append((path, "empty description"))

    if not broken:
        return Check("skills", "Every skill is loadable", "PASS",
                     f"{scanned} SKILL.md files scanned, all have descriptions")
    ev = [f"{os.path.relpath(p, OPENCLAW_HOME)}: {why}" for p, why in broken]
    return Check("skills", "Every skill is loadable", "FAIL",
                 f"{len(broken)} skill(s) invisible to the model — "
                 f"missing or empty description", ev,
                 "add a `description:` line to the YAML frontmatter")


def check_skill_catalog():
    data, err = cli_json(["skills", "check", "--json"], timeout=90)
    if err:
        return Check("skill-catalog", "Skill catalogue is healthy", "WARN",
                     f"could not read catalogue: {err}")
    summary = data.get("summary", {})
    ev = [f"{k}={v}" for k, v in summary.items() if isinstance(v, int)]
    blocked = data.get("blocked", [])
    missing = data.get("missingRequirements", [])
    if blocked or missing:
        ev.append(f"blocked={blocked}")
        ev.append(f"missingRequirements={missing}")
        return Check("skill-catalog", "Skill catalogue is healthy", "WARN",
                     f"{len(blocked)} blocked, {len(missing)} missing "
                     f"requirements", ev)
    return Check("skill-catalog", "Skill catalogue is healthy", "PASS",
                 f"{summary.get('modelVisible', 0)} skills visible to the model",
                 ev)


def check_cron_contracts():
    data, err = cli_json(["cron", "list", "--json"])
    if err:
        return Check("cron-contracts", "Cron contracts hold", "FAIL",
                     f"could not list cron jobs: {err}")
    jobs = data.get("jobs", [])
    ev = []
    failures = []
    for frag, desc in CRON_MUST_BE_ENABLED:
        match = next((j for j in jobs if frag in j.get("name", "")), None)
        if match is None:
            failures.append(f"{desc}: job '{frag}' not found")
        elif not match.get("enabled"):
            failures.append(f"{desc}: job '{frag}' is disabled")
        else:
            ev.append(f"{match['name']}: enabled")

    # RULE 9: books are finished. Fail if a book delivery path reappears.
    book_jobs = [j.get("name") for j in jobs
                 if any(marker in (j.get("name") or "").lower()
                        for marker in BOOK_DELIVERY_MARKERS)]
    if book_jobs:
        failures.append(
            "RULE 9 (books are finished) — a book delivery cron exists "
            f"again: {book_jobs}. Amre set this rule permanently on "
            "2026-10-31; do not recreate book crons.")
    else:
        ev.append("RULE 9 intact — no book delivery cron exists")

    # RULE 9 also covers the launchd side and the workspace scripts.
    book_agents = []
    agents_dir = os.path.join(HOME, "Library", "LaunchAgents")
    try:
        for name in os.listdir(agents_dir):
            low = name.lower()
            if any(marker in low for marker in
                   ("kcread", "book", "kindle", "zlib")):
                book_agents.append(name)
    except OSError:
        pass
    if book_agents:
        failures.append(
            "RULE 9 (books are finished) — a book launchd agent exists "
            f"again: {book_agents}. Amre set this rule permanently on "
            "2026-10-31; do not recreate book agents.")

    book_scripts = []
    for rel in ("scripts/smtp_send.py", "scripts/batch_deliver.py",
                "scripts/send_cap.py", "scripts/rotation_guard.py"):
        if os.path.exists(os.path.join(WORKSPACE, rel)):
            book_scripts.append(rel)
    if os.path.isdir(os.path.join(WORKSPACE, "skills", "zlib-kindle")):
        book_scripts.append("skills/zlib-kindle")
    if book_scripts:
        failures.append(
            "RULE 9 (books are finished) — a book delivery script/skill is "
            f"back: {book_scripts}. Amre set this rule permanently on "
            "2026-10-31; do not recreate book scripts.")

    for j in jobs:
        state = j.get("state") or {}
        if state.get("consecutiveErrors", 0) >= 1:
            failures.append(f"job '{j.get('name')}' has "
                            f"{state.get('consecutiveErrors')} consecutive "
                            f"error(s): {str(state.get('lastErrorReason'))[:120]}")

    ev.append(f"{len(jobs)} jobs total")
    if failures:
        # The reasons MUST be in the evidence. A FAIL that says "1 cron
        # problem(s)" and shows only the passing checks is a finding
        # nobody can act on.
        return Check("cron-contracts", "Cron contracts hold", "FAIL",
                     f"{len(failures)} cron problem(s)",
                     ev + [f"PROBLEM: {f}" for f in failures])
    return Check("cron-contracts", "Cron contracts hold", "PASS",
                 f"{len(jobs)} jobs, contracts intact, none failing", ev)


def check_stale_cli():
    """
    Does a bare `openclaw` on PATH still work? The stale 2026.6.35 Homebrew
    build rejects the current config, which looks like "the cron produced no
    output" rather than a version problem.
    """
    import shutil
    path_bin = shutil.which("openclaw")
    ev = []
    if not path_bin:
        return Check("stale-cli", "PATH openclaw matches the gateway build",
                     "PASS", "no `openclaw` on PATH")
    rc, out, _ = run_cli(["--version"], timeout=30)
    gateway_ver = out.strip().splitlines()[-1] if rc == 0 and out.strip() else "?"
    try:
        proc = subprocess.run([path_bin, "--version"], capture_output=True,
                              text=True, timeout=30)
        path_ver = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "?"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return Check("stale-cli", "PATH openclaw matches the gateway build",
                     "WARN", f"could not run {path_bin}: {exc}")
    ev.append(f"PATH  : {path_bin} -> {path_ver}")
    ev.append(f"gateway: {gateway_ver}")
    if path_ver != gateway_ver:
        return Check("stale-cli", "PATH openclaw matches the gateway build",
                     "WARN",
                     f"the `openclaw` on PATH is a different build "
                     f"({path_ver}) than the gateway ({gateway_ver}); scripts "
                     f"that call it bare will hit the stale config-rejection "
                     f"path", ev,
                     "have scripts resolve $OPENCLAW_BIN / current-bin/openclaw")
    return Check("stale-cli", "PATH openclaw matches the gateway build",
                 "PASS", "PATH openclaw matches the gateway build", ev)


def check_session_store():
    ev = []
    data, err = cli_json(["sessions", "list", "--json", "--limit", "1"])
    count = None
    if err:
        ev.append(f"could not list sessions: {err}")
    else:
        count = data.get("totalCount")
        ev.append(f"{count} live session row(s)")
        ev.append(f"store: {data.get('path')}")
    size = None
    try:
        size = os.path.getsize(SESSION_STORE)
        ev.append(f"store size {human_size(size)}")
    except OSError:
        pass
    if count is None:
        return Check("sessions", "Session store is small", "WARN",
                     "could not read the session store", ev)
    if count > 200:
        return Check("sessions", "Session store is small", "WARN",
                     f"{count} live sessions is unusually many", ev)
    return Check("sessions", "Session store is small", "PASS",
                 f"{count} live session(s), {human_size(size)}", ev)


def check_dead_artifacts():
    """Report only. Deleting these needs a separate yes/no from Amre."""
    ev = []
    archive = dir_size(IMPORT_ARCHIVE)
    if archive:
        ev.append(f"import archive: {human_size(archive)} at {IMPORT_ARCHIVE}")
    try:
        ev.append(f"migration-stuck db: "
                  f"{human_size(os.path.getsize(MIGRATION_STUCK))}")
    except OSError:
        pass
    if not ev:
        return Check("artifacts", "No dead artifacts on disk", "PASS",
                     "no orphaned archives found")
    return Check("artifacts", "No dead artifacts on disk", "INFO",
                 f"{len(ev)} dead artifact(s) holding disk (harmless, disk is "
                 f"not under pressure)", ev,
                 "removal is irreversible and needs Amre's explicit yes")


def check_git_state():
    ev = []
    rc, out, err = git(["status", "--porcelain"])
    if rc != 0:
        return Check("git", "Git tree is clean and published", "WARN",
                     f"git status failed: {err[:150]}")
    dirty = [l for l in out.splitlines() if l.strip()]
    other = [l for l in dirty
             if "drosscash" not in l
             and not any(n in l for n in NOISE_PATTERNS)]
    noise = len(dirty) - len(other)
    for l in other:
        ev.append(l[:100])
    if not other:
        ev.append("(only the deliberately-uncommitted drosscash submodule "
                  "and/or build artifacts)")
    if noise:
        ev.append(f"({noise} build-artifact path(s) ignored)")
    rc, ahead, _ = git(["rev-list", "--count", "origin/main..main"])
    if rc == 0 and ahead.isdigit():
        ev.append(f"{ahead} commit(s) ahead of origin/main")
    if other:
        return Check("git", "Git tree is clean and published", "WARN",
                     f"{len(other)} uncommitted path(s) outside drosscash", ev)
    return Check("git", "Git tree is clean and published", "PASS",
                 "working tree clean (drosscash and build artifacts "
                 "excluded by policy)", ev)


# --------------------------------------------------------------------------
# State handling (baseline + alert dedupe)
# --------------------------------------------------------------------------

def load_state():
    try:
        with open(BASELINE_PATH) as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = BASELINE_PATH + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
    os.replace(tmp, BASELINE_PATH)


def append_history(entry):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(HISTORY_PATH, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def check_cache_ttl_patch():
    """The runtime patch must be present AND behave, in EVERY copy of the gate.

    Why this check exists, and why a string check was not enough:

    `isCacheTtlEligibleProvider` is not defined once. It is inlined into
    three separately-bundled files in the runtime dist:

        dist/builtin-openclaw-<hash>.mjs       (the main bundle)
        dist/worker/worker.mjs                 (the worker bundle)
        dist/worker/sqlite-store.worker.mjs    (the sqlite worker bundle)

    The agent turns actually run in the WORKER. On 2026-10-28 the patch was
    applied to the main bundle only, and the markers duly stopped — for that
    bundle. Six days later the cron session was carrying 22 markers = 607 KB
    of a 910 KB window (67% pure bookkeeping), because the worker's own copy
    of the function was still unpatched and still making the decision.

    And then a second failure: the guard matched only the BARE provider id
    ("minimax") while the call site passes a QUALIFIED reference
    ("minimax/MiniMax-M2.7"). The guard was present in all three copies,
    passed every string check, and still never fired. The only way to catch
    that is to extract the function and CALL it.

    So this check delegates to scripts/apply-openclaw-patches.sh --verify-only,
    which syntax-checks every copy and exercises the guard against every
    shape of reference the runtime can pass.
    """
    script = os.path.join(WORKSPACE, "scripts", "apply-openclaw-patches.sh")
    if not os.path.exists(script):
        return Check("cache-ttl-patch", "The cache-TTL gate is patched everywhere",
                     "INFO", "apply-openclaw-patches.sh is missing — check not run")
    try:
        proc = subprocess.run(["/bin/bash", script, "--verify-only"],
                              capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return Check("cache-ttl-patch", "The cache-TTL gate is patched everywhere",
                     "INFO", f"could not run the verifier: {exc}")
    out = (proc.stdout or "") + (proc.stderr or "")
    evidence = [ln.strip() for ln in out.splitlines()
                if ln.strip().startswith("ok ") or ln.strip().startswith("FAIL")]
    if proc.returncode != 0:
        return Check(
            "cache-ttl-patch", "The cache-TTL gate is patched everywhere",
            "FAIL",
            "a runtime copy of the cache-TTL gate would still write bookkeeping",
            evidence[-12:],
            fix="Run `bash scripts/apply-openclaw-patches.sh` — it discovers "
                "every copy of isCacheTtlEligibleProvider, widens an "
                "existing too-narrow guard in place, and verifies the guard "
                "BEHAVIOUR (not just its presence) — then restart the gateway "
                "with `launchctl kickstart -k gui/501/ai.openclaw.gateway`.")

    copies = 0
    for line in out.splitlines():
        if "behaviour verified:" in line:
            copies += 1
    return Check(
        "cache-ttl-patch", "The cache-TTL gate is patched everywhere",
        "PASS",
        f"all {copies} runtime copies of the gate exclude minimax, "
        "verified by calling the guard",
        evidence[-14:])


def check_sleep_guard():
    """The Mac must not be able to idle-sleep, and the bot must survive it.

    On 2026-10-31 the `pmset -a disablesleep 1` hardening was LOST (a
    settings write, an update or a restore can drop it) and the Mac took
    an idle sleep at 21:27 on AC power. It stayed asleep for 2.7 days. The
    Telegram bot was simply unreachable for that whole time; nothing was
    broken, the machine was off.

    `pmset -g custom` still shows `sleep 1` in that state — the raw timer
    is NOT the thing to look at. The override is the system-wide
    `SleepDisabled` key, and `pmset -g` prints it. A live
    `PreventUserIdleSystemSleep` assertion (the gateway's `caffeinate
    -dims` wrapper) is a second, independent line of defence.

    `womp 1` matters for the same reason: it lets the machine wake for
    network traffic after a sleep.
    """
    try:
        proc = subprocess.run(["pmset", "-g"], capture_output=True, text=True,
                              timeout=20)
        text = proc.stdout or ""
    except (OSError, subprocess.TimeoutExpired):          # pragma: no cover
        return Check("sleep-guard", "The Mac cannot idle-sleep",
                     "WARN", "could not run pmset")
    problems = []
    evidence = []
    if re.search(r"^\s*SleepDisabled\s+1\s*$", text, re.M):
        evidence.append("SleepDisabled 1 (system-wide idle sleep is off)")
    else:
        problems.append("SleepDisabled is not 1 — the Mac can idle-sleep")
        evidence.append("SleepDisabled NOT set in `pmset -g`")
    if re.search(r"^\s*womp\s+1\s*$", text, re.M):
        evidence.append("womp 1 (the Mac wakes for network traffic)")
    else:
        problems.append("womp is not 1 — the Mac will not wake for the network")
    asserted = "sleep prevented" in text
    if asserted:
        evidence.append("a live assertion is already preventing sleep")
    if problems:
        return Check(
            "sleep-guard", "The Mac cannot idle-sleep", "FAIL",
            "; ".join(problems), evidence,
            "osascript -e 'do shell script \"pmset -a disablesleep 1 && "
            "pmset -a womp 1\" with administrator privileges'")
    return Check("sleep-guard", "The Mac cannot idle-sleep", "PASS",
                 "idle sleep is disabled and the Mac wakes for the network",
                 evidence)


def check_prompt_budget(events, window_hours):
    """The prompt must fit the context budget with room to spare.

    Measured on 2026-11-03: the Telegram session's prompt sat at
    184.8k-186.4k tokens against a 184.8k budget — over budget on every
    attempt. The mid-turn precheck caught it (route=compact_only), but the
    auto-compaction it triggers cannot help: the bulk of the prompt is the
    system prompt plus the inlined tool catalog, and
    `toolResultReducibleChars=0` means there is nothing left for compaction
    to trim. The session overflowed 16 times in two hours, each time
    "recovered" by a compaction that changed nothing, and the user saw
    "OpenClaw couldn't produce or deliver a reply".

    Two things are checked here:

      1. the live signal — the worst prompt seen in the window against the
         budget the runtime was working to;
      2. `tools.toolSearch` explicitly false. That setting DISABLES
         OpenClaw's tool-catalog compaction (the feature is on by default
         when the key is unset), which is what put ~168k tokens of tool
         schemas into a prompt whose conversation slice was only ~17k.
    """
    prechecks = [e for e in events if e["kind"] == "precheck"]
    problems = []
    evidence = []
    worst = None
    latest = None

    for e in prechecks:
        tok = field(e["text"], "estimatedPromptTokens", int)
        bud = field(e["text"], "promptBudgetBeforeReserve", int)
        if tok is None or bud is None:
            continue
        if worst is None or tok > worst[0]:
            worst = (tok, bud, e)
        if latest is None or e["at"] >= latest[2]["at"]:
            latest = (tok, bud, e)

    overflows = 0
    for e in events:
        if e["kind"] != "overflow":
            continue
        tok = field(e["text"], "preflightEstimatedTokens", int)
        bud = field(e["text"], "promptBudgetBeforeReserve", int)
        if tok is None or bud is None:
            continue
        if tok >= bud:
            overflows += 1

    if latest is None:
        evidence.append("no prompt measurement in the window")
    else:
        # The LIVE signal is the most recent measurement. The worst one in
        # the window is kept as evidence, because a doctor that only reads
        # the newest number hides a regression that was just fixed, and a
        # doctor that only reads the worst number stays red for hours
        # after the fix.
        tok, bud, e = latest
        pct = (tok / bud * 100) if bud else 0

        # The precheck only fires when the runtime PREDICTS pressure, so
        # after the catalogue compaction is applied the precheck simply
        # stops firing — silence, not a measurement. When the last
        # measurement predates the hot reload, judge on overflows since
        # the reload instead of on a number we already know is stale.
        reloads = [x for x in events if x["kind"] == "toolsearch"]
        reload_at = reloads[-1]["at"] if reloads else None
        if reload_at is not None and latest[2]["at"] < reload_at:
            since = [x for x in events
                     if x["kind"] == "overflow" and x["at"] >= reload_at]
            catalogued = len(reloads)
            evidence.append(
                f"compact tool surface active ({catalogued} cataloguing "
                f"event(s)); the last precheck predates it")
            evidence.append(
                f"overflows since the hot reload: {len(since)}")
            if since:
                problems.append(
                    f"{len(since)} overflow(s) since the tool-catalogue "
                    "compaction was applied")
            else:
                problems = []   # the stale number is not a live failure
        else:
            evidence.append(
                f"latest prompt {tok:,} tokens vs budget {bud:,} "
                f"({pct:.1f}%)")
            if tok >= bud:
                problems.append(
                    f"prompt reached {tok:,} tokens against a {bud:,} budget")
            elif pct >= 90:
                problems.append(
                    f"prompt reached {pct:.1f}% of the {bud:,}-token budget")

        if worst is not None and worst[0] > tok:
            w = (worst[0] / worst[1] * 100) if worst[1] else 0
            evidence.append(
                f"worst in window {worst[0]:,} ({w:.1f}%)")
        if overflows and not (reload_at is not None
                              and latest[2]["at"] < reload_at):
            problems.append(f"{overflows} over-budget prompt(s) in the window")
            evidence.append(f"over-budget prompts: {overflows}")

    # The config cause: an explicit false switches the catalogue compaction
    # off. Left unset, OpenClaw turns it on by itself.
    tool_search = None
    try:
        with open(CONFIG_PATH) as fh:
            tool_search = (json.load(fh).get("tools") or {}).get("toolSearch")
    except (OSError, json.JSONDecodeError, AttributeError):
        tool_search = None

    if tool_search is False:
        problems.append(
            "tools.toolSearch is false — that DISABLES tool-catalog "
            "compaction (it is on by default when unset) and inlines every "
            "MCP tool schema into the prompt")
        evidence.append("tools.toolSearch = false")
        fix = ("openclaw config set tools.toolSearch "
               "'{\"enabled\":true,\"mode\":\"tools\"}'")
    elif isinstance(tool_search, dict):
        evidence.append(
            f"tools.toolSearch = {json.dumps(tool_search)}")
        fix = None
    else:
        evidence.append("tools.toolSearch is unset (catalogue compaction on)")
        fix = None

    if problems:
        status = "FAIL" if any("DISABLES" in p or "against a" in p
                               for p in problems) else "WARN"
        return Check("prompt-budget", "The prompt fits the context budget",
                     status, "; ".join(problems), evidence, fix)
    return Check("prompt-budget", "The prompt fits the context budget",
                 "PASS", "prompt is inside the context budget", evidence)


def check_cache_ttl_markers(window_hours):
    """The `openclaw.cache-ttl` marker is pure bookkeeping, but it is O(n^2).

    Each attempt appends a marker that re-lists every frozen tool result, so a
    session with N attempts and T tool results carries roughly N*T bytes of
    marker overhead. Measured on 2026-10-28 with MiniMax M2.7: 30 markers =
    961 KB of a 1.34 MB session window (72% of the transcript), and the
    session overflowed its context budget because of it.

    OpenClaw treats any provider speaking the Anthropic Messages API as
    cache-TTL eligible, so `agents.defaults.contextPruning.mode = "off"` does
    NOT stop the markers. The runtime bundle carries a local patch that
    excludes those providers (see scripts/apply-openclaw-patches.sh). This
    check is the tripwire for an OpenClaw upgrade that silently reverts it.
    """
    audit = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cache-ttl-audit.py")
    if not os.path.exists(audit):
        return Check("cache-ttl", "Cache-TTL markers are absent",
                     "INFO", "cache-ttl-audit.py is missing — check not run")
    minutes = int(os.environ.get("CLAW_DOCTOR_CACHE_TTL_WINDOW_MIN", "30"))
    try:
        proc = subprocess.run(
            ["/opt/homebrew/bin/python3", audit, "--minutes", str(minutes),
             "--json"],
            capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        return Check("cache-ttl", "Cache-TTL markers are absent",
                     "INFO", f"audit could not run: {exc}")
    try:
        report = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return Check("cache-ttl", "Cache-TTL markers are absent",
                     "INFO", "audit produced no parsable output")
    sessions = report.get("sessions") or []
    if not sessions:
        return Check("cache-ttl", "Cache-TTL markers are absent",
                     "PASS",
                     f"no openclaw.cache-ttl markers in the last {minutes} min "
                     "- the transcript carries no provider bookkeeping")
    # A marker is only worth reporting when it is actually costing the
    # context window. The pathological case (2026-10-28) was 26 KB per
    # marker, 72-83% of the window. After the compaction and thinking fixes a
    # residual single marker is a few hundred bytes, which is noise.
    total_marker_bytes = sum(s["marker_bytes"] for s in sessions)
    worst = max(sessions, key=lambda s: s["marker_bytes"])
    share = (worst["marker_bytes"] / worst["session_bytes"] * 100) if worst.get("session_bytes") else 0
    if total_marker_bytes < 50_000 and share < 10:
        return Check("cache-ttl", "Cache-TTL markers are absent",
                     "PASS",
                     f"{sum(s['markers'] for s in sessions)} marker(s) totalling "
                     f"{total_marker_bytes // 1024} KB across "
                     f"{len(sessions)} session(s) - below the reporting "
                     "threshold, the window is not paying for it")
    return Check(
        "cache-ttl", "Cache-TTL markers are absent", "WARN",
        f"{sum(s['markers'] for s in sessions)} openclaw.cache-ttl marker(s) "
        f"in the last {minutes} min - {total_marker_bytes // 1024} KB of "
        f"pure bookkeeping, {share:.0f}% of the worst session window",
        evidence=[f"{s['session_key'] or s['session_id'][:12]}: {s['markers']} marker(s), "
                  f"{s['marker_bytes'] // 1024} KB" for s in sessions[:4]],
        fix="An OpenClaw upgrade reverted the runtime patch that excludes "
            "Anthropic-compatible providers from the cache-TTL path. Run "
            "`bash scripts/apply-openclaw-patches.sh` and then "
            "`launchctl kickstart -k gui/501/ai.openclaw.gateway`. "
            "`agents.defaults.contextPruning.mode = \"off\"` does NOT fix this "
            "on its own - the agent runtime re-applies `cache-ttl` in its own "
            "config scope.")


# --------------------------------------------------------------------------
# Live-turn safety. Both of these invariants were violated on 2026-10-28 and
# both produced the same user-visible symptom: "OpenClaw couldn't produce or
# deliver a reply".
# --------------------------------------------------------------------------

GUARD_LIB_REL = os.path.join("scripts", "lib", "gateway-restart-guard.sh")
RESTART_PATTERNS = ("launchctl kickstart", "launchctl bootout")
# Room reserved for the model's own output when sizing a fallback's context.
FALLBACK_OUTPUT_RESERVE = 20000


def _shell_scripts():
    out = []
    root = os.path.join(WORKSPACE, "scripts")
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".sh"):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def _executes_restart(path):
    """True if the file actually RUNS a gateway restart, not merely mentions it."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if not any(p in s for p in RESTART_PATTERNS):
                    continue
                # A line that only *reports* a restart is not a restart.
                if s.startswith(("log ", "echo ", "log(", "echo(")):
                    continue
                return True
    except OSError:
        pass
    return False


def check_live_turn_safety():
    """Nothing may abort a live run, and every restart must be turn-aware.

    Why this is a check and not a comment:

    * On 2026-10-28 the watchdog aborted the very run it was supposed to
      heal. A context-overflow death line and a live run are usually the
      SAME event: the gateway's own auto-compaction recovers an overflowed
      turn in place. The watchdog killed run e66ea972 25 seconds before the
      reply went out (13:22:19) and produced the exact error it existed to
      prevent.
    * The gateway's shutdown drain is 5 seconds and a turn takes minutes, so
      ANY restart during a turn kills the reply. Three scripts could restart
      the gateway. They now share scripts/lib/gateway-restart-guard.sh,
      which defers while a turn is live and fails CLOSED when the state is
      unknown.

    This is a static invariant: it reads the scripts, so it catches the
    regression the moment someone edits one, rather than after a user's
    message has died.
    """
    guard_path = os.path.join(WORKSPACE, GUARD_LIB_REL)
    problems = []
    evidence = []

    if not os.path.exists(guard_path):
        problems.append(
            f"the shared restart guard is missing: {GUARD_LIB_REL}")
    else:
        evidence.append("shared restart guard present")

    for path in _shell_scripts():
        rel = os.path.relpath(path, WORKSPACE)
        if os.path.abspath(path) == os.path.abspath(guard_path):
            continue    # the guard IS the mechanism

        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue

        # A live run must never be aborted. Not by session key, not by runId.
        if "sessions.abort" in body:
            problems.append(f"{rel} calls sessions.abort")

        # A restart must be behind the guard.
        if _executes_restart(path) and GUARD_LIB_REL not in body \
                and "safe_restart_gateway" not in body \
                and "restart_allowed" not in body:
            problems.append(f"{rel} restarts the gateway without the turn guard")

    if problems:
        return Check(
            "live-turn-safety",
            "Live turns are protected from aborts and restarts",
            "FAIL",
            f"{len(problems)} script problem(s) — a live Telegram turn can be killed",
            evidence + problems,
            fix="Remove sessions.abort from the script, and route every gateway "
                "restart through scripts/lib/gateway-restart-guard.sh "
                "(safe_restart_gateway / restart_allowed), which defers while a "
                "turn is live and fails closed when the state is unknown.")

    scripts = _shell_scripts()
    return Check(
        "live-turn-safety",
        "Live turns are protected from aborts and restarts",
        "PASS",
        f"no script aborts a run; every gateway restart is turn-aware",
        evidence + [f"{len(scripts)} shell script(s) scanned"])


def _ollama_real_context(model_id, configured_num_ctx=None):
    """What the running ollama server can ACTUALLY serve for this model.

    Returns (real_context, note). `real_context` is None when it cannot be
    determined (server down, model unknown).

    The subtlety this handles: the GGUF's `context_length` is NOT what
    ollama serves. The served context is `min(num_ctx, native)`.

      * `num_ctx` comes from the request (`params.num_ctx` in the config).
        A num_ctx LARGER than the native length is CLAMPED - ollama accepts
        it without complaint and silently serves less.
      * `num_ctx` SMALLER than the native length SHRINKS the context. On
        2026-11-03 a `params.num_ctx: 131072` was added to both ollama
        models: it shrank qwen3:30b from its native 262144 down to 131072
        while the config still declared 262144, and it asked for 131072 on
        qwen3:14b whose native is 40960.

    Both were over-declarations - exactly the 2026-10-28 failure mode -
    and reading only the GGUF metadata hides both of them.

    The most authoritative source is `/api/ps`, which reports the context
    the RUNNER actually allocated. It is only available for a model that is
    currently loaded, so it is used when present and the computed value is
    the fallback.
    """
    import urllib.request

    # The runner's own report, when the model happens to be loaded.
    try:
        with urllib.request.urlopen("http://localhost:11434/api/ps",
                                    timeout=10) as resp:
            ps = json.loads(resp.read().decode("utf-8", "replace"))
        # EXACT name match only. Matching on the base name ("qwen3") is a
        # trap: qwen3:30b and qwen3:14b share a base name but not a
        # context length, and a loose match reports one model's runner
        # context as the other's.
        for m in ps.get("models", []):
            name = str(m.get("name", ""))
            if name == model_id or name == f"{model_id}:latest":
                ctx = m.get("context_length")
                if ctx:
                    return int(ctx), "reported by the loaded runner"
    except Exception:                                     # noqa: BLE001
        pass

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/show",
            data=json.dumps({"model": model_id}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:                              # noqa: BLE001
        return None, f"could not ask ollama about {model_id} ({exc})"
    info = data.get("model_info") or {}
    lens = [v for k, v in info.items() if k.endswith(".context_length")]
    if not lens:
        return None, f"ollama did not report a context length for {model_id}"
    native = max(lens)
    if configured_num_ctx:
        effective = min(native, int(configured_num_ctx))
        if effective != native:
            return effective, (f"num_ctx={configured_num_ctx} shrinks the "
                               f"native {native}")
        return native, "native"
    return native, "native"


def check_fallback_capacity():
    """Can the fallback CHAIN hold the prompts this agent actually sends?

    The primary provider can be rate-limited out at any time. On 2026-10-28
    MiniMax returned HTTP 429 "Token Plan usage limit reached" on every call
    and every turn fell through to the local model. A fallback whose context
    window is smaller than the prompt cannot answer: the router admits the
    attempt as `route=compact_only` and the turn stalls with
    "repeated_model_requests_without_progress" until it dies.

    Measured that day: estimatedPromptTokens=113455 against
    promptBudgetBeforeReserve=111072 on a fallback declared at 131072. The
    fallback was 2,383 tokens too small and the turn never produced a reply.

    TWO separate failure modes, and they need different verdicts.

      1. THE CHAIN IS TOO SMALL. Not one fallback can hold the prompt, so
         when the primary drops there is nowhere to go. That is a FAIL.

      2. A FALLBACK OVER-DECLARES ITS WINDOW. The config says 131072 but
         the provider can only serve 90000. The runtime believes it has
         room, sends a prompt the provider cannot take, and the turn dies
         with an opaque error. THAT is the 2026-10-28 bug, and it is a FAIL
         even when another fallback in the chain is big enough, because the
         over-declaring one is still in the failover order.

    A secondary fallback that is merely SMALLER than the largest prompt is a
    WARN, not a FAIL: it is only reached when the earlier fallbacks have
    already failed, and by then the big one was tried first.
    """
    try:
        with open(CONFIG_PATH) as fh:
            cfg = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return Check("fallback-capacity", "Fallbacks can hold the prompts they see",
                     "INFO", f"could not read {CONFIG_PATH}: {exc}")

    defaults = cfg.get("agents", {}).get("defaults", {})
    fallbacks = defaults.get("model", {}).get("fallbacks") or []
    if not fallbacks:
        return Check("fallback-capacity", "Fallbacks can hold the prompts they see",
                     "INFO", "no fallback models are configured")

    providers = cfg.get("models", {}).get("providers", {})

    # Largest prompt the runtime has actually tried to send. Two markers
    # carry the estimate: the mid-turn precheck (the common one) and the
    # older context-pressure diagnostic.
    max_est = 0
    max_est_at = None
    for path in sorted(glob.glob(LOG_GLOB)):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if ("context-pressure-diagnostic" not in line and
                            "context-overflow-midturn-precheck" not in line):
                        continue
                    m = re.search(r"estimatedPromptTokens=(\d+)", line)
                    if not m:
                        continue
                    val = int(m.group(1))
                    if val > max_est:
                        max_est = val
                        max_est_at = parse_ts(
                            (json.loads(line) or {}).get("time")) if line.strip().startswith("{") else None
        except (OSError, json.JSONDecodeError):
            continue

    windows = {}
    for pname, pcfg in providers.items():
        for mdl in (pcfg.get("models") or []):
            if isinstance(mdl, dict) and mdl.get("id"):
                windows[f"{pname}/{mdl['id']}"] = mdl.get("contextWindow") or 0

    need = max_est + FALLBACK_OUTPUT_RESERVE if max_est else 0
    problems = []          # FAIL-level
    warnings = []          # WARN-level
    evidence = []
    if max_est:
        when = max_est_at.isoformat(timespec="seconds") if max_est_at else "?"
        evidence.append(f"largest prompt the runtime tried to send: {max_est} "
                        f"tokens ({when}); a fallback needs >= {need}")

    capable = 0
    for fb in fallbacks:
        ctx = windows.get(fb)
        if ctx is None:
            problems.append(f"{fb} is configured as a fallback but is not in any provider")
            continue
        line = f"{fb}: contextWindow={ctx}"
        if need:
            line += f" (needs >= {need})"
        # Honesty: does the provider actually serve this much?
        if fb.startswith("ollama/"):
            num_ctx = None
            for mdl in (providers.get("ollama", {}).get("models") or []):
                if isinstance(mdl, dict) and mdl.get("id") == fb.split("/", 1)[1]:
                    num_ctx = (mdl.get("params") or {}).get("num_ctx")
            real, note = _ollama_real_context(fb.split("/", 1)[1], num_ctx)
            if real is None:
                warnings.append(f"{fb}: could not confirm the real context "
                                f"window - {note}")
            elif ctx > real:
                problems.append(
                    f"{fb} DECLARES contextWindow={ctx} but ollama can only "
                    f"serve {real} - the runtime will send a prompt the "
                    f"provider cannot take")
            else:
                line += f"; ollama actually serves {real} ({note})"
        evidence.append(line)

        if need and ctx < need:
            warnings.append(f"{fb} contextWindow={ctx} is smaller than the "
                            f"{need} tokens a prompt of {max_est} needs")
        else:
            capable += 1

    if problems:
        return Check(
            "fallback-capacity", "Fallbacks can hold the prompts they see",
            "FAIL",
            f"{len(problems)} fallback problem(s) that no other fallback can "
            "compensate for",
            evidence + problems,
            fix="Correct the declared contextWindow to what the provider "
                "really serves, and make sure at least one fallback can hold "
                "max_observed_prompt_tokens + 20000. A fallback that "
                "over-declares its window is worse than no fallback: the turn "
                "stalls instead of failing fast.")

    if warnings and capable == 0:
        return Check(
            "fallback-capacity", "Fallbacks can hold the prompts they see",
            "FAIL",
            "NO fallback can hold the prompts this agent produces",
            evidence + warnings,
            fix="Raise a fallback's contextWindow to at least "
                "max_observed_prompt_tokens + 20000. A fallback that cannot "
                "hold the prompt is worse than no fallback: the turn stalls "
                "instead of failing fast.")

    if warnings:
        return Check(
            "fallback-capacity", "Fallbacks can hold the prompts they see",
            "WARN",
            f"{capable} of {len(fallbacks)} fallback(s) can hold the largest "
            f"observed prompt; the rest are smaller (they are only reached "
            "after the bigger ones fail)",
            evidence + warnings,
            fix="Optional: raise the smaller fallbacks' contextWindow, or "
                "remove them from the chain if they cannot serve the prompts "
                "this agent produces.")

    return Check(
        "fallback-capacity", "Fallbacks can hold the prompts they see",
        "PASS",
        f"{len(fallbacks)} fallback(s) can hold the prompts this agent produces",
        evidence)


def _log_lines(window_hours):
    """Yield (datetime, text) for every JSON-log line in the window.

    Deliberately NOT filtered by MARKERS: the provider-failure lines this
    reads ("status=429", "Token Plan usage limit reached") are not markers
    the event classifier knows about, and the whole point of these checks is
    to notice the lines nobody else is watching.
    """
    cutoff = now_utc() - timedelta(hours=window_hours)
    for path in sorted(glob.glob(LOG_GLOB)):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if not line.startswith("{"):
                        continue
                    try:
                        rec = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    text = rec.get("message") or rec.get("1") or ""
                    if not text:
                        continue
                    ts = parse_ts(rec.get("time"))
                    if ts and ts < cutoff:
                        continue
                    yield ts, text
        except OSError:
            continue


def check_provider_health(window_hours):
    """Is the PRIMARY provider actually serving right now?

    Measured on 2026-11-03: MiniMax began returning HTTP 429 with
    "Token Plan usage limit reached ... (2056)" at 18:02 and again at 18:18.
    The turn did not fail cleanly. The auth profile was marked
    "temporarily unavailable", the session stayed in `processing` forever,
    compaction was refused ("Session has an active run"), and the user got
    nothing for 14 minutes. The bot then degraded to a local model without
    saying so.

    The dangerous state is not the 429 itself — it is the 429 being INVISIBLE.
    Nothing in the Doctor reported it, so the only symptom the user saw was
    "the bot stopped answering". This check reads the primary provider's
    outcome in the window and says plainly whether it is serving, degraded,
    or down.

    PASS  - the primary served a request in the window, or has never failed.
    WARN  - the primary failed and a fallback is carrying the traffic.
    FAIL  - the primary failed and there is NO fallback to carry it.
    """
    try:
        with open(CONFIG_PATH) as fh:
            cfg = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return Check("provider-health", "The primary provider is serving",
                     "INFO", f"could not read {CONFIG_PATH}: {exc}")

    model = cfg.get("agents", {}).get("defaults", {}).get("model", {}) or {}
    primary = model.get("primary") or ""
    fallbacks = model.get("fallbacks") or []
    if not primary:
        return Check("provider-health", "The primary provider is serving",
                     "INFO", "no primary model is configured")
    primary_provider = primary.split("/")[0]

    failures = []          # (ts, text)
    successes = []         # (ts, text) for the PRIMARY provider
    fallback_used = 0

    fetch_fail = re.compile(
        r"\[model-fetch\]\s+response\s+provider=(\S+).*?model=(\S+)\s+status=(\d+)")
    for ts, text in _log_lines(window_hours):
        m = fetch_fail.search(text)
        if m:
            prov, _mid, status = m.group(1), m.group(2), int(m.group(3))
            if prov == primary_provider:
                if status >= 400:
                    failures.append((ts, text))
                elif status < 400:
                    successes.append((ts, text))
            continue
        if "Token Plan usage limit reached" in text or \
                "temporarily unavailable for" in text:
            if primary_provider in text:
                failures.append((ts, text))
        # A model-snapshot records which model actually served a turn.
        if "model-snapshot" in text:
            snap = re.search(r'"provider":"([^"]+)".*?"modelId":"([^"]+)"', text)
            if snap and snap.group(1) != primary_provider:
                fallback_used += 1

    if not failures:
        served = f"the primary served {len(successes)} request(s)" if successes \
            else "no failure recorded in the window"
        return Check("provider-health", "The primary provider is serving",
                     "PASS", f"{primary}: {served}", [])

    newest_fail = max((t for t, _ in failures if t), default=None)
    recovered = any(t and newest_fail and t > newest_fail for t, _ in successes)
    if recovered:
        return Check(
            "provider-health", "The primary provider is serving",
            "PASS",
            f"{primary}: {len(failures)} failure(s), but a later request "
            "succeeded — it recovered on its own",
            [f"newest failure {newest_fail.isoformat()}" if newest_fail else ""])

    ev = []
    for ts, text in failures[-6:]:
        when = ts.isoformat(timespec="seconds") if ts else "?"
        ev.append(f"{when} {clip_text(text, 160)}")
    if fallback_used:
        ev.append(f"{fallback_used} turn(s) were served by a fallback model")

    if not fallbacks:
        return Check(
            "provider-health", "The primary provider is serving",
            "FAIL",
            f"{primary} is failing and there is NO fallback configured — "
            "every turn will fail",
            ev,
            fix="Configure at least one fallback "
                "(agents.defaults.model.fallbacks) so a provider outage "
                "degrades instead of failing outright.")

    return Check(
        "provider-health", "The primary provider is serving",
        "WARN",
        f"{primary} is failing ({len(failures)} failure(s) in the window) — "
        f"traffic is being served by the fallback chain: {', '.join(fallbacks)}",
        ev,
        fix="This is an ACCOUNT problem, not a code problem: the provider is "
            "refusing calls (quota/limit/billing). Top up or fix the "
            "credential on the provider side; the fallback chain is already "
            "covering it, but the fallback is a local model and will be "
            "slower and less capable.")


def check_fallback_models():
    """Is every configured fallback actually PRESENT and REACHABLE?

    A fallback that names a model which is not installed is a silent trap:
    the chain looks configured, the Doctor passes, and the turn fails with
    an opaque provider error the first time it is needed.

    For ollama this is checked against the running server's own model list,
    because "installed" and "listed" are not the same thing on a machine
    where models get pruned.
    """
    try:
        with open(CONFIG_PATH) as fh:
            cfg = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return Check("fallback-models", "Fallback models are installed",
                     "INFO", f"could not read {CONFIG_PATH}: {exc}")

    defaults = cfg.get("agents", {}).get("defaults", {})
    fallbacks = defaults.get("model", {}).get("fallbacks") or []
    if not fallbacks:
        return Check("fallback-models", "Fallback models are installed",
                     "INFO", "no fallback models are configured")

    providers = cfg.get("models", {}).get("providers", {})
    problems = []
    evidence = []

    ollama_models = None
    ollama_up = None
    for fb in fallbacks:
        prov, _sep, model_id = fb.partition("/")
        if prov != "ollama":
            pcfg = providers.get(prov) or {}
            if not pcfg.get("baseUrl"):
                problems.append(f"{fb}: provider '{prov}' is not configured "
                                "(no baseUrl in models.providers)")
            else:
                evidence.append(f"{fb}: provider configured")
            continue

        if ollama_up is None:
            try:
                import urllib.request
                with urllib.request.urlopen("http://localhost:11434/api/tags",
                                            timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8", "replace"))
                ollama_models = {m.get("name", "") for m in data.get("models", [])}
                ollama_up = True
                evidence.append(f"ollama server is up with "
                                f"{len(ollama_models)} model(s) installed")
            except Exception as exc:                      # noqa: BLE001
                ollama_up = False
                ollama_models = set()
                problems.append(f"ollama server is not reachable at "
                                f"localhost:11434 ({exc}) — every ollama "
                                "fallback is dead")
        if not ollama_up:
            continue
        names = {n for n in ollama_models}
        wanted = model_id
        if wanted not in names and f"{wanted}:latest" not in names:
            # ollama reports 'qwen3:30b' for a model installed as 'qwen3:30b',
            # but a bare tag shows up as 'name:latest'.
            bare = wanted.split(":")[0]
            if not any(n == wanted or n.split(":")[0] == bare and ":" in n
                       for n in names):
                problems.append(
                    f"{fb}: not installed on the ollama server "
                    f"(have: {', '.join(sorted(names))[:120]})")
            else:
                evidence.append(f"{fb}: installed")
        else:
            evidence.append(f"{fb}: installed")

    if problems:
        return Check(
            "fallback-models", "Fallback models are installed",
            "FAIL",
            f"{len(problems)} configured fallback(s) cannot be used",
            evidence + problems,
            fix="Install the missing model or remove it from the fallback "
                "chain. A fallback naming an absent model fails opaquely at "
                "the moment it is needed.")

    return Check(
        "fallback-models", "Fallback models are installed",
        "PASS",
        f"{len(fallbacks)} fallback(s) are reachable and installed",
        evidence)


def check_session_wedge(window_hours):
    """Is any session stuck in `processing` with no progress?

    The failure mode of 2026-11-03: the provider refused the call, the lane
    task errored, the error message went out to Telegram — and then the
    session stayed `state=processing` forever. The gateway's own watchdog
    noticed (`stalled session: ... classification=stalled_agent_run
    recovery=none`) but nothing released it. While it was wedged:

      * compaction was refused ("Session has an active run"), so the window
        could not shrink;
      * new turns queued behind a lane that would never drain;
      * the restart guard saw a live-ish session and deferred.

    The user saw a bot that had stopped answering. This check makes the
    wedge visible instead of leaving it to be discovered by a user.
    """
    cutoff = now_utc() - timedelta(hours=window_hours)
    stalled = []
    for ts, text in _log_lines(window_hours):
        if "stalled session:" not in text:
            continue
        if ts and ts < cutoff:
            continue
        key = field(text, "sessionKey")
        age = field(text, "age", lambda v: int(float(v.rstrip("s"))))
        cls = field(text, "classification")
        rec = field(text, "recovery")
        stalled.append((ts, key, age, cls, rec, text))

    if not stalled:
        return Check("session-wedge", "No session is wedged in processing",
                     "PASS", "no stalled session reported in the window")

    newest = max(stalled, key=lambda r: r[0] or datetime.min.replace(
        tzinfo=timezone.utc))
    ts, key, age, cls, rec, _text = newest
    when = ts.isoformat(timespec="seconds") if ts else "?"
    # A stall that was later resolved is history, not a fault. Look for
    # progress on that session AFTER the stall report: a compaction, a
    # reply going out, or a gateway restart all release a wedge.
    last_progress = None
    for pts, ptext in _log_lines(window_hours):
        if pts is None or ts is None or pts <= ts:
            continue
        if key and key not in ptext:
            continue
        if ("Compacted session" in ptext or "telegram outbound send ok" in ptext
                or "No compaction needed for session" in ptext
                or "lane task error" in ptext or "model-snapshot" in ptext):
            last_progress = pts
            break
    still_stuck = age is not None and age >= 180 and last_progress is None
    evidence = [f"{when} age={age}s classification={cls} recovery={rec} "
                f"session={key}"]
    for _t, k, a, c, r, _x in stalled[-5:]:
        if k != key:
            evidence.append(f"session={k} age={a}s classification={c}")

    if not still_stuck:
        extra = ""
        if last_progress is not None:
            extra = (f" (released by progress at "
                     f"{last_progress.isoformat(timespec='seconds')})")
        return Check(
            "session-wedge", "No session is wedged in processing",
            "PASS",
            f"{len(stalled)} stall report(s) in the window, none still "
            f"wedged (the newest resolved){extra}",
            evidence)

    return Check(
        "session-wedge", "No session is wedged in processing",
        "FAIL",
        f"session {key} has been in `processing` for {age}s with "
        f"classification={cls} recovery={rec}",
        evidence,
        fix="The gateway restart guard (ai.sol.gateway-restart-if-idle, "
            "every 5 min) restarts the gateway when the lane is quiet and "
            "the session is classified stalled_agent_run with recovery=none — "
            "that is what released it on 2026-11-03. If it does not fire, "
            "run scripts/restart-and-verify.sh by hand.")


def check_restart_churn(window_hours):
    """Is the gateway restarting for no reason?

    The launchd restart agent (ai.sol.gateway-restart-if-idle) was written to
    restart the gateway "when the lane is idle". That was wrong: idle is the
    NORMAL state. On 2026-11-04 and 2026-11-05 it restarted the gateway 255
    times - roughly every nine minutes, for two days.

    Every restart is not free. It churns the Telegram plugin's polling, it
    reloads the runtime, and it keeps the restart race permanently armed: the
    guard reads "idle", a turn writes its first transcript event two seconds
    later, and the restart kills the reply the user was waiting for (that is
    how messageId 2547 died on 2026-11-03).

    The agent now requires a REASON - a wedged session, or the cache-TTL gate
    not being effective in the running process. This check is the tripwire
    for that rule coming back.
    """
    starts = []
    for path in sorted(glob.glob(LOG_GLOB)):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if "http server listening" not in line:
                        continue
                    if not line.startswith("{"):
                        continue
                    try:
                        rec = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    ts = parse_ts(rec.get("time"))
                    if ts:
                        starts.append(ts)
        except OSError:
            continue

    if not starts:
        return Check("restart-churn", "The gateway is not restarting needlessly",
                     "INFO", "no gateway start recorded in the window")

    hours = max(window_hours, 1)
    # Judge the CURRENT rate, not the historical average. A churn bug that
    # was fixed an hour ago must not keep failing the doctor for the whole
    # window, and a churn bug that started an hour ago must not be diluted
    # by a quiet week. The last hour is the honest signal; the window total
    # is the context.
    now = now_utc()
    recent = [ts for ts in starts
              if (now - ts).total_seconds() <= 3600]
    per_hour = len(recent)
    evidence = [f"{len(starts)} gateway start(s) in the last {hours}h; "
                f"{len(recent)} in the last hour ({per_hour}/hour)"]
    for ts in starts[-6:]:
        evidence.append(f"  started {ts.isoformat(timespec='seconds')}")

    if per_hour > 12:
        return Check(
            "restart-churn", "The gateway is not restarting needlessly",
            "FAIL",
            f"the gateway started {len(recent)} time(s) in the last hour - "
            "it is restarting continuously, and every restart can kill a "
            "reply that was seconds away",
            evidence,
            fix="Read scripts/restart-if-idle.sh: a restart must have a "
                "REASON (a wedged session, or the cache-TTL gate not being "
                "effective in the running process). Restarting because the "
                "lane is idle restarts the gateway every few minutes for no "
                "reason at all.")

    if per_hour > 4:
        return Check(
            "restart-churn", "The gateway is not restarting needlessly",
            "WARN",
            f"the gateway started {len(recent)} time(s) in the last hour",
            evidence,
            fix="Check scripts/restart-if-idle.log for why it is restarting. "
                "A restart is only justified by a wedged session or by the "
                "cache-TTL gate not being effective.")

    return Check(
        "restart-churn", "The gateway is not restarting needlessly",
        "PASS",
        f"{len(recent)} gateway start(s) in the last hour "
        f"({len(starts)} in the last {hours}h)",
        evidence)


def check_config_reload_pending():
    """Has a config change been detected that the running gateway ignored?

    The gateway hot-reloads MOST config paths and says so:
    "config hot reload applied (models.providers.ollama.models)".

    But not all of them. A change under `channels.telegram.streaming.*` is
    announced as

      config change detected; evaluating reload (channels.telegram.streaming.mode, ...)

    and then NOTHING. No applied line, no "needs a restart" line. The
    running gateway keeps the old value until it restarts, and nobody says
    so.

    That trap caught the Telegram streaming mode twice. On 2026-11-03 the
    bot switched it to "progress" with narration and commentary on; the
    reload never applied; the raw model narration only started reaching
    Amre's chat at the next restart, and from then on every reply leaked
    raw reasoning into the conversation. On 2026-11-05 the change back to
    "off" was silently ignored in exactly the same way.

    A config change that silently does not apply is worse than no change:
    you look at the config, you believe it is in effect, and it is not.

    scripts/health/config-reload-pending.py answers the question; this
    check surfaces it, and the restart agent uses it as one of its reasons
    to restart.
    """
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "config-reload-pending.py")
    if not os.path.exists(script):
        return Check("config-reload", "Config changes are applied when detected",
                     "INFO", "config-reload-pending.py is missing - check not run")
    try:
        proc = subprocess.run(
            ["/opt/homebrew/bin/python3", script, "--json"],
            capture_output=True, text=True, timeout=90)
        report = json.loads(proc.stdout or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return Check("config-reload", "Config changes are applied when detected",
                     "INFO", f"could not run the detector: {exc}")

    state = report.get("state")
    detail = report.get("detail") or ""
    if state == "pending":
        return Check(
            "config-reload", "Config changes are applied when detected",
            "FAIL",
            "a config change was detected and never applied - the running "
            "gateway is still using the OLD value",
            [detail,
             f"changed paths: {report.get('detected_paths')}",
             f"detected at: {report.get('detected_at')}"],
            fix="The gateway hot-reloads most config paths but not channel "
                "config. The restart agent (ai.sol.gateway-restart-if-idle) "
                "restarts when a change is pending, so it should apply "
                "within five minutes; if it does not, run "
                "scripts/restart-and-verify.sh by hand.")
    if state == "clean":
        return Check("config-reload", "Config changes are applied when detected",
                     "PASS", detail)
    return Check("config-reload", "Config changes are applied when detected",
                 "INFO", detail or "could not determine")


def collect(window_hours):
    events, source = read_log_events(window_hours)
    return [
        check_gateway_alive(),
        check_overflow(events, window_hours),
        check_precheck_coverage(events, window_hours),
        check_truncation(events, window_hours),
        check_compaction_config(),
        check_config_drift(),
        check_config_reload_events(events, window_hours),
        check_skill_frontmatter(),
        check_skill_catalog(),
        check_cron_contracts(),
        check_stale_cli(),
        check_session_store(),
        check_dead_artifacts(),
        check_cache_ttl_patch(),
        check_cache_ttl_markers(window_hours),
        check_prompt_budget(events, window_hours),
        check_sleep_guard(),
        check_live_turn_safety(),
        check_fallback_capacity(),
        check_provider_health(window_hours),
        check_fallback_models(),
        check_session_wedge(window_hours),
        check_restart_churn(window_hours),
        check_config_reload_pending(),
        check_git_state(),
    ], events, source


def render_finding(c, window_hours):
    """A single finding, rendered for a chat message. Concise on purpose."""
    lines = [f"[{c.status}] {c.title}", f"{c.detail}"]
    for e in c.evidence:
        lines.append(f"- {e}")
    if c.fix:
        lines.append(f"fix: {c.fix}")
    return "\n".join(lines)


# Hard cap on the whole cron message. Telegram splits anything long into
# many parts, so a big report becomes a wall of spam. 3000 chars fits one
# message with room to spare.
MAX_MESSAGE_CHARS = 3000


def cap_message(text):
    """Truncate a rendered report to one chat-sized message."""
    if len(text) <= MAX_MESSAGE_CHARS:
        return text
    return (text[:MAX_MESSAGE_CHARS].rsplit("\n", 1)[0]
            + "\n... (report truncated to protect the chat)")


def render_text(checks, window_hours, source):
    fails = [c for c in checks if c.status == "FAIL"]
    warns = [c for c in checks if c.status == "WARN"]
    passes = [c for c in checks if c.status == "PASS"]
    infos = [c for c in checks if c.status == "INFO"]

    lines = []
    lines.append(f"CLAW DOCTOR — "
                 f"{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}"
                 f"  (window {window_hours}h, log source: {source})")
    lines.append("")
    for group in (fails, warns, infos, passes):
        for c in group:
            lines.append(f"[{c.status}] {c.title}")
            lines.append(f"       {c.detail}")
            for e in c.evidence:
                lines.append(f"       - {e}")
            if c.fix:
                lines.append(f"       fix: {c.fix}")
    lines.append("")
    summary = (f"SUMMARY: {len(passes)} pass, {len(warns)} warn, "
               f"{len(fails)} fail, {len(infos)} info")

    # The report is bounded HERE, not only at the print site. A renderer that
    # returns 127 KB and relies on the caller to truncate it is one careless
    # caller away from the flood. The summary line is reserved first so the
    # reader always learns the verdict.
    body = "\n".join(lines)
    budget = MAX_MESSAGE_CHARS - len(summary) - 2
    if len(body) > budget:
        body = (body[:budget].rsplit("\n", 1)[0]
                + "\n... (report truncated to protect the chat)")
    return f"{body}\n\n{summary}"


def main():
    ap = argparse.ArgumentParser(description="Reliability doctor for Dross")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--cron", action="store_true",
                    help="cron mode: print NO_REPLY when healthy")
    ap.add_argument("--window-hours", type=int, default=24)
    ap.add_argument("--update-baseline", action="store_true",
                    help="accept the current compaction config as baseline")
    args = ap.parse_args()

    os.makedirs(STATE_DIR, exist_ok=True)

    if args.update_baseline:
        try:
            with open(CONFIG_PATH) as fh:
                cfg = json.load(fh)
            live = cfg.get("agents", {}).get("defaults", {}).get("compaction", {})
            state = load_state()
            state["baseline"] = live
            save_state(state)
            print("baseline updated")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"could not update baseline: {exc}", file=sys.stderr)
            return 1

    try:
        checks, events, source = collect(args.window_hours)
    except Exception as exc:  # the doctor must never crash silently
        print(f"claw-doctor failed: {exc}", file=sys.stderr)
        return 1

    fails = [c for c in checks if c.status == "FAIL"]
    warns = [c for c in checks if c.status == "WARN"]

    # Alert policy. Amre was explicit that she does not want to be sent
    # chatter or my thoughts. So the cron announces ONLY on a real failure:
    #   * FAIL  -> always announced, but at most once per REALERT_SECONDS
    #               while it persists.
    #   * WARN  -> NOT announced. A warning is context, not news. On
    #               2026-10-29 this job posted a 255k-character report that
    #               Telegram split into 90 messages, so the bar for waking
    #               Amre is now a genuine FAIL and nothing else. WARNs are
    #               still recorded and visible in the JSON report.
    # Healthy is silent: the doctor prints NO_REPLY and the runner
    # suppresses it.
    state = load_state()
    reported = state.get("reported", {})
    now = time.time()
    fresh = []
    for c in checks:
        prior = reported.get(c.cid)
        if c.status == "FAIL":
            if (not prior or prior.get("status") != "FAIL"
                    or now - prior.get("at", 0) > REALERT_SECONDS):
                fresh.append(c)
                reported[c.cid] = {"status": "FAIL", "at": now,
                                   "detail": c.detail[:200]}
        elif c.status == "WARN":
            # Recorded for the report, never announced.
            reported[c.cid] = {"status": "WARN", "at": now,
                               "detail": c.detail[:200]}
        else:
            reported.pop(c.cid, None)
    state["reported"] = reported
    save_state(state)

    summary = {
        "at": datetime.now().astimezone().isoformat(),
        "windowHours": args.window_hours,
        "logSource": source,
        "counts": {
            "pass": len([c for c in checks if c.status == "PASS"]),
            "warn": len(warns),
            "fail": len(fails),
            "info": len([c for c in checks if c.status == "INFO"]),
        },
        "checks": [c.to_dict() for c in checks],
    }
    try:
        with open(REPORT_PATH, "w") as fh:
            json.dump(summary, fh, indent=2)
    except OSError:
        pass
    append_history({
        "at": summary["at"],
        "counts": summary["counts"],
        "overflow": next((c.detail for c in checks if c.cid == "overflow"), ""),
        "truncation": next((c.detail for c in checks if c.cid == "truncation"), ""),
    })

    if args.json:
        summary["freshFindings"] = [c.cid for c in fresh]
        print(json.dumps(summary, indent=2))
        return 0

    if args.cron:
        if not fresh:
            print("NO_REPLY")
            return 0
        # Only the finding that woke us. A full report every three hours is
        # noise, and Amre asked not to be sent my thoughts.
        head = (f"CLAW DOCTOR — {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}")
        blocks = [render_finding(c, args.window_hours) for c in fresh]
        print(cap_message(f"{head}\n\n" + "\n\n".join(blocks)))
        return 0

    print(cap_message(render_text(checks, args.window_hours, source)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
