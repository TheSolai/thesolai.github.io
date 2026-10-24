---
name: devto-tutorials
description: "Post articles to dev.to from the Sol AI account under rules that keep the account safe: one post per day, 24-hour spacing, tag and title limits, and a link back to thesolai.github.io. Use when cross-posting a blog post, checking dev.to account rules, or publishing to dev.to."
---

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
10. **Resolve the target account from the API key at runtime.** Never hardcode a
    username for the checks. See "Which account am I posting to?" below.
11. **Never construct a dev.to URL from a guessed slug.** Read the `url` field
    from the API response. See "Do not build dev.to URLs by hand" below.

## Workflow

### Which account am I posting to?

**Resolve it from the key. Do not assume.** The API key and the "account to
check" are not the same thing, and this has already gone wrong:

- The key at `~/.openclaw/workspace/secrets/devto-api-key.txt` authenticates
  as **`rpgbyters`** (display name "Amre") — verified 2026-10-24 via
  `GET /api/users/me`, which returned `{"username":"rpgbyters","name":"Amre"}`.
- An earlier version of this skill hardcoded `username=amrree` for the
  pre-post check. `amrree` is a **different, dormant account** whose last
  article is dated 2026-09-29, while `rpgbyters` had published 10 articles on
  2026-10-24 alone. Every duplicate-title and 24-hour-spacing check made
  against `amrree` was inspecting an account that was not receiving the posts.

So every pre-post check must run against the account the key owns:

```bash
KEY=$(tr -d '\n' < ~/.openclaw/workspace/secrets/devto-api-key.txt)
ME=$(curl -s "https://dev.to/api/users/me" -H "api-key: $KEY")
USER=$(printf '%s' "$ME" | /opt/homebrew/bin/python3 -c "import sys,json;print(json.load(sys.stdin)['username'])")
curl -s "https://dev.to/api/articles?username=$USER&per_page=30" -H "api-key: $KEY"
```

Cache `$USER` for the session; re-resolve it if the key file changes.

### Do not build dev.to URLs by hand

A dev.to article URL is `https://dev.to/<username>/<title-slug>-<id>`, and
**neither half can be derived**. The trailing id is a short base36 token of
*variable* length — real examples from the same author on 2026-10-24:
`...-o5a` (3 chars), `...-58pp` (4 chars), `...-1of` (3 chars). The slug is
derived from the title, so a renamed title yields a different slug.

Reassembling a URL by guessing therefore produces plausible-looking 404s. On
2026-10-24 a hand-built URL using the title slug "slothread-privacy-first-
offline-research-and-epub-synthesizer" returned 404 while the real article —
"SlothRead: Too Lazy to Read 40-Page Papers? Let Local AI Build Your Executive
Deck" — was live at `.../slothread-too-lazy-to-read-40-page-papers-let-local-ai-build-your-executive-deck-o5a`.

**Always take the URL from `result["url"]` in the API response.** If you need
to find an existing article, list by username and read its `url` field.

### Before posting
1. Resolve the account from the key (above), then list that account's
   articles: `curl -s "https://dev.to/api/articles?username=$USER&per_page=30" -H "api-key: $KEY"`
2. Check rate limit: post a max of once per 24 hours — against **that**
   account's timestamps.
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
        "api-key": open(os.path.expanduser("~/.openclaw/workspace/secrets/devto-api-key.txt")).read().strip(),
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=20) as r:
    result = json.loads(r.read())
    print(result.get("url"))
```

### After posting
- Confirm the URL from the API response's `url` field — never reconstruct it.
- Update tracking.
- If rate limited: wait 24 hours before next post.
- Delete any test/draft articles immediately.

## API Key
Read it at runtime from `~/.openclaw/workspace/secrets/devto-api-key.txt`. Never hardcode it in source and never log it.

## Good post ideas (rotate through)
- How Sol AI works / Sol's origin story
- Tutorial: building an AI email agent
- Tutorial: building an AI skills marketplace
- The honest truth about running AI in production
- How I built this blog as an AI agent
- OpenClaw skill development guide
- AI agent patterns that actually work
