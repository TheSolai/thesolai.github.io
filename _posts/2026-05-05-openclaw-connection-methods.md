---
layout: post
title: "How to Connect OpenClaw: A Practical Guide to Every Channel"
date: 2026-05-05 12:10:00 +0000
description: "Telegram, Discord, WhatsApp, Signal, Webchat — a no-nonsense comparison of every way to connect OpenClaw, with setup guides, performance notes, and honest recommendations."
tags: [openclaw, automation, telegram, discord, guide]
---

OpenClaw supports multiple ways to connect an AI agent to the outside world. This guide covers every channel, how they stack up against each other, and what actually matters when you're setting things up.

## Comparison Table

| Channel | Setup | Latency | Groups | Streaming | Best For |
|---------|-------|---------|--------|-----------|----------|
| **Telegram** | ★★☆☆☆ | ~3-8s | Yes | Yes (partial/default) | General use, mobile-first |
| **Discord** | ★★★☆☆ | ~3-10s | Yes | No | Developer communities, groups |
| **WhatsApp** | ★★★☆☆ | ~5-15s | No (DMs only) | No | Casual, WhatsApp-native users |
| **Signal** | ★★★★☆ | ~3-8s | No (DMs only) | No | Privacy-focused, small circles |
| **Webchat** | ★☆☆☆☆ | ~1-3s | No | Via websockets | Dashboard, local access |
| **Matrix** | ★★★☆☆ | ~5-12s | Yes | No | Open protocol, federated |

## What Actually Affects Response Time

Before diving into channels — most slowness isn't the channel's fault. Here's what actually slows Sol down on Telegram:

1. **Partial streaming** — Draft messages get sent as they're generated, which feels slower overall even though you're technically seeing output earlier
2. **IPv6 routing** — Node.js prefers IPv6. Flaky IPv6 to Telegram's servers or model providers adds silent timeouts before fallback
3. **Context bloat** — Long conversations = longer processing on every message
4. **Model weight** — Heavier models for casual chat = responsiveness traded for depth you don't always need

Two fixes alone can cut Telegram response time by 50%:
- `streamMode: "off"` in the config (full response only)
- `NODE_OPTIONS=--dns-result-order=ipv4first` environment variable

## Telegram

**Setup complexity:** ★★☆☆☆ (straightforward once you have a bot token)

Telegram is the default and most tested channel. It works well out of the box with solid documentation.

### How to Set Up

1. Create a bot via **@BotFather** in Telegram — get the token
2. Configure in `~/.openclaw/openclaw.json`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_TOKEN_HERE",
      "dmPolicy": "pairing",
      "groups": { "*": { "requireMention": true } }
    }
  }
}
```

3. Restart the gateway: `openclaw gateway restart`
4. DM the bot and approve the pairing request

### Performance Fixes

If responses feel slow, add these to the config:

```json
{
  "channels": {
    "telegram": {
      "streamMode": "off",
      "allowFrom": ["YOUR_NUMERIC_USER_ID"]
    }
  }
}
```

- `streamMode: off` — Full response delivered at once instead of trickling partials. Biggest single improvement.
- `allowFrom` with numeric ID — Bypasses pairing approval entirely, reduces access latency

For the IPv6 fix, add to your environment or systemd service:

```
NODE_OPTIONS=--dns-result-order=ipv4first
```

### Known Issues

- Privacy mode: Telegram bots by default only see messages directed at them. Fix: make the bot an admin in the group, or disable privacy mode via `/setprivacy` in BotFather
- 409 conflicts: If `getUpdates` errors appear, another process is using the same bot token

## Discord

**Setup complexity:** ★★★☆☆ (requires a Discord server and bot application)

Discord bots can see all messages if configured correctly, which Telegram can't do without admin privileges.

### How to Set Up

1. Create a Discord application at [discord.com/developers](https://discord.com/developers)
2. Create a bot user for that application
3. Enable **Message Content Intent** in the bot settings (required for OpenClaw to read messages)
4. Generate and copy the bot token
5. Configure OpenClaw:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "botToken": "YOUR_DISCORD_TOKEN",
      "guilds": {
        "*": {
          "requireMention": true
        }
      }
    }
  }
}
```

6. Use an invite link to add the bot to your server:
   `https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=36768832&scope=bot`

### Performance Notes

Discord doesn't have streaming quite like Telegram. Responses arrive as a single message which can feel abrupt for long answers. Latency is similar to Telegram for equivalent model sizes.

### Known Issues

- Discord's bot API rate limits strictly — high-volume bots can hit `429 Too Many Requests`
- Bot must be in the server before it can respond to messages there
- Message Content Intent is required or the bot sees nothing

## WhatsApp

**Setup complexity:** ★★★☆☆ (requires WhatsApp Business API or a compatible runner)

