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

# `str | None` in the minimax_generate signature is PEP 604 syntax, which
# raises TypeError at import time on Python 3.9 (the system python3 on macOS
# is still 3.9). Deferring annotation evaluation keeps this module importable
# on every interpreter the content pipeline might be invoked with.
from __future__ import annotations

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

# Introspective scratch openers: prose that plans rather than publishes.
_SCRATCH_OPENER = re.compile(
    r"^(?:let me|okay,|ok,|alright|right,|i'?ll|i will|now,|first,|next,|"
    r"so,|well,|here'?s what|let'?s think)\b",
    re.IGNORECASE,
)

# A short byline the model may place directly above the article.
_BYLINE = re.compile(r"^\s*\*\*(?:By|by)\s+[^*]{1,40}\*\*\s*$")


def _is_article_candidate(line):
    """True if `line` plausibly opens the article proper."""
    s = line.strip()
    if not s:
        return False
    if line.startswith("    ") or line.startswith("\t"):
        return False
    if _HARD_SCRATCH.match(s):
        return False
    if _SCRATCH_OPENER.match(s):
        return False
    if s.startswith("#"):
        return True
    if _BYLINE.match(line):
        return True
    # Long unbroken prose is article; short lines are scratch notes.
    return len(s) > 60


def _find_article_start(lines, start):
    """Index of the first real article line after the preamble at `start`.

    Prefers the LAST terminator: models often write "Let's write it." in the
    middle of the scratchpad and only close with "...done thinking.".
    """
    terms = [i for i in range(start + 1, len(lines)) if _TERMINATOR.match(lines[i])]
    for t in reversed(terms):
        for i in range(t + 1, len(lines)):
            if _is_article_candidate(lines[i]):
                return i

    # No terminator matched: the model folded the boundary into a sentence.
    # Prefer a markdown heading -- the pipeline prompts for the post to open
    # with one -- and only then fall back to the first long prose line.
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

    for i in range(start + 1, len(lines)):
        if _is_article_candidate(lines[i]):
            return i
    return None


# ── Terminal capture artifacts ───────────────────────────────────────────────
# Content captured from a PTY carries the terminal's own hard-wrap control
# sequences. When a word straddled the wrap point the terminal emitted
# ESC[<N>D (cursor back N) followed by ESC[K (erase to end of line) so the
# partial word would not be displayed twice. A browser never executes these
# escapes, so the published page showed the word TWICE.
#
# 13 live posts carried this. strip_terminal_artifacts() reproduces what the
# terminal would have displayed, then re-flows the wrapped lines.

_ESC_CURSOR_BACK = re.compile(r"\x1b\[(\d*)D")
_ESC_ERASE_EOL = re.compile(r"\x1b\[K")
_ESC_CSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# A line that starts a new markdown block.
_BLOCK_START = re.compile(
    r"^(?:\s{0,3}(?:#{1,6}\s|>|```|~~~|-{3,}\s*$|\|)|\s*(?:[-*+]|\d+[.)])\s)"
)
_FENCE = re.compile(r"^\s*(?:```|~~~)")


def render_terminal_line(raw: str) -> str:
    """Return the text a terminal would display for this raw line.

    Simulates cursor-back (ESC[N D) and erase-to-end-of-line (ESC[K).
    """
    buf = []
    cursor = 0
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\x1b":
            m = _ESC_CURSOR_BACK.match(raw, i)
            if m:
                cursor = max(0, cursor - int(m.group(1) or 1))
                i = m.end()
                continue
            m = _ESC_ERASE_EOL.match(raw, i)
            if m:
                del buf[cursor:]
                i = m.end()
                continue
            m = _ESC_CSI.match(raw, i)
            if m:
                i = m.end()
                continue
            i += 1
            continue
        if cursor < len(buf):
            buf[cursor] = ch
            cursor += 1
        else:
            buf.append(ch)
            cursor += 1
        i += 1
    return "".join(buf)


def strip_terminal_escapes(text: str) -> str:
    """Render every line as a terminal would, keeping line structure."""
    if not text:
        return text
    return "\n".join(render_terminal_line(l) for l in text.split("\n"))


def strip_terminal_artifacts(text: str) -> str:
    """Render escapes away and re-flow hard-wrapped paragraphs.

    Markdown structure is preserved: headings, list items, blockquotes,
    tables and fenced code blocks keep their own lines and are never joined.
    """
    if not text:
        return text

    lines = strip_terminal_escapes(text).split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        if not line.strip():
            out.append("")
            i += 1
            continue

        # Fenced code block: copy verbatim until the closing fence.
        if _FENCE.match(line):
            out.append(line.rstrip())
            i += 1
            while i < n:
                out.append(lines[i].rstrip())
                closing = bool(_FENCE.match(lines[i]))
                i += 1
                if closing:
                    break
            continue

        # A block-start line begins its own block; continuation lines are
        # joined on to it.
        if _BLOCK_START.match(line):
            block = [line.rstrip()]
            i += 1
            while i < n and lines[i].strip() and not _FENCE.match(lines[i]) \
                    and not _BLOCK_START.match(lines[i]):
                block.append(lines[i].strip())
                i += 1
            out.append(" ".join(x for x in block if x).rstrip())
            continue

        # Plain paragraph: join the following non-blank, non-block lines.
        para = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not _FENCE.match(lines[i]) \
                and not _BLOCK_START.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(" ".join(x for x in para if x).rstrip())

    # Collapse runs of blank lines to a single blank line.
    collapsed = []
    for l in out:
        if not l.strip() and collapsed and not collapsed[-1].strip():
            continue
        collapsed.append(l)
    return "\n".join(collapsed)


def strip_thinking(text: str) -> str:
    """Remove leaked model reasoning from generated text.

    Returns the article only. If no preamble is detected the text is
    returned unchanged -- this must never eat legitimate content.
    """
    if not text:
        return text

    # Normalise terminal hard-wrap escapes first: the preamble marker can be
    # followed by capture artefacts, and the line structure must be stable
    # before we look for the scratchpad boundary.
    text = strip_terminal_escapes(text)

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

    # Keep a byline that sits directly above the article.
    begin = art
    j = art - 1
    while j > start and not lines[j].strip():
        j -= 1
    if j > start and _BYLINE.match(lines[j]):
        begin = j

    out = []
    for line in lines[begin:]:
        # Drop leading blank lines only; the boundary above is authoritative.
        if not out and not line.strip():
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