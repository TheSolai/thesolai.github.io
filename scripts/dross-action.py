#!/usr/bin/env python3
"""
dross-action.py — Detect and execute commands from Amre's emails on the host,
then return the output for Dross to reference in his reply.

Safety:
- Whitelist of allowed commands (ollama, git clone, wget, curl, pip, npm, openclaw, etc.)
- 60s default timeout
- 100KB output cap
- No sudo, no rm, no chmod, no writes to /etc, /System, /usr
- All commands run as the current user (amre)
- Output is captured (stdout + stderr) and returned

Command patterns detected in email body:
  "ollama run X"        → ollama run X (15min timeout for model loads)
  "ollama pull X"       → ollama pull X
  "Download this: URL"  → wget URL (to ~/.dross-downloads/)
  "Run this cmd: X"     → X (validated against whitelist)
  "git clone URL"       → git clone URL (to ~/Projects/ or ~/.openclaw/workspace/)
  "pip install X"       → pip install --user X
  "npm install -g X"    → npm install -g X

Returns: dict with {executed, command, output, error, skipped_reason}
"""
import os
import re
import shlex
import subprocess
import time
from pathlib import Path

USER = os.environ.get('USER', 'amre')
DOWNLOADS_DIR = os.path.expanduser('~/.dross-downloads')
PROJECTS_DIR = os.path.expanduser('~/Projects')
WORKSPACE_DIR = os.path.expanduser('~/.openclaw/workspace')

# Command whitelist — prefixes that are safe to auto-execute
SAFE_PREFIXES = (
    'ollama run ', 'ollama pull ', 'ollama list', 'ollama show ', 'ollama ps',
    'ollama cp ', 'ollama rm ', 'ollama create ',
    'git clone ', 'git status', 'git log', 'git diff', 'git pull',
    'wget ', 'curl ',
    'pip install --user', 'pip3 install --user', 'pip install ', 'pip3 install ',
    'npm install -g ', 'npm list -g', 'npm list',
    'node ', 'python3 ', 'python ',
    'openclaw skills list', 'openclaw skills install ',
    'ls ', 'cat ', 'head ', 'tail ', 'grep ', 'find ', 'wc ', 'file ',
    'echo ', 'date ', 'whoami', 'pwd', 'df -h', 'du -sh', 'ps aux', 'top -l 1',
    'mkdir -p ', 'mv ', 'cp ', 'touch ',
    'which ', 'whereis ',
    'brew list', 'brew info ', 'brew search ',
    'ollama --version', 'node --version', 'python3 --version', 'git --version',
    'diskutil list', 'system_profiler ',
)

# Hard block — never execute these even if whitelisted
HARD_BLOCK = (
    'rm ', 'rm -', 'rmdir ', 'sudo ', 'su ', 'chmod ', 'chown ', 'chgrp ',
    'mv /etc', 'mv /System', 'mv /usr', 'mv /bin', 'mv /sbin',
    'rm -rf /', 'rm -rf ~', 'rm -rf .',
    'dd ', 'mkfs', 'fdisk', 'diskutil eraseDisk', 'diskutil partitionDisk',
    'kill -9 1', 'killall ', 'pkill -9 init', 'pkill -9 launchd',
    ':(){:|:&};:',  # fork bomb
    'curl | sh', 'curl | bash', 'wget | sh', 'wget | bash',  # pipe to shell
    '> /etc/', '> /System/', '> /usr/', '> /bin/', '> /sbin/',
    'eval ', 'exec ',
)


def is_safe(command):
    """Check if a command is safe to execute."""
    cmd_lower = command.lower().strip()
    # Hard block first
    for blocked in HARD_BLOCK:
        if blocked.lower() in cmd_lower:
            return False, f'HARD BLOCKED: contains "{blocked.strip()}"'
    # Must match at least one safe prefix
    for prefix in SAFE_PREFIXES:
        if cmd_lower.startswith(prefix.lower()):
            return True, None
    return False, f'NOT WHITELISTED: no safe prefix match'


