"""Settings service — reads/writes ~/.raised-letters/settings.json."""
import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".raised-letters" / "settings.json"
SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True")

_DEFAULTS = {
    "ai_model": "llama2-uncensored:latest",
    "ai_engine": "ollama",
    "ai_temperature": 0.7,
    "ai_max_tokens": 2048,
}

def get_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return _DEFAULTS.copy()
    try:
        return json.loads(SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return _DEFAULTS.copy()

def save_settings(settings: dict) -> dict:
    merged = {**_DEFAULTS, **get_settings(), **settings}
    SETTINGS_PATH.write_text(json.dumps(merged, indent=2))
    return merged

def get_ai_model() -> str:
    return get_settings().get("ai_model", "llama2-uncensored:latest")
