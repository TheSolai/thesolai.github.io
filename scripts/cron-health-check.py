#!/usr/bin/env python3
"""
Cron Health Checker — Dross's system integrity monitor.

Surfaces ANY cron currently in an error state (1+ consecutive failures).
Run from HEARTBEAT.md protocol.
"""
import subprocess
import json
import sys
import os
import shutil
from datetime import datetime, timezone

CRON_STATE_FILE = os.path.expanduser("~/.openclaw/state/cron-state.json")

# Fixed 2026-10-22: bare `openclaw` on PATH resolved to a stale 2026.6.35
# Homebrew build which rejects the current ~/.openclaw/openclaw.json, so this
# checker always reported "ERROR: Could not fetch cron jobs" even when crons
# were healthy. Resolve the gateway-owned build explicitly, and only fall back
# to PATH if that is missing.
OPENCLAW_HOME = os.path.expanduser("~/.openclaw")
NODE_BIN = f"{OPENCLAW_HOME}/tools/node-v24.21.0/bin/node"
CLI_MJS = f"{OPENCLAW_HOME}/tools/node-v24.21.0/lib/node_modules/openclaw/openclaw.mjs"


def build_cli_cmd():
    """Return the argv prefix that invokes the authoritative openclaw CLI."""
    if os.path.exists(NODE_BIN) and os.path.exists(CLI_MJS):
        return [NODE_BIN, CLI_MJS]
    fallback = shutil.which("openclaw")
    if fallback:
        return [fallback]
    return None
# Fixed 2026-10-22: threshold was 3, which let a genuinely broken cron
# ("Sol — Repo Roulette Scout" — ModuleNotFoundError) sit unnoticed with
# only 1 recorded error. Any cron in an error state is surfaced now.
ALERT_THRESHOLD = 1

def get_cron_jobs():
    """Get cron jobs via the authoritative openclaw CLI."""
    cmd = build_cli_cmd()
    if cmd is None:
        return None
    try:
        result = subprocess.run(
            cmd + ['cron', 'list', '--json'],
            capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        print(f"  cli-error: rc={result.returncode} stderr={(result.stderr or '').strip()[:300]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def check_failures(jobs):
    """Find crons with 1+ consecutive failures (any cron in error state)."""
    failures = []
    if isinstance(jobs, dict):
        jobs = jobs.get('jobs', [])
    for job in jobs:
        if not isinstance(job, dict):
            continue
        state = job.get('state', {})
        errors = state.get('consecutiveErrors', 0)
        if errors >= ALERT_THRESHOLD:
            # Fixed 2026-10-22: the CLI reports the cause as
            # 'lastErrorReason'. Reading 'lastError' always yielded
            # 'Unknown', so every alert named a cause it never showed.
            last_error = (state.get('lastErrorReason')
                          or state.get('lastError')
                          or 'Unknown')
            duration = state.get('lastDurationMs', 0)
            failures.append({
                'name': job.get('name', 'Unknown'),
                'id': job.get('id', ''),
                'errors': errors,
                'lastError': last_error,
                'durationMs': duration,
                'lastRun': state.get('lastRunAtMs', 0)
            })
    return failures

def main():
    jobs = get_cron_jobs()
    if jobs is None:
        print("ERROR: Could not fetch cron jobs")
        return 1
    
    failures = check_failures(jobs)
    if failures:
        print(f"ALERT: {len(failures)} cron(s) failing:")
        for f in failures:
            last_run = datetime.fromtimestamp(f['lastRun']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if f['lastRun'] else 'never'
            mins = f"{f.get('durationMs', 0)//1000}s" if f.get('durationMs') else "n/a"
            print(f"  - {f['name']}: {f['errors']} failures (last ran: {last_run}, took {mins})")
            print(f"    Error: {f['lastError']}")
        return 2
    
    print("OK: No cron failures detected")
    return 0

if __name__ == '__main__':
    sys.exit(main())
