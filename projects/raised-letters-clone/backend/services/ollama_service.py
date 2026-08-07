"""Ollama bridge for local LLM calls."""
import httpx
from typing import Generator

OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT = 120.0


def chat(model: str, prompt: str, system: str = "", stream: bool = True) -> Generator[str, None, None]:
    """Send a chat request to Ollama. Yields response tokens."""
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": stream,
        "options": {"temperature": 0.7, "num_predict": 2048}
    }
    with httpx.stream("POST", OLLAMA_URL, json=payload, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                try:
                    import json
                    data = json.loads(line)
                    yield data.get("response", "")
                except json.JSONDecodeError:
                    continue


async def health_check() -> dict:
    """Check if Ollama is running and list available models."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            return {"status": "ok", "models": [m["name"] for m in models]}
    except Exception as e:
        return {"status": "error", "error": str(e)}
