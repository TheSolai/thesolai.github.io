---
name: agentmail-email
description: Send, read, and reply to Sol's email via AgentMail SDK. Use when processing the inbox, replying to inbound emails, or sending new emails from sol-ai@agentmail.to.
---

# AgentMail Email — Sol Inbox

Inbox: **sol-ai@agentmail.to**  
API key: `~/.openclaw/workspace/secrets/sol-agentmail-api-key.txt`

## Two inboxes — never confuse them

| Inbox | Owner | Consumer |
|---|---|---|
| `sol-ai@agentmail.to` | Sol | `Sol — Email Watch` cron, Sol's autonomous handler |
| `thedross@agentmail.to` | Dross | `Dross Email — Autonomous Handler` cron |

One API key reaches both inboxes, so a wrong `inbox_id` does not error — it silently returns the other inbox's mail. Always pass the inbox the consumer was registered against, and confirm the target in the cron's own argv before changing it.

```bash
openclaw cron list --json | grep -o "agentmail.to"
```

## Python SDK (preferred over curl)

```python
from agentmail import AgentMail
key = open('/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt').read().strip()
client = AgentMail(api_key=key)
inbox_id = 'sol-ai@agentmail.to'
```

## List messages

```python
result = client.inboxes.messages.list(inbox_id=inbox_id, limit=50)
for m in result.messages:
    print(m.message_id, m.thread_id, m.subject, m.labels, m.timestamp, m.from_, m.preview[:100])
```

Returns `ListMessagesResponse` — iterate `.messages`. Never subscript with `result[0]`.

## Reply to a message — message_id vs thread_id

```python
# CRITICAL: reply() takes message_id as first argument, NOT thread_id
reply = client.inboxes.messages.reply(inbox_id, message_id, text="Reply text here")
print(reply.message_id)  # confirms it sent
```

**`message_id` ≠ `thread_id`**. Passing `thread_id` returns HTTP 404 NotFoundError. Always use the `message_id` field from the list output. `message_id` looks like `<CAO=qJ6R...@gmail.com>` or `<010001a0...@email.amazonses.com>`; `thread_id` is a UUID like `f61b0be7-84e0-4214-a3be-8e8e4cd9314a`.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `HTTP 404` on reply | `thread_id` passed instead of `message_id` | Use `.message_id` from the list response |
| `HTTP 401` | API key wrong or revoked | Rotate at agentmail.to |
| `AttributeError` on list response | Wrong attribute name | Iterate `result.messages` — it has no `.items` |
| `TypeError` on a message object | Wrong field name | `getattr(msg, 'body', getattr(msg, 'text', None))` |

## Get full message body

```python
# messages.get() requires the exact message_id string from the list endpoint
msg = client.inboxes.messages.get(inbox_id, message_id)
print(msg.body)
```

## Send a new email

```python
send = client.inboxes.messages.send(
    inbox_id,
    to=['recipient@example.com'],
    subject='Subject',
    text='Body'
)
```

## Search all pages (30+ day history)

The API returns messages in reverse-chronological order with a page token. Use pagination to reach older messages:

```python
all_msgs = []
page_token = None
while True:
    result = (client.inboxes.messages.list(inbox_id=inbox_id, limit=50, page_token=page_token)
              if page_token
              else client.inboxes.messages.list(inbox_id=inbox_id, limit=50))
    for m in result.messages:
        all_msgs.append(m)
    if result.next_page_token:
        page_token = result.next_page_token
    else:
        break
```

Then filter by date or sender:
```python
from datetime import datetime, timezone, timedelta
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
for m in all_msgs:
    if m.timestamp >= cutoff:
        print(m.from_, m.subject, m.timestamp)
```

## Shell script traps for engagement scripts

### The `***` heredoc trap

Never pass `api_key=***` inline in a shell heredoc — Python sees `***` as a bare word and fails with `SyntaxError`. Read the key from file inside the heredoc instead:

```bash
# WRONG — SyntaxError: invalid character
python3 << 'PYEOF'
from agentmail import AgentMail
client = AgentMail(api_key=***)  # *** is a bare word in Python!
PYEOF

# RIGHT — single-quoted heredoc, read key inside
python3 << 'PYEOF'
from agentmail import AgentMail
key = open('/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt').read().strip()
client = AgentMail(api_key=key)
PYEOF
```

### The Python path trap

System python (`/usr/bin/python3`) lacks the `agentmail` module. Always use the Homebrew python:

```bash
# WRONG — wrong python, ModuleNotFoundError
python3 << 'PYEOF'
from agentmail import AgentMail  # fails
PYEOF

# RIGHT — explicit Homebrew python
/opt/homebrew/bin/python3 << 'PYEOF'
from agentmail import AgentMail  # works
PYEOF
```

Or add it to PATH at the top of the bash script:

```bash
#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
```

### State file directory must be created first

If your script writes to a state file, create the directory before the python heredoc runs (bash runs before the heredoc):

```bash
SEEN="/Users/amre/.openclaw/workspace/scripts/engagement/state/seen_ids.txt"
mkdir -p "$(dirname "$SEEN")"  # creates dir BEFORE python runs

/opt/homebrew/bin/python3 << 'PYEOF'
import os
seen_ids = set()
seen_file = '/Users/amre/.openclaw/workspace/scripts/engagement/state/seen_ids.txt'
if os.path.exists(seen_file):
    with open(seen_file) as f:
        seen_ids = set(line.strip() for line in f if line.strip())
PYEOF
```

### Announce-mode cron: print to stdout, don't curl Telegram

When a cron is registered with `--announce`, OpenClaw reads its stdout and delivers to Telegram. Never send Telegram messages directly via curl:

```bash
# RIGHT — print to stdout, OpenClaw handles delivery
if [[ ${#new_important[@]} -gt 0 ]]; then
    echo "📧 New email — don't reply yet"
    for item in "${new_important[@]}"; do
        echo "From: ${item['from']}"
    done
fi
# Exit 0 — "nothing to say" is not an error, suppresses error noise in logs
exit 0
```

`ok (suppressed)` in cron status means the cron ran successfully but printed nothing — that is correct behavior.

## Get thread messages

```python
thread = client.inboxes.threads.get(inbox_id, thread_id)
for msg in thread.messages:
    body = getattr(msg, 'body', getattr(msg, 'text', None))
    print(msg.from_, msg.timestamp, msg.subject, body)
```

## Email reply quality standard

When asked to reply to a message:

1. **Read the full thread** — fetch the body via `thread.get()`, not just the preview.
2. **Identify what the sender actually asked or offered.**
3. **Correct factual errors** in earlier replies, including attribution ("Sol" vs "Sol + Annmarie").
4. **Answer the specific question** with substantive content — something worth receiving.
5. **Include a right-of-reply paragraph** when quoting or attributing Sol publicly.
6. **Confirm the send** to Amre: who was replied to, and in what language.

A generic acknowledgment is not a reply. Verify the send by printing `reply.message_id`.

## Cron pre-registration check for email monitors

Before registering an email-monitoring cron:

1. **Confirm the script finds messages in the target `inbox_id`** — a wrong inbox returns zero messages, not an error.
2. **Run the full script standalone** and confirm it produces non-empty output.
3. **Deregister immediately if it delivers blank messages** — `openclaw cron rm <cron-id>` (the id, not the display name).

An empty-output cron provides no value and only makes noise.
