"""Companion document CRUD + character CRUD router."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/companions", tags=["companions"])

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"


# ── Pydantic models ──────────────────────────────────────────────────────────

class CompanionCreate(BaseModel):
    project_id: str
    type: str  # world_bible | style_guide | editorial_letter
    content: dict | str = {}


class CompanionUpdate(BaseModel):
    content: dict | str | None = None


class CharacterCreate(BaseModel):
    companion_id: str
    name: str
    role: str = ""
    description: str = ""
    first_appearance: str = ""
    details: dict = {}


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    first_appearance: Optional[str] = None
    details: Optional[dict] = None


class CharacterOut(BaseModel):
    id: str
    companion_id: str
    name: str
    role: str
    description: str
    first_appearance: str
    details: dict
    created_at: str
    updated_at: str


class CompanionOut(BaseModel):
    id: str
    project_id: str
    type: str
    content: dict | str
    created_at: str
    updated_at: str
    characters: list[CharacterOut] = []


def _row_to_character(row) -> CharacterOut:
    return CharacterOut(
        id=row[0], companion_id=row[1], name=row[2], role=row[3] or "",
        description=row[4] or "", first_appearance=row[5] or "",
        details=json.loads(row[6]) if isinstance(row[6], str) else (row[6] or {}),
        created_at=row[7], updated_at=row[8]
    )


def _row_to_companion(row, characters=None) -> CompanionOut:
    content = row[2]
    if isinstance(content, str):
        content = json.loads(content)
    return CompanionOut(
        id=row[0], project_id=row[1], type=row[2],
        content=content if isinstance(content, dict) else {},
        created_at=row[3], updated_at=row[4],
        characters=characters or []
    )


# ── Companion CRUD ────────────────────────────────────────────────────────────

@router.get("/for-project/{project_id}", response_model=list[CompanionOut])
async def list_companions(project_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, project_id, type, content, created_at, updated_at FROM companions WHERE project_id = ?",
            (project_id,),
        )
        companion_rows = await cur.fetchall()

    result = []
    for row in companion_rows:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            char_cur = await conn.execute(
                "SELECT * FROM characters WHERE companion_id = ? ORDER BY name", (row[0],)
            )
            char_rows = await char_cur.fetchall()
        chars = [_row_to_character(r) for r in char_rows]
        result.append(_row_to_companion(row, chars))

    return result


@router.get("/{companion_id}", response_model=CompanionOut)
async def get_companion(companion_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, project_id, type, content, created_at, updated_at FROM companions WHERE id = ?",
            (companion_id,),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Companion not found")

        char_cur = await conn.execute(
            "SELECT * FROM characters WHERE companion_id = ? ORDER BY name", (companion_id,)
        )
        char_rows = await char_cur.fetchall()

    chars = [_row_to_character(r) for r in char_rows]
    return _row_to_companion(row, chars)


@router.post("", response_model=CompanionOut, status_code=201)
async def create_companion(data: CompanionCreate):
    VALID_TYPES = {"world_bible", "style_guide", "editorial_letter"}
    if data.type not in VALID_TYPES:
        raise HTTPException(400, f"type must be one of {VALID_TYPES}")

    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())
    content_json = json.dumps(data.content) if isinstance(data.content, dict) else data.content

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                """INSERT INTO companions (id, project_id, type, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cid, data.project_id, data.type, content_json, now, now),
            )
            await conn.commit()
    except Exception as e:
        raise HTTPException(400, f"Companion already exists for this project/type: {e}")

    return CompanionOut(
        id=cid, project_id=data.project_id, type=data.type,
        content=data.content if isinstance(data.content, dict) else {},
        created_at=now, updated_at=now, characters=[]
    )


@router.patch("/{companion_id}", response_model=CompanionOut)
async def update_companion(companion_id: str, data: CompanionUpdate):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM companions WHERE id = ?", (companion_id,)
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Companion not found")

        content_val = json.dumps(data.content) if data.content is not None else row[2]
        await conn.execute(
            "UPDATE companions SET content = ?, updated_at = ? WHERE id = ?",
            (content_val, now, companion_id),
        )
        await conn.commit()

        char_cur = await conn.execute(
            "SELECT * FROM characters WHERE companion_id = ? ORDER BY name", (companion_id,)
        )
        char_rows = await char_cur.fetchall()

        cur2 = await conn.execute(
            "SELECT id, project_id, type, content, created_at, updated_at FROM companions WHERE id = ?",
            (companion_id,),
        )
        updated_row = await cur2.fetchone()

    chars = [_row_to_character(r) for r in char_rows]
    content_dict = json.loads(updated_row[2]) if isinstance(updated_row[2], str) else updated_row[2]
    return CompanionOut(
        id=updated_row[0], project_id=updated_row[1], type=updated_row[2],
        content=content_dict or {}, created_at=updated_row[3],
        updated_at=updated_row[4], characters=chars
    )


@router.delete("/{companion_id}", status_code=204)
async def delete_companion(companion_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT id FROM companions WHERE id = ?", (companion_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Companion not found")
        await conn.execute("DELETE FROM companions WHERE id = ?", (companion_id,))
        await conn.commit()


# ── Character CRUD ────────────────────────────────────────────────────────────

@router.get("/characters/{character_id}", response_model=CharacterOut)
async def get_character(character_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Character not found")
    return _row_to_character(row)


@router.post("/characters", response_model=CharacterOut, status_code=201)
async def create_character(data: CharacterCreate):
    now = datetime.now(timezone.utc).isoformat()
    char_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT id FROM companions WHERE id = ?", (data.companion_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Companion not found")

        await conn.execute(
            """INSERT INTO characters (id, companion_id, name, role, description, first_appearance, details, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (char_id, data.companion_id, data.name, data.role, data.description,
             data.first_appearance, json.dumps(data.details), now, now),
        )
        await conn.commit()
    return CharacterOut(
        id=char_id, companion_id=data.companion_id, name=data.name,
        role=data.role, description=data.description,
        first_appearance=data.first_appearance, details=data.details,
        created_at=now, updated_at=now
    )


@router.patch("/characters/{character_id}", response_model=CharacterOut)
async def update_character(character_id: str, data: CharacterUpdate):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Character not found")

        updates = {}
        for field, val in [
            ("name", data.name), ("role", data.role), ("description", data.description),
            ("first_appearance", data.first_appearance),
        ]:
            if val is not None:
                updates[field] = val
        if data.details is not None:
            updates["details"] = json.dumps(data.details)

        if updates:
            updates["updated_at"] = now
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [character_id]
            await conn.execute(f"UPDATE characters SET {set_clause} WHERE id = ?", vals)
            await conn.commit()

        cur = await conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        updated = await cur.fetchone()
    return _row_to_character(updated)


@router.delete("/characters/{character_id}", status_code=204)
async def delete_character(character_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT id FROM characters WHERE id = ?", (character_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Character not found")
        await conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
        await conn.commit()
