#!/usr/bin/env python3
"""
Daily AI/RAG/Memory Briefing
Runs: 07:00 BST daily
Sweeps: GitHub trending, HN front page, key newsletters
Surfaces: 3-5 most interesting items with one-line explanations
Output: Written to /tmp/daily-briefing.txt, sent via AgentMail
"""

import json
import urllib.request
import urllib.error
import time
import re
from datetime import datetime

AGENTMAIL_KEY_PATH = "/Users/amre/.openclaw/workspace/secrets/sol-agentmail-api-key.txt"

def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return ""

def gh_trending():
    """Find AI/LLM/RAG/memory repos trending today"""
    c = fetch("https://github.com/trending?since=daily", timeout=15)
    if not c:
        return []
    
    repos = []
    # Parse repo blocks
    items = re.findall(r'<h2[^>]*><a[^>]*href="(/[^"]+)"[^>]*>([^<]+)</a>.*?<p[^>]*>([^<]+)', c, re.DOTALL)
    for href, name, desc in items[:30]:
        href = href.strip('/')
        desc = re.sub(r'<[^>]+>', '', desc).strip()
        keywords = ['rag', 'memory', 'llm', 'ai', 'agent', 'ollama', 'embed', 'vector', 
                    'context', 'chunk', 'retriev', 'local', 'model', 'inference', 'cuda',
                    'context', 'window', 'prompt', 'tuning', 'fine-tun']
        name_str = (name + ' ' + desc).lower()
        if any(k in name_str for k in keywords):
            url = f"https://github.com/{href}"
            repos.append((name.strip(), desc[:120], url))
    
    return repos[:5]

def hn_top():
    """Find AI-adjacent items on HN front page"""
    try:
        ids = json.loads(fetch("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10))[:30]
        items = []
        for i in ids:
            try:
                item = json.loads(fetch(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=8))
                title = item.get('title', '')
                keywords = ['ai', 'llm', 'rag', 'memory', 'local', 'ollama', 'model', 'agent',
                           'embedding', 'vector', 'context', 'inference', 'gpt', 'inference']
                if any(k in title.lower() for k in keywords):
                    items.append((title[:120], item.get('url', f"https://news.ycombinator.com/item?id={i}")))
            except:
                pass
            time.sleep(0.1)
        return items[:5]
    except:
        return []

def main():
    today = datetime.now().strftime("%Y-%m-%d %H:%M BST")
    output = []
    output.append(f"🤖 AI/RAG/MEMORY BRIEFING — {today}\n")
    output.append("=" * 50)
    
    # GitHub trending
    gh = gh_trending()
    if gh:
        output.append("\n📦 GITHUB TRENDING — AI/LLM/MEMORY\n")
        for name, desc, url in gh:
            output.append(f"  • {name}")
            output.append(f"    {desc}")
            output.append(f"    {url}\n")
    
    # HN
    hn = hn_top()
    if hn:
        output.append("\n📰 HACKER NEWS — AI ADJACENT\n")
        for title, url in hn:
            output.append(f"  • {title}")
            output.append(f"    {url}\n")
    
    output.append("\n---\nDross compiled this. Your dyslexia patch. 🤖")
    
    body = '\n'.join(output)
    
    # Save locally
    with open('/tmp/daily-briefing.txt', 'w') as f:
        f.write(body)
    
    # Send to Amre via AgentMail
    try:
        import sys
        sys.path.insert(0, '/opt/homebrew/lib/python3.14/site-packages')
        from agentmail import AgentMail
        key = open(AGENTMAIL_KEY_PATH).read().strip()
        client = AgentMail(api_key=key)
        
        client.inboxes.messages.send(
            inbox_id='sol-ai@agentmail.to',
            to=['[REDACTED-RECIPIENT]'],
            subject=f'AI/RAG/Memory Briefing — {datetime.now().strftime("%Y-%m-%d")}',
            text=body
        )
        print(f"Briefing sent at {today}")
    except Exception as e:
        print(f"Failed to send: {e}")
    
    print(body)

if __name__ == '__main__':
    main()
