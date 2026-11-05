#!/usr/bin/env python3
"""
config-reload-pending.py — has a config change been detected that the running
gateway has NOT applied?

WHY THIS EXISTS
  The gateway hot-reloads most config paths, and it says so:
  "config hot reload applied (models.providers.ollama.models)".

  But NOT every path. A change under `channels.telegram.streaming.*` is
  announced as

    config change detected; evaluating reload (channels.telegram.streaming.mode, ...)

  and then... nothing. No "applied" line. No "needs a restart" line. The
  change simply does not take effect until the gateway restarts, and the
  gateway does not say so.

  That is a SILENT failure, and it has bitten twice:

    * 2026-11-03 18:08 — the bot switched Telegram streaming to
      "progress" with narration and commentary on. The reload was detected
      and never applied. It only took effect at the 18:16:13 restart, and
      from then on every reply streamed the model's raw narration into
      Amre's chat. She described it as "my replies were leaking raw
      reasoning into the chat" and eventually as "this keeps happening".

    * 2026-11-05 08:35 — the same path was changed back to "off". Same
      silence. The change was NOT live; only a restart would apply it.

  A config change that silently does not apply is worse than no change:
  you look at the config, you believe it is in effect, and it is not.

HOW IT ANSWERS THE QUESTION
  It compares the last "config change detected" event with the last
  "config hot reload applied" event. If a detection has no matching
  application after it, the change is still pending.

Usage:
  config-reload-pending.py          # human-readable
  config-reload-pending.py --json   # machine-readable

Exit codes:
  0  no pending change (everything detected was applied)
  1  a config change is pending — a restart would apply it
  2  it could not be determined
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys

LOG_DIR = "/tmp/openclaw"
LOG_GLOB = os.path.join(LOG_DIR, "openclaw-*.log")
GATEWAY_LOG = os.path.expanduser("~/Library/Logs/openclaw/gateway.log")


def _ts(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def scan_json_log():
    """(last_detected, last_applied) from the JSON logs."""
    detected = []
    applied = []
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
                    msg = rec.get("message") or rec.get("1") or ""
                    ts = _ts(rec.get("time"))
                    if "config change detected" in msg:
                        paths = ""
                        m = re.search(r"\(([^)]*)\)", msg)
                        if m:
                            paths = m.group(1)
                        detected.append((ts, paths))
                    elif "config hot reload applied" in msg:
                        paths = ""
                        m = re.search(r"\(([^)]*)\)", msg)
                        if m:
                            paths = m.group(1)
                        applied.append((ts, paths))
        except OSError:
            continue
    return detected, applied


def scan_plain_log():
    """Fallback: the plain gateway log, whose timestamps are UTC ISO."""
    detected = []
    applied = []
    try:
        with open(GATEWAY_LOG, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "config change detected" in line:
                    m = re.search(r"^(\S+)", line)
                    paths = ""
                    pm = re.search(r"\(([^)]*)\)", line)
                    if pm:
                        paths = pm.group(1)
                    detected.append((_ts(m.group(1)) if m else None, paths))
                elif "config hot reload applied" in line:
                    m = re.search(r"^(\S+)", line)
                    paths = ""
                    pm = re.search(r"\(([^)]*)\)", line)
                    if pm:
                        paths = pm.group(1)
                    applied.append((_ts(m.group(1)) if m else None, paths))
    except OSError:
        pass
    return detected, applied


def gateway_start_epoch():
    """Start time of the running gateway process, as a unix epoch."""
    import subprocess
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True,
                             text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pid = None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "ai.openclaw.gateway":
            try:
                pid = int(parts[0])
            except ValueError:
                pid = None
    if not pid:
        return None
    try:
        lstart = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="],
                                capture_output=True, text=True,
                                timeout=20).stdout.strip()
        if not lstart:
            return None
        return int(subprocess.run(
            ["date", "-j", "-f", "%a %b %e %H:%M:%S %Y", lstart, "+%s"],
            capture_output=True, text=True, timeout=20).stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    detected, applied = scan_json_log()
    if not detected:
        detected, applied = scan_plain_log()

    result = {"state": "unknown", "detail": "", "detected_paths": None,
              "detected_at": None, "applied_at": None}

    if not detected:
        result["state"] = "clean"
        result["detail"] = ("no config change was detected in the logs — "
                            "nothing is pending")
    else:
        last_det = max(detected, key=lambda x: x[0] or datetime.datetime.min.replace(
            tzinfo=datetime.timezone.utc))
        det_ts, det_paths = last_det
        later_applied = [a for a in applied
                         if a[0] and det_ts and a[0] > det_ts]
        # A RESTART also resolves it: the new process read the config at
        # startup. Only a change detected AFTER the current gateway
        # started is still pending. Without this the detector reports
        # "pending" forever after the very restart that applied the
        # change - and the restart agent then restarts in a loop.
        gw_start = gateway_start_epoch()
        restarted_after = False
        if gw_start and det_ts:
            restarted_after = det_ts.timestamp() < gw_start
        if later_applied:
            ap = max(later_applied, key=lambda x: x[0])
            result["state"] = "clean"
            result["detail"] = (f"the last config change ({det_paths}) was "
                                f"applied at {ap[0].isoformat(timespec='seconds')}")
            result["applied_at"] = ap[0].isoformat(timespec="seconds")
        elif restarted_after:
            result["state"] = "clean"
            result["detail"] = (f"the last config change ({det_paths}) was "
                                f"picked up by the gateway restart that started "
                                f"this process")
        else:
            result["state"] = "pending"
            result["detail"] = (f"a config change was detected and never "
                                f"applied: {det_paths}. The running gateway "
                                f"is still using the OLD value; a restart "
                                f"would apply it.")
            result["detected_paths"] = det_paths
            result["detected_at"] = (det_ts.isoformat(timespec="seconds")
                                      if det_ts else None)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"state:  {result['state']}")
        print(f"detail: {result['detail']}")

    return {"clean": 0, "pending": 1}.get(result["state"], 2)


if __name__ == "__main__":
    sys.exit(main())
