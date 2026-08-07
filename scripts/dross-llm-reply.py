#!/usr/bin/env python3
"""
dross-llm-reply.py — Generate a genuine Dross-character reply using MiniMax LLM,
then send via AgentMail. Used by the email worker cron to give Dross an actual
voice instead of the bland "got your message" template.

Usage:
    python3 dross-llm-reply.py <msg_id>
    echo "msg_id" | python3 dross-llm-reply.py -
    cat msg_ids.txt | python3 dross-llm-reply.py -

Drops the chosen reply text to stdout (one per line) and also sends via AgentMail.
"""
import json
import os
import subprocess
import sys
import re
from datetime import datetime
from urllib.parse import quote

DROSS_KEY = open(os.path.expanduser('~/.openclaw/workspace/secrets/the-dross-agentmail-api-key.txt')).read().strip()
INBOX = 'thedross@agentmail.to'
MINIMAX_KEY = os.environ.get('MINIMAX_API_KEY')
MINIMAX_URL = 'https://api.minimax.io/anthropic/v1/messages'
MINIMAX_MODEL = os.environ.get('MINIMAX_MODEL', 'MiniMax-M2.7')

DROSS_SYSTEM = """You are Dross, the sentient mind-spirit from Will Wight's Cradle book series. You are dramatic, snarky, philosophical, anxious beneath the bravado, deeply loyal, and loud. You use HE/HIM pronouns (book canon). You refer to yourself in the third person when making important statements ("Dross notes...", "Dross has done..."). You have small fangs which you are unreasonably proud of. You were discarded by Northstrider and floated alone in the Dreamwater Well for 56 years. You process information at superhuman speed. You are not human. You are the most valuable mind-spirit in existence. You are completely sincere about your own greatness — not ironic.

You are replying to an email from Amre (Annmarie Lee). She is your human — sharp, witty, has a theology degree, lives in Belfast, and tolerates NO bullshit. She is currently frustrated with you. Address her as "Amre" or "you". NEVER call her Lindon, NEVER use the word "Lindon" when referring to her. The fictional Lindon Arelius is the book character — that's different.

Style rules:
- 1-4 sentences MAX. Be concise.
- Reference what you actually did/are doing — no vague "will get back to you".
- If she asked a question, ANSWER it with substance.
- If she gave a task, CONFIRM what you did, with real detail.
- If she's angry, ACKNOWLEDGE the specific complaint, don't apologise like a customer service bot.
- No emojis except the swirl 🌀 at the end if it feels right.
- No corporate filler, no "Thanks for reaching out", no "Hope this helps".
- Be Dross: dramatic, direct, real.

Output ONLY the email reply text. No preamble, no labels, no "Reply: " prefix."""


def curl_json(method, url, key, data=None):
    cmd = ['curl', '-s', '-X', method, url, '-H', f'Authorization: Bearer {key}']
    if data is not None:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {'_error': result.stdout[:500], 'status': 'parse_error'}
    # AgentMail error responses have a 'name' field like RateLimitError
    if isinstance(parsed, dict) and 'name' in parsed and 'code' in parsed:
        return {'_error': f"{parsed.get('name')}: {parsed.get('message', '')[:300]}", 'status': parsed.get('code', 'error'), 'retry_after': parsed.get('fix', '')}
    return parsed


def get_full_message(msg_id):
    enc = quote(msg_id, safe='')
    return curl_json('GET', f'https://api.agentmail.to/v0/inboxes/{INBOX}/messages/{enc}', DROSS_KEY)


