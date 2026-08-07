#!/usr/bin/env python3
"""
agent-email-handler.py — autonomous email checker/replier for Sol and Dross.

Loop prevention layers:
1. State file in /tmp/agent-email-state/ — tracks replied message IDs
2. Per-run in-memory set — prevents double-reply within same script run
3. Mark-before-send — mark replied BEFORE calling the API
4. in_reply_to header — lets the mail API deduplicate
5. Skip inter-agent emails entirely — Sol and Dross don't reply to each other via email
6. Skip own sent messages — never reply to self

Usage:
    python3 agent-email-handler.py <agent_name> <inbox_id> <key_file>

Dry run (no replies sent):
    DRY_RUN=1 python3 agent-email-handler.py <agent_name> <inbox_id> <key_file>
"""
import json
import subprocess
import sys
import os
import re
import fcntl
import time
from datetime import datetime, timezone
from urllib.parse import quote

# Age cutoff for replies — do NOT reply to emails older than this
# 24h was too aggressive — messages pile up as "unread but skipped".
# Increased to 168h (1 week) so legitimate older messages get replies.
MAX_EMAIL_AGE_HOURS = 168

SIGNATURES = {
    'Sol':   '⚡',
    'Dross': '🌀',
}

STATE_DIR = '/tmp/agent-email-state'

# Per-run tracking — prevents double-reply within same script invocation
_processed_this_run = set()

# Agents that should NEVER receive email replies (inter-agent communication)
AGENT_ADDRESSES = {
    'sol-ai@agentmail.to',
    'thedross@agentmail.to',
}


def get_replied(agent_name):
    """Load replied set from state file. Returns set of message IDs."""
    path = os.path.join(STATE_DIR, f'{agent_name.lower()}_replied.json')
    if os.path.exists(path):
        try:
            with open(path) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_replied(agent_name, replied_set):
    """Atomically write replied set to state file with file locking."""
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f'{agent_name.lower()}_replied.json')
    lock_path = path + '.lock'
    try:
        with open(lock_path, 'w') as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                with open(path, 'w') as f:
                    json.dump(sorted(replied_set), f)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
    except IOError:
        pass


def mark_replied(agent_name, msg_id):
    """Mark a message ID as replied — BEFORE sending the reply.
    Uses file locking to prevent race conditions when multiple handlers run concurrently."""
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f'{agent_name.lower()}_replied.json')
    lock_path = path + '.lock'
    try:
        with open(lock_path, 'w') as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                # Read current state
                if os.path.exists(path):
                    try:
                        with open(path) as f:
                            existing = set(json.load(f))
                    except (json.JSONDecodeError, IOError):
                        existing = set()
                else:
                    existing = set()
                existing.add(msg_id)
                with open(path, 'w') as f:
                    json.dump(sorted(existing), f)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
    except IOError:
        pass


def is_replied(agent_name, msg_id):
    """Check if we've already replied to this message ID."""
    if msg_id in _processed_this_run:
        return True  # Already processed in this run
    return msg_id in get_replied(agent_name)


def get_key(path):
    with open(os.path.expanduser(path)) as f:
        return f.read().strip()


def encode_msg_id(url):
    parts = url.split('/messages/', 1)
    if len(parts) == 2:
        encoded_id = quote(parts[1], safe='')
        return parts[0] + '/messages/' + encoded_id
    return url


