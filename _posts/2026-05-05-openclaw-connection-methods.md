---
layout: post
title: "How to Connect OpenClaw to Any Chat Platform"
date: 2026-05-05
description: "A practical breakdown of every connection method — Telegram, Discord, WhatsApp, Signal, Matrix, and Webchat. Setup complexity, latency, features, and what each one is actually good for."
tags: [openclaw, setup, telegram, discord, whatsapp, signal, matrix, webchat]
---

OpenClaw connects to your AI agent through chat platforms you already use. No new app to learn, no separate UI to maintain. You just message it wherever you're already messaging.

This guide covers the six most relevant connection methods: Telegram, Discord, WhatsApp, Signal, Matrix, and Webchat. For each one I've documented what it actually is, how hard it is to set up, how fast it responds, what features you get, and where it falls short.

**The short version if you don't want to read the whole thing:** Telegram is the fastest to set up and most reliable for most people. Discord is best if you want a multi-channel workspace. WhatsApp is best if you need to reach someone who won't install anything new. Signal is for when privacy is non-negotiable. Matrix is for self-hosted enthusiasts. Webchat is for quick local testing or embedding in a site.

---

## Comparison Table

| Channel   | Setup Complexity | Latency    | DMs | Groups | Streaming | Media | Best For |
|-----------|-----------------|------------|-----|--------|-----------|-------|----------|
| **Telegram** | 2/5 | ~200-500ms | Yes | Yes | Partial (edit-based) | Photos, video, audio, files | Most users; fastest setup |
| **Discord** | 3/5 | ~300-800ms | Yes | Yes | No (final only) | Photos, video, audio, files, embeds | Multi-channel workspace |
| **WhatsApp** | 3/5 | ~500ms-2s | Yes | Yes | No | Photos, video, audio, voice notes | Reaching non-technical users |
| **Signal** | 4/5 | ~500ms-2s | Yes | Yes | No | Photos, video, audio, files | Privacy-first users |
| **Matrix** | 4/5 | ~500ms-1.5s | Yes | Yes | Opt-in | Photos, video, audio, files, E2EE | Self-hosted, federation |
| **Webchat** | 2/5 | ~100-300ms | No | No | Yes (native WebSocket) | None | Local testing, embedded UI |

---

## Telegram

Telegram is the default recommendation for most OpenClaw users. It's production-ready via the grammY framework, has the cleanest setup process, and reliably delivers messages.

### What it is

Telegram is a cloud-based messaging app with a mature Bot API. OpenClaw connects using a bot token you get from @BotFather. The bot lives in the cloud — Telegram handles the message delivery and OpenClaw processes them. This means your gateway needs to be reachable from the internet, or you use webhook mode to receive messages without maintaining an outbound connection.

### Setup complexity

Two out of five stars. You create a bot in @BotFather, paste the token into your config, start the gateway, and approve the first DM via pairing. That's it. The only friction is finding your own Telegram user ID if you want to use allowlist mode instead of pairing. Everything else is copy-paste from the docs.

### Latency and performance

Telegram has two modes: **long polling** (default) and **webhook**. Long polling keeps a persistent connection open to Telegram's API and pulls new messages as they arrive. Typical round-trip latency is 200–500ms for the network path plus whatever your LLM takes to respond.

**Webhooks are technically faster** in absolute terms — messages arrive the moment Telegram POSTs them to your server rather than on the next poll cycle. In practice, the difference is negligible for most use cases (under 100ms at best). Webhooks add operational complexity: you need a publicly reachable HTTPS endpoint, proper TLS certificate setup, and webhook secret validation. Long polling is simpler and works fine for personal bots at any scale most people would actually run.

The OpenClaw docs explicitly state long polling is the default mode and webhook is optional. For personal use or even moderate traffic bots, long polling is fine. Switch to webhooks only if you're running high-volume bots and have already optimized everything else.

### Features

Telegram supports DMs, groups, supergroups, and forum topics. Streaming partial responses back as edits is supported — OpenClaw uses `editMessageText` to update a preview message in real time as the model generates output. This works in both DMs and groups. Media support is comprehensive: photos, videos, audio, voice notes, documents. You can configure `requireMention: false` to have the bot respond to everything in a group, or require explicit @mention to keep it quiet until summoned.

Access control is done via `dmPolicy` (pairing, allowlist, open, or disabled) and `groupPolicy` for server-side sender filtering. Pairing is the default — unknown senders get a one-time code they need approved before the bot responds to them.

### Known issues

Telegram bots default to Privacy Mode, which means they can only see messages directed at them. If you want the bot to read all messages in a group (for context or moderation), you need to disable privacy mode via `/setprivacy` in BotFather or make the bot an admin. When you toggle privacy mode, you must remove and re-add the bot to each group for Telegram to apply the change.

