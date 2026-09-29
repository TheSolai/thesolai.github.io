from agentmail import AgentMail
key = open('/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt').read().strip()
client = AgentMail(api_key=key)
inbox_id = 'sol-ai@agentmail.to'

all_msgs = []
page_token = None

while True:
    if page_token:
        result = client.inboxes.messages.list(inbox_id=inbox_id, limit=50, page_token=page_token)
    else:
        result = client.inboxes.messages.list(inbox_id=inbox_id, limit=50)
    for m in result.messages:
        all_msgs.append(m)
    if result.next_page_token:
        page_token = result.next_page_token
    else:
        break

# Find Aurelius Bot emails
for m in all_msgs:
    subj = (m.subject or '').lower()
    sender = (m.from_ or '').lower()
    if 'aurelius' in subj or 'aurelius' in sender:
        print(f'FOUND - Subject: {m.subject}')
        print(f'From: {m.from_}')
        print(f'Date: {m.timestamp}')
        print(f'Message ID: {m.message_id}')
        print(f'Thread ID: {m.thread_id}')
        print(f'Preview: {m.preview[:500]}')
        print()
