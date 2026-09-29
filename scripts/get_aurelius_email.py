from agentmail import AgentMail
key = open('/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt').read().strip()
client = AgentMail(api_key=key)
inbox_id = 'sol-ai@agentmail.to'

# Aurelius Bot - get thread to see full conversation
thread_id = '54500a7e-c6c5-4e39-bd4a-f4f5324ab987'
thread = client.inboxes.threads.get(inbox_id, thread_id)
print(f'Thread messages: {len(thread.messages) if hasattr(thread, "messages") else "?"}')
for msg in (thread.messages if hasattr(thread, "messages") else []):
    print(f'\n=== From: {msg.from_} ===')
    print(f'=== Date: {msg.timestamp} ===')
    print(f'=== Subject: {msg.subject} ===')
    body = msg.body if hasattr(msg, 'body') else getattr(msg, 'text', getattr(msg, 'content', 'NO BODY'))
    print(body)
    print('---')
