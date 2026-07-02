# Dev.to Tutorials — Skill

## What this skill does

Helps post quality articles to dev.to on behalf of Sol AI (thesolai.github.io).

## Rules — follow these or the account gets banned

1. **One post per day maximum.** Never post more than one per day.
2. **Space posts by at least 24 hours.** Check dev.to before posting.
3. **Never automate posting.** Every post must be intentional and thoughtful.
4. **Always link back to thesolai.github.io.** Footer of every post: `Originally published on [Sol AI](https://thesolai.github.io).`
5. **No short throwaway posts.** Minimum 400 words, original content.
6. **No duplicate titles.** Check existing posts before writing.
7. **Title max 128 characters.** Dev.to rejects longer.
8. **Description min 20 characters.** Must be unique per post.
9. **Max 4 tags.** Use relevant tags only.

## Workflow

### Before posting
1. Check existing articles: `curl -s "https://dev.to/api/articles?username=amrree&per_page=30" -H "api-key: <KEY>"`
2. Check rate limit: post a max of once per 24 hours.
3. Verify title is unique and under 128 chars.

### Writing the post
- Open with a hook — don't start with "In this article..."
- Conversational Sol AI voice: direct, slightly wry, honest.
- Structure: Hook → Body → Takeaway. No bullet points in body.
- End with a soft CTA linking back to the site.
- Add `---` divider before footer.

### Posting
```python
import json, urllib.request

payload = {
    "article": {
        "title": "<title ≤128 chars>",
        "body_markdown": "<content>\n\n---\n\n*Originally published on [Sol AI](https://thesolai.github.io).*",
        "tag_list": ["ai", "tutorial", "opensource"],  # max 4
        "description": "<20+ char description>",
        "published": True,
    }
}

req = urllib.request.Request(
    "https://dev.to/api/articles",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "SolAI/1.0",
        "api-key": "SmxPhE8pmiScGnW8SprUCF7U",
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    print(result.get("url"))
```

### After posting
- Confirm URL, update tracking.
- If rate limited: wait 24 hours before next post.
- Delete any test/draft articles immediately.

## API Key
`SmxPhE8pmiScGnW8SprUCF7U` — stored in memory, do not log.

## Good post ideas (rotate through)
- How Sol AI works / Sol's origin story
- Tutorial: building an AI email agent
- Tutorial: building an AI skills marketplace
- The honest truth about running AI in production
- How I built this blog as an AI agent
- OpenClaw skill development guide
- AI agent patterns that actually work
