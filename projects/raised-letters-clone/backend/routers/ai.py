"""AI editorial endpoints (personas, feedback, copyedit, format_check, revision_pass)."""
import json
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ollama_service import health_check as ollama_health_check
from backend.services.settings_service import get_ai_model, save_settings, get_settings

router = APIRouter(prefix="/api/ai", tags=["ai"])

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"


# ── Pydantic models ──────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    project_id: str
    chapter_id: str
    passage: str = ""
    persona_id: str


class CopyeditRequest(BaseModel):
    project_id: str
    chapter_id: str
    passage: str = ""


class FormatCheckRequest(BaseModel):
    project_id: str
    chapter_id: str


class RevisionPassRequest(BaseModel):
    project_id: str
    chapter_id: str
    instructions: str = ""


# ── Stub responses ────────────────────────────────────────────────────────────

STUB_FEEDBACK = """## Editorial Feedback

**Overall Impression:**
This passage has a strong sense of place and the prose moves at a controlled pace. The sensory details are present but occasionally overwhelmed by exposition. The dialogue feels functional without being particularly distinctive.

**Strengths:**
- You've established a clear physical environment quickly
- The character's internal state is visible in their actions
- Pacing in the middle section is effective

**Areas to Examine:**

> "The door had been left open, just a crack, and through it came the sound of something mechanical working."

This is doing heavy lifting. Consider whether it earns its place. A crack in a door can convey tension without explaining the sound immediately. Let the reader sit with uncertainty.

> "She had been here before, years ago, when things were different."

"This" and "things" are doing vague work here. What was different? Name it — or decide that vagueness is the point and commit to it structurally.

**Structural Note:**
The passage shifts perspective at the third paragraph without a clear transition. If this is intentional, consider a hard break or a typographic signal. If it isn't, trace back to where the shift happens and decide whether it needs grounding.

**Next Steps:**
Focus on trimming 15-20% of the explanatory passages. Your best sentences are doing things; the weaker ones are explaining what the things mean. Trust the reader. Trust the prose.
"""

STUB_COPYEDIT = """## Copyedited Passage

Here's a tighter version with minimal intervention — only cuts and phrasing changes where they improve clarity or rhythm:

---

She didn't knock. The door had been left open, just a crack, and through it came the sound of something mechanical working, a low rhythmic grinding that seemed to come from the walls themselves.

Inside, the room was larger than she'd expected. Dark hardwood floors, a long table covered in papers and equipment she didn't recognize. At the far end, beneath a window that looked out onto the street, he stood with his back to her.

"You came," he said. He didn't turn around.

She stepped inside and closed the door behind her. The grinding sound stopped.

---

**Changes:**
- Removed "again" — it's implied by context
- Split one long sentence for pacing
- "Something mechanical working" → "something mechanical working" (kept, but flagged for possible tightening)
- "at the far end, beneath a window" → "at the far end, beneath a window" — consider removing "at the far end" if the room's layout is established
"""

STUB_FORMAT_CHECK = """## Format & Style Check

| Element | Status | Notes |
|---------|--------|-------|
| Dialogue tags | ⚠️ Review | 3 instances of "he said" / "she said" in close succession — consider trimming |
| Paragraph length | ✅ Good | Mix is appropriate for the scene type |
| Sentence length | ⚠️ Mixed | Several sentences over 30 words; break up for pacing |
| POV consistency | ✅ Maintained | Close third held throughout |
| Tense | ✅ Consistent | Past tense throughout |
| Semicolon use | ⚠️ Review | 1 semicolon found; consider breaking into separate sentences |
| Em-dashes | ✅ Appropriate | Used sparingly and correctly |
| Scene breaks | ❌ Missing | Consider adding a break between the arrival and what comes next |
| Word count | ℹ️ Info | Passage is ~{word_count} words |
"""

