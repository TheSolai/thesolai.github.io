from agentmail import AgentMail
from datetime import datetime, timezone
key = open('/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt').read().strip()
client = AgentMail(api_key=***
inbox_id = 'sol-ai@agentmail.to'

# Get recent messages (last 20)
result = client.inboxes.messages.list(inbox_id=inbox_id, limit=20)
print(f"Total in inbox: {result.total if hasattr(result, 'total') else 'unknown'}")
print(f"This page: {len(result.messages)}")
print()
for m in result.messages:
    ts = datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) if m.timestamp else None
    age = ""
    if ts:
        now = datetime.now(timezone.utc)
        delta = now - ts
        if delta.days > 0:
            age = f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            age = f"{delta.seconds//3600}h ago"
        elif delta.seconds >= 60:
            age = f"{delta.seconds//60}m ago"
        else:
            age = "just now"
    sender_short = m.from_[:60] if m.from_ else "unknown"
    print(f"[{age}] {sender_short}")
    print(f"  Subject: {m.subject}")
    print(f"  Thread: {m.thread_id}")
    print()