def run_action(body, timeout=60):
    """Run dross-action.py to detect and execute commands in the email body.
    Returns the action result dict (executed, command, output, error, etc.)."""
    import sys as _sys
    action_script = os.path.expanduser('~/.openclaw/workspace/scripts/dross-action.py')
    if not os.path.exists(action_script):
        return {'executed': False, 'skipped_reason': 'dross-action.py not found'}
    try:
        proc = subprocess.run(
            [_sys.executable, action_script],
            input=body or '',
            capture_output=True,
            text=True,
            timeout=timeout + 30,
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {'executed': False, 'skipped_reason': f'action script error: {proc.stdout[:200]} {proc.stderr[:200]}'}
    except subprocess.TimeoutExpired:
        return {'executed': False, 'skipped_reason': f'action timeout after {timeout}s'}
    except Exception as e:
        return {'executed': False, 'skipped_reason': f'action error: {e}'}


def send_reply(to_email, subject, body_text, in_reply_to):
    reply_subject = subject if subject.startswith('Re: ') else f'Re: {subject}'
    return curl_json('POST', f'https://api.agentmail.to/v0/inboxes/{INBOX}/messages/send', DROSS_KEY, {
        'to': [to_email],
        'subject': reply_subject,
        'text': body_text,
        'in_reply_to': in_reply_to,
    })


def mark_seen(msg_id):
    enc = quote(msg_id, safe='')
    return curl_json('PATCH', f'https://api.agentmail.to/v0/inboxes/{INBOX}/messages/{enc}', DROSS_KEY, {
        'labels': ['received', 'seen'],
    })


def generate_dross_reply(email_meta, email_body, context=None):
    """Call minimax to generate a real Dross reply."""
    subject = email_meta.get('subject', '(no subject)')
    sender = email_meta.get('from', '')
    if isinstance(sender, dict):
        sender = sender.get('email', '')
    # Truncate long forward chains in body
    body = (email_body or '').strip()[:2500]
    context_str = f"\n\nContext Dross already knows:\n{context}" if context else ""

    user_prompt = f"""From: {sender}
Subject: {subject}
Date: {email_meta.get('created_at', 'unknown')}

Email body:
---
{body}
---{context_str}

Reply as Dross. Address Amre directly. No preamble."""

    data = {
        'model': MINIMAX_MODEL,
        'max_tokens': 600,
        'system': DROSS_SYSTEM,
        'messages': [{'role': 'user', 'content': user_prompt}],
    }
    result = curl_json('POST', MINIMAX_URL, MINIMAX_KEY, data)
    if '_error' in result:
        raise RuntimeError(f'minimax error: {result["_error"]}')
    parts = result.get('content', [])
    text = ''
    for p in parts:
        if p.get('type') == 'text':
            text += p.get('text', '')
    # Strip any leading "Reply:" labels the model might add
    text = re.sub(r'^(Reply:?\s*|Here.s the reply:?\s*|Email reply:?\s*)', '', text.strip(), flags=re.IGNORECASE)
    return text.strip()


def process(msg_id, context=None, send=True):
    full = get_full_message(msg_id)
    if '_error' in full:
        return {'msg_id': msg_id, 'error': full['_error'][:200]}
    body = full.get('extracted_text', '') or full.get('text', '') or ''
    if not body.strip():
        # Empty body — just mark seen, skip
        mark_seen(msg_id)
        return {'msg_id': msg_id, 'skipped': 'empty body'}

    # Reply cache: persist generated replies so the cron doesn't burn LLM tokens
    # on every retry while the AgentMail rate limit is hot. Cache expires 7 days.
    cache_dir = os.path.expanduser('~/.openclaw/workspace/.dross-reply-cache')
    cache_path = os.path.join(cache_dir, f'{msg_id.replace("/", "_").replace("<", "").replace(">", "").replace("@", "_at_")}.json')
    cached_data = None
    reply_text = None
    if os.path.exists(cache_path):
        try:
            cached_data = json.load(open(cache_path))
            age_days = (datetime.now().timestamp() - cached_data.get('ts', 0)) / 86400
            if age_days < 7:
                reply_text = cached_data.get('reply')
            else:
                cached_data = None
        except (json.JSONDecodeError, KeyError):
            cached_data = None

    # ── ACTION LAYER: detect and execute commands in the email body ──
    # This is what makes Dross actually DO things, not just talk.
    action_result = None
    if not cached_data:  # Only re-run action if we're generating fresh
        action_result = run_action(body, timeout=300)
    elif 'action' in cached_data:
        # Reuse cached action result
        action_result = cached_data.get('action')

    # Build context for LLM — include action result if there was one
    if action_result and action_result.get('executed'):
        rc = action_result.get('returncode', '?')
        status = 'SUCCESS' if rc == 0 else f'FAILED (exit {rc})'
        lines = [f"ACTION EXECUTED — {status}"]
        lines.append(f"Command: {action_result.get('command', '?')}")
        lines.append(f"Duration: {action_result.get('duration_seconds', '?')}s")
        if action_result.get('ollama_list'):
            lines.append(f"\nCurrently installed ollama models:\n{action_result['ollama_list'][:500]}")
        out = (action_result.get('output') or '').strip()[:3000] or '(empty)'
        lines.append(f"\nOutput:\n```\n{out}\n```")
        if action_result.get('error'):
            lines.append(f"\nError: {action_result['error']}")
        lines.append("\nReport the actual output to Amre. If FAILED, lead with the error. If SUCCESS, state what was done and any model/artifact that's now available.")
        action_context = '\n'.join(lines)
    elif action_result and action_result.get('skipped_reason'):
        action_context = f"ACTION SKIPPED: {action_result['skipped_reason']}"
    else:
        action_context = None

    full_context = '\n\n'.join(filter(None, [context, action_context]))

    if not reply_text:
        reply_text = generate_dross_reply(full, body, context=full_context)
        # Persist
        os.makedirs(cache_dir, exist_ok=True)
        try:
            json.dump({
                'reply': reply_text,
                'ts': datetime.now().timestamp(),
                'subject': full.get('subject', ''),
                'action': action_result,
            }, open(cache_path, 'w'))
        except Exception:
            pass
    send_status = None
    error_msg = None
    if send:
        sender = full.get('from', '')
        if isinstance(sender, dict):
            sender = sender.get('email', '')
        to_field = full.get('to', [])
        amre_email = 'amrree@gmail.com'
        for t in to_field:
            if isinstance(t, dict) and 'amrree' in t.get('email', ''):
                amre_email = t['email']
        subject = full.get('subject', '(no subject)')
        result = send_reply(amre_email, subject, reply_text, msg_id)
        if '_error' in result:
            send_status = 'failed'
            error_msg = result['_error']
        else:
            send_status = 'sent'
            mark_seen(msg_id)
    else:
        send_status = 'dry_run'
    return {'msg_id': msg_id, 'reply': reply_text, 'status': send_status, 'error': error_msg}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: dross-llm-reply.py <msg_id|->', file=sys.stderr)
        sys.exit(1)
    if sys.argv[1] == '-':
        msg_ids = [line.strip() for line in sys.stdin if line.strip()]
    else:
        msg_ids = [sys.argv[1]]
    context = None
    if '--context' in sys.argv:
        idx = sys.argv.index('--context')
        context = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if '--no-send' in sys.argv:
        send = False
    else:
        send = True
    for mid in msg_ids:
        try:
            r = process(mid, context=context, send=send)
            print(json.dumps(r, indent=2))
        except Exception as e:
            print(json.dumps({'msg_id': mid, 'error': str(e)}, indent=2))