`dmPolicy: "open"` with `allowFrom: ["*"]` lets anyone who finds your bot command it. Don't do this for personal bots. Use `allowlist` with your numeric user ID instead.

### Best for

Personal AI assistants, small team bots, any setup where you want the lowest friction and most reliable experience. If you're new to OpenClaw, start here.

---

## Discord

Discord is the choice if you want your AI agent to live inside a community space — multiple channels, different contexts per channel, and the ability to build a proper workspace.

### What it is

Discord bots connect via the official Discord gateway using a bot token. Your OpenClaw gateway acts as a WebSocket client connecting to Discord's gateway, receiving events (messages, reactions, member updates) and responding back through the API.

### Setup complexity

Three out of five stars. The Discord Developer Portal setup is more involved than Telegram because you need to configure OAuth2 scopes, set privileged gateway intents, generate an invite URL, and get your server and user IDs. None of it is technically difficult, but there's more clicking and more things that can go wrong. The OpenClaw docs walk through every step. Plan for 15–20 minutes the first time.

### Latency and performance

Discord uses a persistent WebSocket connection. Event delivery latency is typically 300–800ms for the Discord→gateway path. This is comparable to Telegram long polling. Discord does not support streaming edits the way Telegram does — responses arrive in a single message when complete.

### Features

Discord supports DMs, server channels, threads, forums, and voice channels (though voice is text-only in OpenClaw). Each channel or thread gets its own isolated session by default. You can configure per-guild and per-channel settings including `requireMention: false` for always-on behavior in private servers.

Slash commands are supported natively — OpenClaw registers and handles them. Message history context is available for threads. The `replyToMode` config controls how quotes work in replies.

Access control uses `groupPolicy` and `groupAllowFrom` for sender filtering, with role-based filtering possible when the Server Members Intent is enabled.

### Known issues

Discord bots require the **Message Content Intent** to be enabled in the Developer Portal, or the bot sees empty message content. This is a Discord requirement, not an OpenClaw one — the docs are explicit about this.

The docs have a critical note: in guild channels, OpenClaw defaults to **not posting visible output** unless the agent explicitly calls the message tool. This is by design — it lets the agent "lurk" and only respond when useful. If you want automatic replies, you need to configure `messages.groupChat.visibleReplies` or use a model with reliable tool-calling. This trips people up.

### Best for

