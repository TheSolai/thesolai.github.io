"""
Shared MiniMax API helper for content-pipeline scripts.

Provides a single robust call with:
  - 180s timeout (up from 90s)
  - 3 retries with exponential backoff
  - Proper Anthropic-compatible message format
  - Clean error reporting

Usage:
    from _minimax_helper import minimax_generate, load_minimax_key

    key = _load_minimax_key()
    text = minimax_generate(prompt, api_key=key, max_tokens=600, system="...")
"""

import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

MINIMAX_KEY_PATH = Path.home() / ".openclaw" / "workspace" / "secrets" / "minimax-key.txt"
MINIMAX_URL = "https://api.minimax.io/anthropic/v1/messages"
MINIMAX_MODEL = "MiniMax-Text-01"


# ── Thinking-block stripping ────────────────────────────────────────────────
# Reasoning models (MiniMax M2.7, qwen3.5) emit their scratchpad inline:
#
#     Thinking...
#     Thinking Process:
#     1.  **Analyze the Request:**
#         *   **Topic:** ...
#     Let's write it.
#     ...done thinking.
#     <the actual article>
#
# Left in place this publishes the model's planning notes as the post body.
# 13 live posts carried it. Strip at the source so every caller benefits.

_PREAMBLE_START = re.compile(r"^\s*\*{0,2}(Thinking\.\.\.|Thinking Process:)")
_TERMINATOR = re.compile(
    r"^\s*(?:\*{0,2}\s*)?(?:Let's write it\.?|Let's write\.?|Let's assemble\.?|"
    r"Let's draft it\.?|\.\.\.done thinking\.?)\s*$",
    re.IGNORECASE,
)
# Lines that are unmistakably scratchpad rather than article prose.
_SCRATCH = re.compile(
    r"^(?:\d+\.\s+\*\*|\*{1,2}\(|\*{0,2}Thinking|Let's\b|\.\.\.|"
    r"\*{1,2}[A-Z][A-Za-z0-9 /]{0,30}:\*?)"
)


def _is_scratch(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if line.startswith("    ") or line.startswith("\t"):
        return True
    return bool(_SCRATCH.match(s))


# Hard scratchpad markers: the structured planning lines. Deliberately does
# NOT include "Let's" -- prose may legitimately open with "Let's talk about
# ...", and treating that as scratchpad would drop a real opening paragraph.
_HARD_SCRATCH = re.compile(
    r"^(?:\d+\.\s+\*\*|\*{0,2}Thinking|\.\.\.|\*{1,2}\()"
)


def _find_article_start(lines, start):
    """Index of the first real article line after the preamble at `start`.

    Prefers the LAST terminator: models often write "Let's write it." in the
    middle of the scratchpad and only close with "...done thinking.".
    """
    terms = [i for i in range(start + 1, len(lines)) if _TERMINATOR.match(lines[i])]
    for t in reversed(terms):
        # The article begins on the first line after the terminator that is
        # not hard scratchpad (indented bullets, numbered sections).
        for i in range(t + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue
            if line.startswith("    ") or line.startswith("\t"):
                continue
            if _HARD_SCRATCH.match(line.strip()):
                continue
            return i
        # Nothing usable after this terminator -- fall through to the next
        # earlier terminator rather than guessing.

    # No terminator matched. The model may have folded the boundary into a
    # sentence. Fall back to the first top-level markdown heading after the
    # preamble, which is where the article proper begins.
    for i in range(start + 1, len(lines)):
        line = lines[i]
        s = line.strip()
        if not s.startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            continue
        head = "\n".join(lines[i:i + 5])
        if re.search(r"Thinking Process|Analyze the Request", head):
            continue
        return i
    return None


def strip_thinking(text: str) -> str:
    """Remove leaked model reasoning from generated text.

    Returns the article only. If no preamble is detected the text is
    returned unchanged — this must never eat legitimate content.
    """
    if not text:
        return text

    # Fenced form: ```\nThinking Process: ... ```
    text = re.sub(r"```\s*\n?\s*Thinking Process:.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if _PREAMBLE_START.match(l)), None)
    if start is None:
        return text.strip()

    art = _find_article_start(lines, start)
    if art is None:
        # No boundary could be identified. Returning the text unchanged is
        # safer than cutting into real prose.
        return text.strip()

    out = []
    for line in lines[art:]:
        # Drop leading blank lines and residual scratchpad notes, but keep the
        # byline and everything after it.
        if not out:
            if _is_scratch(line):
                if line.strip().startswith("**By ") or line.strip().startswith("*By "):
                    out.append(line)
                continue
        out.append(line)

    result = "\n".join(out).strip()
    return result if result else text.strip()


def load_minimax_key() -> str:
    """Load MiniMax API key from secrets file."""
    try:
        return MINIMAX_KEY_PATH.read_text().strip()
    except Exception:
        return ""


def minimax_generate(prompt: str, api_key: str, max_tokens: int = 600, system: str = "",
                    temperature: float = 0.7, timeout: int = 180, retries: int = 3) -> str | None:
    """Call MiniMax with retries. Returns generated text or None on failure."""
    if not api_key:
        return None

    if system:
        messages = [{"role": "user", "content": system + "\n\n" + prompt}]
    else:
        messages = [{"role": "user", "content": prompt}]

    body = json.dumps({
        "model": MINIMAX_MODEL,
        "max_tokens": min(max_tokens, 8192),
        "temperature": temperature,
        "messages": messages,
    }).encode()

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                MINIMAX_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": api_key,
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
                for block in resp.get("content", []):
                    if block.get("type") == "text":
                        text = strip_thinking(block["text"])
                        if text:
                            return text
                last_err = "empty content"
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.reason}"
            if e.code in (429, 500, 502, 503, 504):
                # Transient — retry
                pass
            else:
                # Non-transient — don't retry
                return None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"

        # Backoff before next attempt
        if attempt < retries:
            backoff = 2 ** attempt  # 2, 4 seconds
            time.sleep(backoff)

    return None