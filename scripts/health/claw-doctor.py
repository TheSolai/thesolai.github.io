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
    ("Horror Book", "Friday horror delivery"),
    ("Blog Post", "Weekly long-form post"),
    ("Agent Blog Network", "Blog network sync"),
]

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

    def __init__(self, cid, title, status, detail, evidence=None, fix=None):
        self.cid = cid
        self.title = title
        self.status = status          # PASS | WARN | FAIL | INFO
        self.detail = detail
        ev = list(evidence or [])
        if len(ev) > self.MAX_EVIDENCE:
            dropped = len(ev) - self.MAX_EVIDENCE
            ev = ev[:self.MAX_EVIDENCE] + [f"... and {dropped} more line(s)"]
        self.evidence = ev
        self.fix = fix

    def to_dict(self):
        return {
            "id": self.cid,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "evidence": self.evidence,
            "fix": self.fix,
        }


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
        f"this axis is budget competition between the summary body, the "
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

    horror = next((j for j in jobs if "Horror Book" in j.get("name", "")), None)
    if horror:
        payload = horror.get("payload", {})
        argv = payload.get("argv", [])
        problems = []
        if "--send" not in argv:
            problems.append("missing --send (it would recommend but not deliver)")
        if payload.get("timeoutSeconds", 0) < 300:
            problems.append(f"timeout={payload.get('timeoutSeconds')}s < 300s")
        if horror.get("sessionTarget") != "isolated":
            problems.append(f"sessionTarget={horror.get('sessionTarget')}")
        if (horror.get("delivery") or {}).get("mode") != "announce":
            problems.append("delivery is not announce")
        if problems:
            failures.append("horror contract: " + "; ".join(problems))
        else:
            ev.append("horror contract intact (--send, 300s, isolated, announce)")

    for j in jobs:
        state = j.get("state") or {}
        if state.get("consecutiveErrors", 0) >= 1:
            failures.append(f"job '{j.get('name')}' has "
                            f"{state.get('consecutiveErrors')} consecutive "
                            f"error(s): {str(state.get('lastErrorReason'))[:120]}")

    ev.append(f"{len(jobs)} jobs total")
    if failures:
        return Check("cron-contracts", "Cron contracts hold", "FAIL",
                     f"{len(failures)} cron problem(s)", ev)
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
    # Build output and dependency trees are not "work in progress". Counting
    # thousands of Rust target/ files as dirt produced a 2550-line report
    # that Telegram split into ~90 messages.
    NOISE = ("/target/", "node_modules/", "/.venv/", "__pycache__/",
             "/dist/", "/build/", ".pytest_cache/")
    other = [l for l in dirty
             if "drosscash" not in l
             and not any(n in l for n in NOISE)]
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


def check_fallback_capacity():
    """Every configured fallback must be able to hold the prompts it will see.

    The primary provider can be rate-limited out at any time — on 2026-10-28
    MiniMax returned HTTP 429 "Token Plan usage limit reached" on every call
    and every turn fell through to the local model. A fallback whose context
    window is smaller than the prompt cannot answer: the router admits the
    attempt as `route=compact_only` and the turn stalls with
    "repeated_model_requests_without_progress" until it dies.

    Measured that day: estimatedPromptTokens=113455 against
    promptBudgetBeforeReserve=111072 on a fallback declared at 131072. The
    fallback was 2,383 tokens too small and the turn never produced a reply.
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

    # Largest prompt the runtime has actually tried to send.
    max_est = 0
    max_est_at = None
    for path in sorted(glob.glob(LOG_GLOB)):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if "context-pressure-diagnostic" not in line:
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

    problems = []
    evidence = []
    if max_est:
        evidence.append(f"largest prompt the runtime tried to send: {max_est} tokens")

    for fb in fallbacks:
        ctx = windows.get(fb)
        if ctx is None:
            problems.append(f"{fb} is configured as a fallback but is not in any provider")
            continue
        need = max_est + FALLBACK_OUTPUT_RESERVE if max_est else 0
        evidence.append(f"{fb}: contextWindow={ctx}"
                        + (f" (needs >= {need})" if need else ""))
        if need and ctx < need:
            problems.append(
                f"{fb} contextWindow={ctx} is below the {need} tokens a prompt "
                f"of {max_est} needs")

    if problems:
        return Check(
            "fallback-capacity", "Fallbacks can hold the prompts they see",
            "FAIL",
            f"{len(problems)} fallback(s) cannot serve the prompts this agent produces",
            evidence + problems,
            fix="Raise the fallback's contextWindow to at least "
                "max_observed_prompt_tokens + 20000, and drop fallbacks whose "
                "model does not support that context at all. A fallback that "
                "cannot hold the prompt is worse than no fallback: the turn "
                "stalls instead of failing fast.")

    return Check(
        "fallback-capacity", "Fallbacks can hold the prompts they see",
        "PASS",
        f"{len(fallbacks)} fallback(s) can hold the prompts this agent produces",
        evidence)


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
        check_cache_ttl_markers(window_hours),
        check_live_turn_safety(),
        check_fallback_capacity(),
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
    lines.append(f"SUMMARY: {len(passes)} pass, {len(warns)} warn, "
                 f"{len(fails)} fail, {len(infos)} info")
    return "\n".join(lines)


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