STUB_REVISION = """## Self-Revision Pass

You wrote this. Is this what you meant?

**The easy version vs. the true version:**

When a character "didn't knock," we understand that she's comfortable here, or that she's past the point of courtesy. But "didn't knock" is the safe way to write it — it's what any character would do. What would your specific character do? Would they hesitate at the door? Check their phone one more time? Stand there and almost leave?

The passage is full of small decisions like this. The words you've chosen are correct, but they may not be the *exact* words. The difference between "she stepped inside" and "she crossed the threshold" is not style — it's meaning.

**Questions to push through:**

1. In the second paragraph, you introduce "equipment she didn't recognize." What would she recognize? What does that distinction say about her?

2. When he says "You came," — that line is doing something. Is it relief? Surprise? A test? The line works only if you know what it means to him. Do you?

3. The grinding sound stopping when she closes the door — is that coincidence, or is he listening for her? That ambiguity is your best asset here. Don't resolve it accidentally.

**Tighten to:**
Cut the first sentence's adverb. "She didn't knock" is stronger without "either." Cut "larger than she'd expected" — "larger than expected" and trust the reader to know what she expected. Cut "that looked out onto the street" — we don't need to know yet.

You have the material. The revision is finding what's already there and cutting what isn't.
"""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def ai_status():
    """Check Ollama availability and loaded models."""
    return await ollama_health_check()


@router.get("/personas")
async def list_personas():
    """List all available editorial personas."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, name, description, system_prompt, is_active FROM personas ORDER BY id"
        )
        rows = await cur.fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "system_prompt": r["system_prompt"],
            "is_active": bool(r["is_active"]),
        }
        for r in rows
    ]


@router.get("/personas/{persona_id}")
async def get_persona(persona_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, name, description, system_prompt, is_active FROM personas WHERE id = ?",
            (persona_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Persona not found")
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "system_prompt": row["system_prompt"],
        "is_active": bool(row["is_active"]),
    }




# ── Model switcher ───────────────────────────────────────────────────────────

class ModelSettingsUpdate(BaseModel):
    ai_model: str | None = None
    ai_temperature: float | None = None
    ai_max_tokens: int | None = None


@router.get("/settings")
async def get_ai_settings():
    """Return current AI settings (model, temperature, max_tokens)."""
    return get_settings()


@router.patch("/settings")
async def update_ai_settings(data: ModelSettingsUpdate):
    """Update AI settings — switch model on the fly."""
    current = get_settings()
    update = {k: v for k, v in {
        "ai_model": data.ai_model,
        "ai_temperature": data.ai_temperature,
        "ai_max_tokens": data.ai_max_tokens,
    }.items() if v is not None}
    merged = save_settings(update)
    return {"status": "ok", **merged}


@router.post("/feedback")
async def get_feedback(data: FeedbackRequest):
    """
    Get editorial feedback from the selected persona on a passage.
    Stub returns realistic sample feedback; full Ollama integration pending.
    """
    # TODO: wire up Ollama once model is confirmed
    return {
        "persona_id": data.persona_id,
        "chapter_id": data.chapter_id,
        "feedback": STUB_FEEDBACK,
        "source": "stub",
    }


@router.post("/copyedit")
async def copyedit(data: CopyeditRequest):
    """
    Copyedit a passage.
    Stub returns sample copyedit; full Ollama integration pending.
    """
    word_count = len(data.passage.split())
    return {
        "chapter_id": data.chapter_id,
        "copyedited": STUB_COPYEDIT.format(word_count=word_count),
        "source": "stub",
    }


@router.post("/format-check")
async def format_check(data: FormatCheckRequest):
    """
    Check manuscript formatting and style consistency.
    Stub returns sample format report; full Ollama integration pending.
    """
    return {
        "chapter_id": data.chapter_id,
        "report": STUB_FORMAT_CHECK,
        "source": "stub",
    }


@router.post("/revision-pass")
async def revision_pass(data: RevisionPassRequest):
    """
    Self-revision pass: push the author toward the harder, truer version.
    Stub returns sample revision guide; full Ollama integration pending.
    """
    return {
        "chapter_id": data.chapter_id,
        "revision_guide": STUB_REVISION,
        "source": "stub",
    }
