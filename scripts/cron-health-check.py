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
from datetime import datetime, timezone

CRON_STATE_FILE = os.path.expanduser("~/.openclaw/state/cron-state.json")
# Fixed 2026-10-22: threshold was 3, which let a genuinely broken cron
# ("Sol — Repo Roulette Scout" — ModuleNotFoundError) sit unnoticed with
# only 1 recorded error. Any cron in an error state is surfaced now.
ALERT_THRESHOLD = 1

def get_cron_jobs():
    """Get cron jobs via openclaw CLI."""
    result = subprocess.run(
        ['openclaw', 'cron', 'list', '--json'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except:
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
            failures.append({
                'name': job.get('name', 'Unknown'),
                'id': job.get('id', ''),
                'errors': errors,
                'lastError': state.get('lastError', 'Unknown'),
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
            print(f"  - {f['name']}: {f['errors']} failures (last ran: {last_run})")
            print(f"    Error: {f['lastError']}")
        return 2
    
    print("OK: No cron failures detected")
    return 0

if __name__ == '__main__':
    sys.exit(main())