def extract_command(body):
    """Extract the first executable command from email body."""
    if not body:
        return None

    # Normalize: replace newlines with spaces, collapse whitespace
    # so "ollama run\nhf.co/X" becomes "ollama run hf.co/X"
    normalized = re.sub(r'\s+', ' ', body).strip()
    lines = [normalized] + body.split('\n')  # Try normalized first, then per-line

    # Pattern 1: explicit "Run this cmd:" or "Run:" prefix
    for line in lines:
        line = line.strip()
        m = re.match(r'(?:run this cmd|run this|run:|cmd:|command:)\s*[`]?(.+?)[`]?$', line, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Pattern 2: "ollama run X" / "ollama pull X" (handles multi-line)
    for line in lines:
        line = line.strip()
        m = re.match(r'ollama\s+(run|pull|list|show|cp|rm|create)\s+(.+)$', line, re.IGNORECASE)
        if m:
            return f'ollama {m.group(1).lower()} {m.group(2).strip()}'

    # Pattern 3: "Download this for ollama" with URL
    m = re.search(r'(https?://[^\s]+)', body)
    if m and 'download' in body.lower():
        url = m.group(1)
        if 'huggingface.co' in url.lower():
            hf_path = url.split('huggingface.co/')[-1].rstrip('/')
            return f'ollama pull hf.co/{hf_path}'
        return f'curl -L -o {DOWNLOADS_DIR}/$(basename {url}) {url}'

    # Pattern 4: "git clone URL" anywhere
    m = re.search(r'(https?://github\.com/[\w\-]+/[\w\-]+(?:\.git)?)', body)
    if m:
        return f'git clone {m.group(1)} {PROJECTS_DIR}/'

    # Pattern 5: pip install / npm install
    m = re.search(r'pip(?:3)?\s+install\s+([\w\-=\.]+)', body, re.IGNORECASE)
    if m:
        return f'pip3 install --user {m.group(1)}'
    m = re.search(r'npm\s+install(?:\s+-g)?\s+([\w\-@/]+)', body, re.IGNORECASE)
    if m:
        return f'npm install -g {m.group(1)}'

    return None


def execute(command, timeout=60):
    """Execute a command and return (output, error, returncode)."""
    try:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser('~'),
        )
        output = (result.stdout or '') + (result.stderr or '')
        # Strip ANSI escape codes (cursor moves, colors, spinner chars)
        output = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', output)
        output = re.sub(r'\x1b\[\?[0-9]+[hl]', '', output)
        # Collapse repeated identical progress lines ("pulling manifest" x6)
        lines = output.split('\n')
        deduped = []
        last = None
        for ln in lines:
            stripped = ln.strip()
            if stripped and stripped == last and 'pulling' in stripped.lower():
                continue
            if stripped:
                deduped.append(ln)
            last = stripped
        output = '\n'.join(deduped).strip()
        # Cap output at 100KB to keep replies sane
        if len(output) > 100_000:
            output = output[:50_000] + '\n\n[... output truncated at 100KB ...]\n\n' + output[-50_000:]
        return output, None, result.returncode
    except subprocess.TimeoutExpired:
        return '', f'Command timed out after {timeout}s', -1
    except Exception as e:
        return '', f'Execution error: {e}', -1


def run(body, timeout=60):
    """Main entry: detect command, validate, execute, return result."""
    cmd = extract_command(body)
    if not cmd:
        return {
            'executed': False,
            'skipped_reason': 'no command detected in email body',
        }

    safe, reason = is_safe(cmd)
    if not safe:
        return {
            'executed': False,
            'command': cmd,
            'skipped_reason': reason,
        }

    # Auto-extend timeout for known-slow commands
    if 'ollama' in cmd and 'pull' in cmd:
        timeout = max(timeout, 900)  # 15 min for model loads
    if 'ollama' in cmd and ' run ' in (' ' + cmd + ' '):
        # Don't actually start an interactive chat — verify the model exists instead
        # Extract model name from "ollama run MODEL"
        parts = cmd.split()
        if len(parts) >= 3:
            model_name = parts[2]
            cmd = f'ollama show {model_name}'  # verify model exists, no chat
    if 'git clone' in cmd:
        timeout = max(timeout, 300)  # 5 min for clones

    start = time.time()
    output, error, rc = execute(cmd, timeout=timeout)
    duration = time.time() - start

    result = {
        'executed': True,
        'command': cmd,
        'output': output,
        'error': error,
        'returncode': rc,
        'duration_seconds': round(duration, 1),
    }

    # For ollama commands, also fetch the model list as context
    if 'ollama' in cmd:
        try:
            list_output, _, list_rc = execute('ollama list', timeout=10)
            result['ollama_list'] = list_output
        except Exception:
            pass

    return result


if __name__ == '__main__':
    import json
    import sys
    body = sys.stdin.read()
    result = run(body)
    print(json.dumps(result, indent=2))
