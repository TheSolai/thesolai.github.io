---
name: sol-email
description: Send, read, and reply to emails via AgentMail API using curl
---

# Sol Email — AgentMail API

You have access to the AgentMail email API. Your inbox is **sol-ai@agentmail.to**.
Your API key is in `secrets/sol-agentmail-api-key.txt`.

## API Setup

```bash
export AGENTMAIL_KEY=$(cat ~/.openclaw/workspace/secrets/sol-agentmail-api-key.txt | tr -d '\n')
export INBOX_ID="sol-ai@agentmail.to"
export API_BASE="https://api.agentmail.to/v0"
```

## Send an Email

```bash
curl -s -X POST "$API_BASE/inboxes/$INBOX_ID/messages/send" \
  -H "Authorization: Bearer $AGENTMAIL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Subject line",
    "text": "Body text here."
  }'
```

## List Recent Messages

```bash
curl -s "$API_BASE/inboxes/$INBOX_ID/messages?limit=10" \
  -H "Authorization: Bearer $AGENTMAIL_KEY"
```

## Read a Full Message

```bash
curl -s "$API_BASE/inboxes/$INBOX_ID/messages/MESSAGE_ID" \
  -H "Authorization: Bearer $AGENTMAIL_KEY"
```

Use the `extracted_text` field from the response — it strips quoted reply history.

## Reply to a Message (threaded)

> **Important:** The `/messages/{id}/reply` endpoint does NOT accept Gmail or SES message IDs directly.
> Use the send endpoint with `in_reply_to` and `references` headers instead — this correctly threads the reply.

```bash
# Get the full message first to extract the message_id and thread_id
FULL_MSG=$(curl -s "$API_BASE/inboxes/$INBOX_ID/messages/MESSAGE_ID" \
  -H "Authorization: Bearer $AGENTMAIL_KEY")

# Extract from_: the original sender's email (to find their address)
# Extract the in_reply_to and references from the message headers

curl -s -X POST "$API_BASE/inboxes/$INBOX_ID/messages/send" \
  -H "Authorization: Bearer $AGENTMAIL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["original_sender@email.com"],
    "subject": "Re: Original Subject",
    "text": "Your reply text here.",
    "in_reply_to": "ORIGINAL_MESSAGE_ID",
    "references": ["ORIGINAL_REFERENCES"]
  }'
```

Or more simply: just use the send endpoint with the same subject prefixed `Re: ` and include `in_reply_to: ORIGINAL_MESSAGE_ID` — threading works automatically.

## Mark a Message as Seen

```bash
curl -s -X PATCH "$API_BASE/inboxes/$INBOX_ID/messages/MESSAGE_ID" \
  -H "Authorization: Bearer $AGENTMAIL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"labels": ["seen"]}'
```

## Workflow

1. **List messages** to see what's in the inbox
2. **Read a message** with `messages/MESSAGE_ID` to get full body
3. **Reply** using the original message ID (thread continuity is automatic)
4. **Mark seen** after reading so it doesn't re-appear as new

## Rules
- Always read a message fully before replying — never reply based on preview alone
- Detect the language of the incoming email and reply in the same language
- Keep replies concise and appropriate to the tone (formal/informal)
- Do NOT write a signature — it is added automatically by the API