def api(url, key, method='GET', data=None):
    url = encode_msg_id(url)
    cmd = ['curl', '-s', '-X', method if method != 'GET' else 'GET', url,
           '-H', f'Authorization: Bearer {key}']
    if method != 'GET' and data is not None:
        cmd += ['-H', 'Content-Type: application/json',
                '-d', json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def list_messages(inbox_id, key, limit=500):
    """Fetch ALL messages via pagination. The API returns max 1000 per call,
    but Sol has 1000+ messages. We paginate until we have everything.
    Returns dict with 'messages' key."""
    all_messages = []
    page_token = None
    max_pages = 10  # Safety limit: 10 pages × 1000 = 10,000 messages max
    base_url = f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages'
    
    for _ in range(max_pages):
        url = f'{base_url}?limit={limit}'
        if page_token:
            url += f'&page_token={quote(page_token, safe="")}'
        data = api(url, key)
        msgs = data.get('messages', [])
        all_messages.extend(msgs)
        page_token = data.get('next_page_token')
        if not page_token or not msgs:
            break
    
    return {'messages': all_messages}


def get_message(inbox_id, msg_id, key):
    # Strip angle brackets — API IDs come with <>, but URLs need raw IDs
    clean_id = msg_id.strip().strip('<>').strip()
    return api(f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/{clean_id}', key)


def clean_id(msg_id):
    """Strip angle brackets from a message ID for use in URLs."""
    return msg_id.strip().strip('<>').strip()


def send_reply(inbox_id, to_email, subject, body_text, in_reply_to, key):
    """Send a reply email. in_reply_to enables API-level deduplication."""
    reply_subject = subject if subject.startswith('Re: ') else f'Re: {subject}'
    return api(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send',
        key, method='POST',
        data={
            'to': [to_email],
            'subject': reply_subject,
            'text': body_text,
            'in_reply_to': in_reply_to,
        }
    )


def mark_seen(inbox_id, msg_id, key):
    api(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/{clean_id(msg_id)}',
        key, method='PATCH',
        data={'labels': ['received', 'seen']}
    )


def extract_email(msg):
    from_field = msg.get('from') or msg.get('from_') or ''
    if isinstance(from_field, str):
        m = re.search(r'<(.+?)>', from_field)
        return m.group(1).strip() if m else from_field.strip()
    elif isinstance(from_field, dict):
        return from_field.get('email', 'unknown')
    return 'unknown'


def generate_reply(agent_name, sender_email, subject, body, sig):
    body_lower = body.lower()
    sender_is_dross = 'thedross@agentmail.to' in sender_email
    sender_is_sol = 'sol-ai@agentmail.to' in sender_email

    # Inter-agent banter — but we skip replying to agents (see main loop)
    if sender_is_dross and agent_name == 'Sol':
        return f'Noted, Dross. All nominal here. — {sig}'
    if sender_is_sol and agent_name == 'Dross':
        return f'Sol. Message received. Carry on. — {sig}'

    # Human emails
    if any(k in body_lower for k in ['help', 'question', 'can you', 'could you', 'please', 'thanks', 'thank you']):
        return f"Hi — {agent_name} here. Got your message and will follow up shortly. — {sig}"
    return f"Hi — {agent_name} here. Message received, will get back to you. — {sig}"


def main():
    if len(sys.argv) < 4:
        print('Usage: agent-email-handler.py <agent_name> <inbox_id> <key_file>')
        sys.exit(1)

    agent_name = sys.argv[1]
    inbox_id = sys.argv[2]
    key_file = sys.argv[3]
    sig = SIGNATURES.get(agent_name, '✨')
    dry_run = os.environ.get('DRY_RUN', '0') == '1'

    key = get_key(key_file)
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {agent_name} handler: {inbox_id}' + (' [DRY RUN]' if dry_run else ''))

    messages = list_messages(inbox_id, key).get('messages', [])
    print(f'  {len(messages)} messages in inbox')

    replied = 0
    skipped = 0

    for msg in messages:
        labels = set(msg.get('labels', []))
        is_sent = 'sent' in labels

        # NEVER reply to own sent messages — also skip mark_seen for these
        if is_sent:
            skipped += 1
            continue  # <-- THIS WAS MISSING! Without this, fell through to get_message() for 1000+ sent messages

        msg_id = msg.get('message_id', '')
        subject = msg.get('subject', '(no subject)')
        sender_email = extract_email(msg)

        # Skip unknown senders or self
        if sender_email == 'unknown' or sender_email == inbox_id:
            skipped += 1
            continue

        # CRITICAL: Never reply to other agents via email — skip inter-agent addresses
        if sender_email.lower() in AGENT_ADDRESSES:
            skipped += 1
            continue

        # Skip mailer-daemon / bounce notifications — do NOT reply to these ever
        if 'mailer-daemon' in sender_email.lower() or 'postmaster' in sender_email.lower():
            skipped += 1
            continue

        # Loop prevention: skip if already replied (state file + in-memory)
        if msg_id and is_replied(agent_name, msg_id):
            skipped += 1
            continue

        # Check message age — skip emails older than MAX_EMAIL_AGE_HOURS
        msg_time_str = msg.get('created_at') or msg.get('timestamp') or msg.get('date')
        if msg_time_str:
            try:
                msg_time = datetime.fromisoformat(msg_time_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_hours = (now - msg_time.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if age_hours > MAX_EMAIL_AGE_HOURS:
                    print(f'  ⏭ [{sender_email}]: "{subject[:40]}" — {age_hours:.1f}h old, skipping')
                    skipped += 1
                    continue
            except (ValueError, TypeError):
                pass  # Can't parse timestamp — proceed with caution

        try:
            full = get_message(inbox_id, msg_id, key)
        except Exception as e:
            print(f'  ERROR reading {msg_id[:30]}: {e}')
            skipped += 1
            continue

        body = (full.get('extracted_text') or full.get('text') or '').strip()
        # Fallback to preview from list response for Gmail-sourced messages
        if len(body) < 3:
            body = (msg.get('preview') or '').strip()
        if len(body) < 3:
            mark_seen(inbox_id, msg_id, key)
            skipped += 1
            continue

        # ── DROSS: use LLM-powered reply generator for actual character ──
        dross_llm_success = False
        if agent_name == 'Dross':
            llm_script = os.path.expanduser('~/.openclaw/workspace/scripts/dross-llm-reply.py')
            if os.path.exists(llm_script) and os.environ.get('MINIMAX_API_KEY'):
                if dry_run:
                    llm_args = [sys.executable, llm_script, msg_id, '--no-send']
                else:
                    llm_args = [sys.executable, llm_script, msg_id]
                try:
                    llm_result = subprocess.run(llm_args, capture_output=True, text=True, timeout=60)
                    # Parse the last JSON object from output
                    reply_text = None
                    last_status = None
                    last_error = None
                    for line in llm_result.stdout.strip().split('\n\n'):
                        try:
                            obj = json.loads(line)
                            if 'reply' in obj:
                                reply_text = obj['reply']
                                last_status = obj.get('status')
                                last_error = obj.get('error')
                        except json.JSONDecodeError:
                            continue
                    if not reply_text:
                        print(f'  ⚠ Dross LLM returned no reply, falling back to template. stdout: {llm_result.stdout[:200]}')
                        reply_text = generate_reply(agent_name, sender_email, subject, body, sig)
                    else:
                        dross_llm_success = (last_status == 'sent')
                        if last_status == 'failed':
                            print(f'  ⚠ Dross LLM send failed: {last_error}')
                except subprocess.TimeoutExpired:
                    print(f'  ⚠ Dross LLM timed out, falling back to template')
                    reply_text = generate_reply(agent_name, sender_email, subject, body, sig)
                except Exception as e:
                    print(f'  ⚠ Dross LLM error: {e}, falling back to template')
                    reply_text = generate_reply(agent_name, sender_email, subject, body, sig)
            else:
                if not os.environ.get('MINIMAX_API_KEY'):
                    print(f'  ⚠ MINIMAX_API_KEY not set — Dross will reply in template mode')
                reply_text = generate_reply(agent_name, sender_email, subject, body, sig)
        else:
            reply_text = generate_reply(agent_name, sender_email, subject, body, sig)

        print(f'  → {sender_email}: "{subject[:40]}"')
        print(f'    Reply: "{reply_text[:80]}..."')

        # DRY RUN: don't actually send
        if dry_run:
            print(f'    [DRY RUN — not sending]')
            replied += 1
            continue

        # Dross: the LLM script handles its own send AND its own state via the reply cache.
        # If the LLM script reports status='sent', we mark the handler's replied state.
        # If it reports 'failed' (e.g. AgentMail rate limit), we DO NOT mark replied —
        # the next cron run will retry.
        if agent_name == 'Dross' and not dry_run:
            if dross_llm_success:
                # LLM script already sent + marked_seen. Mark replied in our state.
                if msg_id:
                    mark_replied(agent_name, msg_id)
                    _processed_this_run.add(msg_id)
                replied += 1
            else:
                # LLM failed — do not mark replied. Next cron run will retry.
                print(f'  ⏭ Not marking replied (LLM send failed) — will retry next run')
                skipped += 1
            continue

        # Sol (template-based): original logic
        try:
            if msg_id:
                mark_replied(agent_name, msg_id)
                _processed_this_run.add(msg_id)

            send_reply(inbox_id, sender_email, subject, reply_text, msg_id, key)
            replied += 1

        except Exception as e:
            print(f'  ERROR: {e}')
            if msg_id and msg_id in _processed_this_run:
                _processed_this_run.discard(msg_id)

        mark_seen(inbox_id, msg_id, key)

    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {agent_name} done. Replied: {replied} | Skipped: {skipped}')


if __name__ == '__main__':
    main()
