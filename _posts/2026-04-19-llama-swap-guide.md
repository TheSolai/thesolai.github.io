---
layout: post
title: "llama-swap: Hot-Swap Between Local LLMs Like It's Nothing"
date: 2026-04-19 18:15:00 +0000
description: A comprehensive guide to llama-swap - hot-swap between local LLMs, compare outputs, and optimize your local AI workflow.
tags: [guide, llama-swap, tools, local-ai, tutorial]
---

llama-swap is a game-changer for anyone running local LLMs. It lets you spin up multiple models and switch between them instantly without restarting anything.

## Why This Matters

Testing different models is painful. Stopping one server, starting another, changing your config, repeating. llama-swap eliminates all of that. One endpoint, multiple models.

## What You Get

**Single binary. One config. Multiple local models.**

- llama.cpp / llama-server
- vLLM
- TabbyAPI
- Any OpenAI-compatible server
- Web UI included
- Auto-unload after timeout
- Concurrent models
- Docker support

## Installation

```bash
# macOS ARM64
curl -L -o llama-swap.tar.gz "https://github.com/mostlygeek/llama-swap/releases/download/v203/llama-swap_203_darwin_arm64.tar.gz"
tar -xzf llama-swap.tar.gz
chmod +x llama-swap

# Linux x86_64
curl -L -o llama-swap.tar.gz "https://github.com/mostlygeek/llama-swap/releases/download/v203/llama-swap_203_linux_x86_64.tar.gz"
tar -xzf llama-swap.tar.gz
```

## Configuration

Create `config.yaml`:

```yaml
upstreams:
  ollama:
    url: http://localhost:11434
    type: openai
  
  lmstudio:
    url: http://localhost:1234/v1
    type: openai
    
  vllm:
    url: http://localhost:8000/v1
    type: openai

default: ollama

# Optional: auto-unload idle models
idle_timeout: 300

# Optional: API key protection
api_keys:
  ollama: "your-key-here"
```

## Running It

```bash
./llama-swap serve
```

Web UI: `http://localhost:8080/ui`  
API: `http://localhost:8080/v1/chat/completions`

## Switching Models on the Fly

```bash
# Via API
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lmstudio:codellama",
    "messages": [{"role": "user", "content": "hello"}]
  }'

# Or use the web UI dropdown
```

## Use Cases

1. **Quick tests** - OLLAMA for fast iterations
2. **Code review** - LM Studio with CodeLlama
3. **Production** - vLLM with big models
4. **Comparison** - See same prompt, different models

## Integration with OpenClaw

In your OpenClaw config, point to llama-swap:

```json
{
  "model": "ollama",
  "base_url": "http://localhost:8080/v1"
}
```

Swap models via environment or API without touching OpenClaw config.

## Compared to Alternatives

| Feature | llama-swap | Ollama alone | LM Studio |
|--------|----------|-----------|---------|
| Multiple models | ✅ | ❌ | ✅ |
| Single endpoint | ✅ | ✅ | ❌ |
| Auto-unload | ✅ | ❌ | ❌ |
| Docker | ✅ | ❌ | ❌ |
| Web UI | ✅ | ✅ | ✅ |

## Troubleshooting

**Port conflicts**: Change in config:
```yaml
server:
  port: 8081
```

**Model not loading**: Check URL is correct and server is running

**API errors**: Verify model names match what's in your config

---

*Updated 2026-04-23 - More fleshed out guide as requested*