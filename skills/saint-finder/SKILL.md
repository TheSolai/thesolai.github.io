---
name: saint-finder
description: Find the patron saint for any need, illness, or difficulty, and talk to that saint about it. Use whenever someone mentions a worry, a need, an illness, a decision, a relationship, a loss, a job, an exam, or asks "which saint", "patron saint", "who should I pray to", or "saint for".
homepage: https://thesolai.github.io
metadata: {"clawdbot":{"emoji":"✝️","requires":{"bins":["curl"]}}}
---

# Saint Finder

The StFinder engine — 87 saints, 240 patronages, a curated synonym map — runs
as a persistent service on this machine. Ask it anything; it matches a need to
saints and holds a conversation with them.

## The one call that matters

```bash
curl -s -X POST http://127.0.0.1:8787/api/chat \
  -H 'content-type: application/json' \
  -d '{"text":"THE NEED IN PLAIN WORDS"}'
```

Returns `{"text": "...", "buttons": [[{"label":"…","data":"…"}]]}`.

Reply to the user with the **`text`** field as the bot's answer, and offer the
`buttons` as suggestions the user can pick (render them as a short list of the
`label` values, or as inline buttons if the channel supports them).

## Continuing a conversation with one saint

When the user picks a saint — the button `data` is `s:<saintId>` — open the
conversation:

```bash
curl -s -X POST http://127.0.0.1:8787/api/callback \
  -H 'content-type: application/json' \
  -d '{"data":"s:anthony-padua"}'
```

Then every follow-up message goes to the same endpoint as a normal message,
with a **session key** so the conversation is remembered:

```bash
curl -s -X POST "http://127.0.0.1:8787/api/chat?session=USER_ID" \
  -H 'content-type: application/json' \
  -d '{"text":"what do you look after"}'
```

Use a stable `session` per user (their Telegram id, or a hash of it) so
conversations persist across turns.

## The action buttons

Buttons returned with `q:` prefixes are the saint speaking:

| `data` | Effect |
|---|---|
| `q:pray` | the saint's prayer, to pray together |
| `q:story` | the saint's biography |
| `q:patronage` | what they are patron of |
| `q:feast` | their feast day |
| `q:reflect` | a reflection prompt |
| `b:back` | back to finding saints |
| `p:<prompt>` | an opening prompt — treat as the need itself |

## Commands the bot understands

`/start` · `/saint <name>` · `/today` · `/saints` · `/new` · `/help`

## If the service is down

```bash
bash /Users/amre/Documents/StFind/scripts/deploy-saint-bot.sh
```

That rebuilds, redeploys and reloads the launchd agent. Check with:

```bash
curl -s http://127.0.0.1:8787/api/health
```

## Rules for the tone

The bot already speaks in the voice of the saints — plain, warm, scriptural,
never clinical, never preachy. **Relay its `text` essentially as written.**
Do not summarise it into corporate mush, do not add "I hope this helps", and
do not editorialize about the match. The match reasons it gives ("for
Dentists, Teeth") are the useful part — keep them.

Do not invent saints, patronages, or feast days. Everything comes from the
engine. If the engine returns ten saints, present ten; if the user wants one,
give the top match and offer to narrow.
