---
name: agentmail-email
description: Send, read, and reply to Sol's email via AgentMail SDK. Use when processing the inbox, replying to inbound emails, or sending new emails from sol-ai@agentmail.to.
---

# AgentMail Email — Sol Inbox

Inbox: **sol-ai@agentmail.to**  
API key: `~/.openclaw/workspace/secrets/sol-agentmail-api-key.txt`

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

## Shell script trap

Never pass `api_key=***` inline in a shell heredoc — Python sees `***` as a bare word and fails with `SyntaxError`. Write the script to a file first, then execute it:

```bash
# WRONG — SyntaxError
python3 << 'PYEOF'
client = AgentMail(api_key=***
PYEOF

# RIGHT — write to file first
cat > /tmp/script.py << 'PYEOF'
from agentmail import AgentMail
key = open('/path/to/key.txt').read().strip()
client = AgentMail(api_key=key)
PYEOF
python3 /tmp/script.py
```

## Get thread messages

```python
thread = client.inboxes.threads.get(inbox_id, thread_id)
for msg in thread.messages:
    body = getattr(msg, 'body', getattr(msg, 'text', None))
    print(msg.from_, msg.timestamp, msg.subject, body)
```