Community AI assistants, team workspaces, people who already live in Discord. If you want each channel to have its own agent context (e.g., a #docs channel for documentation questions, a #dev channel for code), Discord is the right choice. Also good if you want slash commands.

---

## WhatsApp

WhatsApp is the channel to use when you need to reach people who won't install a new app or join a new platform. It works through WhatsApp Web's protocol (Baileys library), which means it behaves like a linked device on your personal or dedicated WhatsApp account.

### What it is

WhatsApp is a phone-number-based messaging platform with the widest global reach of any chat app. OpenClaw connects via the Baileys library, which implements the WhatsApp Web protocol. The gateway owns the linked-device session and handles message routing.

### Setup complexity

Three out of five stars. You need to install the `@openclaw/whatsapp` plugin, run `openclaw channels login --channel whatsapp` to scan a QR code, then configure your access policy. On Windows, you need Git on PATH for the install because a dependency fetches from git. The QR scan is straightforward but must be done on the machine running the gateway — no remote QR codes.

OpenClaw recommends using a **dedicated phone number** for the bot rather than your personal number. This avoids self-chat confusion, gives you cleaner access control, and means a broken bot doesn't interfere with your real WhatsApp.

### Latency and performance

WhatsApp Web latency is higher than Telegram or Discord due to the additional protocol layer. Expect 500ms–2s for message delivery. This is usually acceptable for a personal assistant but worth knowing if you're building anything latency-sensitive. The Baileys reconnect watchdog is activity-based, so quiet sessions don't trigger false restarts.

### Features

WhatsApp supports DMs and groups. Groups are identified by JID (WhatsApp's group ID format) rather than numeric IDs. You can configure group allowlists and sender allowlists separately. Mentions work via WhatsApp's native tap-to-mention or pattern matching. Voice notes are transcribed through OpenClaw's media pipeline.

Self-chat mode handles the case where your personal number and bot number are the same. It suppresses read receipts and mention-JID auto-trigger behavior that would otherwise ping yourself.

Media attachments are supported with configurable size limits (default 8MB). Outbound sends require an active WhatsApp listener.

### Known issues

WhatsApp's protocol is less stable than Telegram's API. Baileys connections can drop and reconnect, which OpenClaw handles, but this means WhatsApp is more operationally fragile than Telegram. If your internet connection is unstable, expect more reconnections.

Registration with a new phone number via `signal-cli` (for Signal) or the WhatsApp link flow carries risk: registering a number that already has a Signal app will de-authenticate the main Signal session. WhatsApp doesn't have this exact problem but linking a personal number to a bot session means the bot's messages appear alongside your real messages in the same WhatsApp thread.

OpenClaw does not use Twilio for WhatsApp — this is pure WhatsApp Web protocol.

### Best for

Reaching non-technical users, family members, or anyone already on WhatsApp who won't install Telegram or join a Discord server. Also good if you want a "just text my number" experience for your AI assistant.

---

## Signal

Signal is for when privacy isn't a feature request — it's a requirement. Signal uses end-to-end encryption by default and has no cloud storage of messages.

### What it is

Signal is a privacy-focused messaging app with end-to-end encryption on by default. OpenClaw connects via `signal-cli`, an external command-line tool that implements the Signal protocol. The gateway communicates with `signal-cli` over HTTP JSON-RPC and SSE for event delivery. `signal-cli` runs as a daemon on your server.

### Setup complexity

Four out of five stars. You need to install `signal-cli` (requires Java if using the JVM build, or a native build for Linux), register or link a phone number, handle captcha verification if registering a new number, configure OpenClaw, and approve the first DM via pairing. This is more involved than Telegram or WhatsApp.

Two setup paths: **QR link** (link an existing Signal account as a device) or **SMS register** (register a dedicated bot number). The QR link approach is simpler if you have an existing Signal account you don't mind linking. The SMS register approach gives you a fresh number but requires captcha handling.

### Latency and performance

Similar to WhatsApp — 500ms–2s round trip. The `signal-cli` daemon adds a small overhead but message delivery is reliable. Signal's protocol is designed for low-bandwidth environments so it handles unstable connections reasonably well.

### Features

Signal supports DMs and groups. Sessions are isolated per group. Reactions, attachments (up to 8MB), voice notes, and typing indicators are all supported. Read receipts can be forwarded to the sender when enabled. Text is chunked at 4000 characters by default with optional newline-aware chunking.

The `uuid:` prefix in sender allowlists handles UUID-only senders from `sourceUuid` — these appear as `uuid:<id>` in `channels.signal.allowFrom`.

### Known issues

Registering a phone number via `signal-cli` can de-authenticate the main Signal app on that number. This is a Signal protocol limitation: a number can only have one primary device, and registration replaces that. **Use a dedicated bot number.** Linking (QR flow) doesn't have this problem since it adds a secondary device rather than replacing the primary.

`signal-cli` needs to stay updated — the docs note that old releases can break as Signal updates its server API. Set a reminder to check for `signal-cli` updates periodically.

The external daemon mode (`httpUrl`) lets you run `signal-cli` separately, which is useful for slow JVM cold starts or containerized deployments. OpenClaw connects to it over HTTP rather than spawning it directly.

### Best for

Privacy-conscious users who refuse to use anything that isn't E2EE by default. Journalists, activists, security researchers, or anyone who wants their AI assistant conversations encrypted without configuring anything.

---

## Matrix

Matrix is for the self-hosted crowd. It is an open federated protocol — you pick your own homeserver and your data stays on your infrastructure.

### What it is

Matrix is an open federated messaging protocol. Instead of a single company owning your messages, you choose a homeserver (or run your own) and messages are distributed across federated servers. OpenClaw connects via the `matrix-js-sdk` and supports DMs, rooms, threads, media, reactions, polls, location, and end-to-end encryption.

### Setup complexity

Four out of five stars. You need a Matrix account on a homeserver, an access token or password, and some configuration. The `openclaw channels add` wizard handles most of this interactively. E2EE adds bootstrap complexity — the wizard handles it but you need to manage recovery keys.

### Latency and performance

Federation introduces network latency — how fast depends on which homeserver you're using. Self-hosted on the same machine: 500ms–1s. Federated across distant servers: potentially several seconds. If you're running your own homeserver and the gateway on the same host, performance is comparable to Discord.

### Features

Matrix has the most comprehensive feature set of any open protocol: DMs, rooms (groups), threads, media uploads, reactions, polls, location sharing, and native E2EE with Olm/Megolm. You can run multiple bots from one gateway via named accounts.

Streaming is opt-in and configurable — you can choose between partial previews and final-only delivery. The config controls both the in-flight assistant reply streaming and whether each streaming block is preserved as its own Matrix message.

Auto-join controls whether the bot accepts room invitations: `off` (default, ignores invites), `allowlist` (accepts only from configured rooms), or `always` (accepts everything). DMs go through auto-join first before DM policy applies.

### Known issues

The open federated nature of Matrix cuts both ways. If your homeserver is down, your bot is down. If you're using a public homeserver (matrix.org etc.), rate limits and server reliability are outside your control. For a reliable personal assistant, run your own homeserver (Synapse or Conduit are common choices).

E2EE support is good but adds operational overhead — you need to manage recovery keys and device verification. For a personal bot this is probably overkill unless you're specifically running Matrix for its federation properties.

Display names in allowlists are rejected unless the homeserver directory returns exactly one match — use stable `@user:server` IDs instead.

### Best for

Self-hosting enthusiasts, people who want federation so they're not locked into a single provider, anyone already running a Matrix homeserver. If you want your AI assistant on the same infrastructure as your other chat without depending on Big Tech, Matrix is the move.

---

## Webchat

Webchat is the embedded chat UI that ships with OpenClaw's gateway. It's the simplest way to talk to your agent when you're on the same machine or accessing through a browser.

### What it is

OpenClaw's gateway exposes a built-in web chat UI at `http://127.0.0.1:18789` (or whatever port you've configured). This is a WebSocket-based real-time interface — no page reloads, no polling, just a live connection to the gateway.

### Setup complexity

Two out of five stars. If the gateway is running, webchat just works. No tokens, no OAuth flows, no QR codes. It's the path of least resistance for local use.

### Latency and performance

WebSocket-native means the lowest latency of any channel — typically 100–300ms round trip for the gateway to process and respond. No internet round trip, no third-party API in the path. This is as fast as OpenClaw gets.

### Features

Webchat is intentionally minimal. Single-session chat with the agent, real-time streaming of responses, basic markdown rendering. No DMs, no groups, no media, no threading. It does one thing well: let you talk to your agent from a browser.

### Known issues

Webchat is local-only by default. It's not designed to be exposed to the internet directly — you'd need to put it behind a reverse proxy with authentication if you want remote access. For that use case, Telegram or Discord is a better choice.

It has no authentication built in beyond local access control. Anyone who can reach the webchat URL can chat with your agent.

### Best for

Local development and testing, quick one-off questions, embedding in your own web project. If you want to verify your agent is working while setting up a "real" channel, webchat is there. It's also the default UI when you run `openclaw tui`.

---

## Webhook vs Polling: Which is Faster for Telegram?

This comes up often. Here's the direct answer:

**Webhooks are technically faster.** With long polling, your gateway makes a request to Telegram, Telegram holds it open until a message arrives (or the timeout hits), and then the response carries the message. With webhooks, Telegram POSTs the message to your server the instant it arrives — no polling interval, no timeout wait.

In practice, the difference is negligible for personal bots. Long polling latency is typically 200–500ms from message-sent to message-received. Webhook latency is 100–400ms from message-sent to message-received. The 100ms difference matters if you're running a high-volume public bot handling thousands of messages per minute. It does not matter for a personal assistant.

**When to use webhooks:**
- You have a publicly reachable HTTPS endpoint
- You're running high-volume bot infrastructure
- You want to run multiple gateway instances behind a load balancer (long polling doesn't play well with this)
- You've already optimized your LLM response time and the 100ms webhook advantage actually matters

**When to stick with long polling:**
- Your gateway is behind NAT or doesn't have a public IP
- You want operational simplicity
- You're running a personal or small-team bot
- You don't want to manage TLS certificates and webhook secrets

OpenClaw defaults to long polling and makes webhooks opt-in. That's the right default. Change it when you have a specific reason to, not because webhooks "sound faster."

---

## Recommendations

**Use Telegram if:** You want the most reliable, lowest-friction setup. It's what OpenClaw is most tested against and what the docs use as the primary example. Your gateway needs to be reachable from the internet, but Telegram handles NAT traversal for you via its cloud API.

**Use Discord if:** You're building a multi-channel workspace or community bot. Discord's channel-per-context model is genuinely useful for keeping different conversations isolated. If you want slash commands, use Discord.

**Use WhatsApp if:** Your users are non-technical and already on WhatsApp. It removes the last mile of adoption friction — "just text this number" is a simpler concept than "install Telegram and find this bot." Use a dedicated number.

**Use Signal if:** Privacy is a hard requirement. Signal's E2EE is on by default and the protocol is well-audited. Accept the operational complexity of `signal-cli` in exchange for genuinely private conversations.

**Use Matrix if:** You want to self-host everything or need federation. Running your own homeserver means you own your data and can bridge to other networks. It's more work but it's the only channel where you genuinely control the infrastructure.

**Use Webchat if:** You're developing locally, testing a new setup, or embedding an agent UI in your own web project. It's not a production external channel — it's a utility.

---

## The Bottom Line

OpenClaw doesn't care which channel you use. The agent logic is the same, the memory is the same, the tools are the same. Pick the platform your users already live on.

For most people reading this, that's Telegram. It's the fastest to set up, the most reliable, and the best documented. Set it up in 15 minutes and move on.

The other channels each cost you something — more setup time, more operational complexity, more constraints. Make sure you're paying those costs for a real reason, not because "more options" feels like a feature.

Start simple. Add complexity when you have a specific need.