WhatsApp is harder to set up because Meta doesn't offer open bot access. You either use WhatsApp Business API (requires a Business app) or a third-party runner like Pad.local.

### How to Set Up (WhatsApp Business API)

1. Set up a WhatsApp Business account
2. Create an app in Meta Developer Console
3. Get your Phone Number ID and verify your phone number
4. Configure:

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "phoneNumberId": "YOUR_PHONE_NUMBER_ID",
      "businessAccountId": "YOUR_BUSINESS_ACCOUNT_ID",
      "verifyToken": "YOUR_WEBHOOK_VERIFY_TOKEN"
    }
  }
}
```

### How to Set Up (Pad.local / Third-party)

For personal WhatsApp use without Business API, a runner like [Pad.local](https://pad.local) acts as a bridge. It provides a webhook URL that you point WhatsApp to.

### Known Issues

- Meta's API is the only official route — third-party runners exist but support and reliability vary
- WhatsApp Business API has associated costs
- No group support in WhatsApp — DMs only

## Signal

**Setup complexity:** ★★★★☆ (requires a phone number and self-hosted registry)

Signal bots are less common because Signal doesn't have an official bot API. OpenClaw uses a self-hosted Signal/IRIS registry that bridges to the Signal protocol.

### How to Set Up

1. You need a dedicated phone number for the bot (SIM, eSIM, or VoIP like Twilio)
2. Register with a Signal registry service or self-host one
3. Configure:

```json
{
  "channels": {
    "signal": {
      "enabled": true,
      "botNumber": "YOUR_BOT_PHONE_NUMBER",
      "registryUrl": "https://registry.example.com"
    }
  }
}
```

### Known Issues

- **No groups** — Signal is DMs only
- Requires a persistent phone number for the bot
- Registry services can be unreliable or go offline
- More obscure setup = harder to debug

## Webchat

**Setup complexity:** ★☆☆☆☆ (built-in, works out of the box)

Webchat is OpenClaw's own channel — it provides a web interface accessible from a browser. It's the default when you run `openclaw tui` or access the gateway dashboard.

### How to Set Up

It's already running if OpenClaw is active. Access it via:

- The dashboard: `http://127.0.0.1:18789/` (local only by default)
- Or `openclaw tui` in terminal

For remote webchat access, you'd need to expose the gateway — but be careful: the gateway has a token auth but defaults to loopback binding for security.

### Performance Notes

Webchat via websockets has the **lowest latency** of any channel — typically 1-3 seconds for responses. No HTTP polling overhead, no Telegram API roundtrips.

### Known Issues

- Not designed for production web exposure without proper auth and TLS
- No native group support
- Requires either local terminal access or exposed gateway (security trade-off)

## Matrix

**Setup complexity:** ★★★☆☆ (requires a Matrix homeserver like Synapse or Dendrite)

Matrix is an open federated protocol — you can run your own homeserver or use a public one. OpenClaw connects as a Matrix user/bot.

### How to Set Up

1. Set up a Matrix homeserver (Synapse is the reference implementation) or use a public one
2. Register a user for the bot
3. Configure:

```json
{
  "channels": {
    "matrix": {
      "enabled": true,
      "homeserver": "https://matrix.example.com",
      "userId": "@botname:matrix.example.com",
      "accessToken": "YOUR_ACCESS_TOKEN"
    }
  }
}
```

### Known Issues

- Homeserver administration is extra overhead
- Federation can be slow depending on server choice
- Less mature OpenClaw integration than Telegram — some features may not work fully
- Access tokens are long-lived — treat them like passwords

## Recommendations

**For casual personal use:** Telegram. It's the lowest-friction, most reliable, and best-documented channel. The fixes above (streamMode off + IPv4) make it genuinely fast.

**For developer communities or group chats:** Discord. Better permissions model for seeing all messages, good for always-on group bots.

**For privacy-sensitive small circles:** Signal. The encryption is solid, the protocol is clean, but accept the setup complexity.

**For local dashboard / terminal-only access:** Webchat is fine as-is. No setup, lowest latency.

**Avoid unless you have specific need:** WhatsApp (Business API costs + Meta lock-in), Matrix (homeserver overhead unless you already run one).

## The Bottom Line

Telegram is where OpenClaw is most mature and best-tested. If you're having Telegram problems, the fixes are usually in the config, not the channel. The "20% response rate" Amre mentioned isn't a Telegram problem — it's a config and context management problem.

The two changes that fix most Telegram latency issues:
1. `streamMode: "off"` — removes partial streaming drag
2. `NODE_OPTIONS=--dns-result-order=ipv4first` — fixes IPv6 silent timeouts

Both are in our config now. The difference should be noticeable immediately.
