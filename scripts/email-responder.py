#!/usr/bin/env python3
"""
Sol Email Worker — runs as a subprocess, handles all email for sol-ai@agentmail.to
Usage: email-responder.py <inbox_id> <api_key_file>
"""
import json
import subprocess
import sys
import os
from datetime import datetime

def get_key(path):
    with open(path) as f:
        return f.read().strip()

def curl_get(url, key):
    result = subprocess.run(
        ['curl', '-s', url, '-H', f'Authorization: Bearer {key}'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def curl_post(url, key, data):
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', url,
         '-H', f'Authorization: Bearer {key}',
         '-H', 'Content-Type: application/json',
         '-d', json.dumps(data)],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def get_full_message(inbox_id, msg_id, key):
    return curl_get(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/{msg_id}',
        key
    )

def send_reply(inbox_id, to_email, subject, text, in_reply_to, key):
    reply_subject = subject if subject.startswith('Re: ') else f'Re: {subject}'
    return curl_post(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send',
        key,
        {
            'to': [to_email],
            'subject': reply_subject,
            'text': text,
            'in_reply_to': in_reply_to
        }
    )

def mark_seen(inbox_id, msg_id, key):
    curl_post(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/{msg_id}',
        key,
        {'labels': ['received', 'seen']}
    )

def main():
    inbox_id = sys.argv[1]
    key_file = sys.argv[2]
    key = get_key(key_file)

    # Fetch inbox state
    result = curl_get(
        f'https://api.agentmail.to/v0/inboxes/{inbox_id}/messages?limit=20',
        key
    )

    messages = result.get('messages', [])
    print(f'[{datetime.now().isoformat()}] {inbox_id}: {len(messages)} messages')

    replied_count = 0
    for msg in messages:
        labels = list(msg.get('labels', []))
        is_unread = 'unread' in labels or ('received' in labels and 'seen' not in labels)
        is_sent = 'sent' in labels

        # Skip sent messages
        if is_sent:
            continue

        msg_id = msg.get('message_id')
        thread_id = msg.get('thread_id')
        subject = msg.get('subject', '(no subject)')
        from_field = msg.get('from_', '')

        # Extract sender email
        if isinstance(from_field, str):
            # Format: "Name <email@domain.com>" or just "email@domain.com"
            if '<' in from_field:
                sender_email = from_field.split('<')[1].rstrip('>').strip()
            else:
                sender_email = from_field.strip()
        elif isinstance(from_field, dict):
            sender_email = from_field.get('email', 'unknown')
        else:
            sender_email = 'unknown'

        if sender_email == 'unknown':
            print(f'  SKIP {msg_id[:40]}... — unknown sender')
            continue

        # Get full message body
        full = get_full_message(inbox_id, msg_id, key)
        body = full.get('extracted_text') or full.get('text') or ''

        # Skip very short/uninformative messages
        if len(body.strip()) < 3:
            print(f'  SKIP {msg_id[:40]}... — empty')
            mark_seen(inbox_id, msg_id, key)
            continue

        # Detect if this is from Dross or another agent
        is_from_dross = 'thedross@agentmail.to' in sender_email

        # Generate reply based on sender and content
        if is_from_dross:
            reply_text = f"Received. All good on this end. — Sol ⚡"
        else:
            # Generic acknowledgment for unknown senders
            reply_text = f"Hi — Sol here. Got your message and will review shortly. — Sol ⚡"

        print(f'  REPLYING to {sender_email}: {subject[:50]}')
        try:
            send_reply(inbox_id, sender_email, subject, reply_text, msg_id, key)
            replied_count += 1
        except Exception as e:
            print(f'  ERROR: {e}')

        # Mark as seen
        mark_seen(inbox_id, msg_id, key)

    print(f'[{datetime.now().isoformat()}] {inbox_id}: done. Replied: {replied_count}')

if __name__ == '__main__':
    main()
