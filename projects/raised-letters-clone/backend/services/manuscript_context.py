"""Build full-manuscript context for AI editorial requests."""
import re

# ~28k tokens max for manuscript content (reserving ~4k for system + persona + response)
MAX_MANUSCRIPT_TOKENS = 28000
CHARS_PER_TOKEN = 4  # rough approximation


def build_context(project_id: str, chapters: list, companions: dict, focus_chapter_id: str = None) -> str:
    """
    Build a full-manuscript context string for AI editorial requests.

    Format:
    [WORLD BIBLE]
    {characters and world details}

    [STYLE GUIDE]
    {style rules}

    [EDITORIAL LETTER]
    {author's notes to the editor}

    [MANUSCRIPT]
    Chapter 1: {title}
    {content}

    Chapter 2: {title}
    {content}
    ...

    [PASSAGE TO REVIEW]
    {selected text or focus chapter content}
    """
    sections = []

    # World Bible
    if companions.get("world_bible"):
        wb = companions["world_bible"]
        sections.append("[WORLD BIBLE]\n")
        if wb.get("characters"):
            for char in wb["characters"]:
                sections.append(f"- {char['name']} ({char.get('role', 'character')}): {char.get('description', '')}\n")
        sections.append("\n")

    # Style Guide
    if companions.get("style_guide"):
        sg = companions["style_guide"]
        sections.append("[STYLE GUIDE]\n")
        if isinstance(sg, dict):
            for key, val in sg.items():
                sections.append(f"- {key}: {val}\n")
        sections.append("\n")

    # Editorial Letter
    if companions.get("editorial_letter"):
        el = companions["editorial_letter"]
        sections.append("[EDITORIAL LETTER]\n")
        if isinstance(el, dict):
            sections.append(el.get("content", str(el)) + "\n")
        sections.append("\n")

    # Chapters in order
    sections.append("[MANUSCRIPT]\n")
    ordered = sorted(chapters, key=lambda c: c["order_index"])
    for ch in ordered:
        is_focus = ch["id"] == focus_chapter_id
        marker = " <<< FOCUS CHAPTER >>>" if is_focus else ""
        sections.append(f"Chapter: {ch['title']}{marker}\n")
        sections.append(ch.get("content", "") + "\n\n")

    context = "".join(sections)

    # Truncate if needed (from earliest chapters, keeping focus chapter intact)
    max_chars = MAX_MANUSCRIPT_TOKENS * CHARS_PER_TOKEN
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[MANUSCRIPT TRUNCATED — earlier chapters not included]\n"

    return context


def estimate_tokens(text: str) -> int:
    """Rough token estimate."""
    return len(text) // CHARS_PER_TOKEN
