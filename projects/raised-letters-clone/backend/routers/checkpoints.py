"""Checkpoint CRUD + restore router."""
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"
MANUSCRIPT_ROOT = Path.home() / ".raised-letters" / "manuscripts"


def _chapter_content_path(project_id: str, chapter_id: str) -> Path:
    return MANUSCRIPT_ROOT / project_id / f"{chapter_id}.txt"


def _get_content(project_id: str, chapter_id: str) -> str:
    path = _chapter_content_path(project_id, chapter_id)
    if path.exists():
        return path.read_text()
    return ""


def _word_count(text: str) -> int:
    return len(text.split())


class CheckpointCreate(BaseModel):
    chapter_id: str
    name: str
    content: str | None = None  # Optional — auto-captured if omitted


class CheckpointOut(BaseModel):
    id: str
    chapter_id: str
    name: str
    content: str
    word_count: int
    created_at: str


class RestoreRequest(BaseModel):
    content: str | None = None


@router.get("/for-chapter/{chapter_id}", response_model=list[CheckpointOut])
async def list_checkpoints(chapter_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """SELECT id, chapter_id, name, content, word_count, created_at
               FROM checkpoints WHERE chapter_id = ? ORDER BY created_at DESC""",
            (chapter_id,),
        )
        rows = await cur.fetchall()
    return [
        CheckpointOut(id=r[0], chapter_id=r[1], name=r[2], content=r[3],
                      word_count=r[4], created_at=r[5])
        for r in rows
    ]


@router.get("/{checkpoint_id}", response_model=CheckpointOut)
async def get_checkpoint(checkpoint_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, chapter_id, name, content, word_count, created_at FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Checkpoint not found")
    return CheckpointOut(id=row[0], chapter_id=row[1], name=row[2], content=row[3],
                         word_count=row[4], created_at=row[5])


@router.post("", response_model=CheckpointOut, status_code=201)
async def create_checkpoint(data: CheckpointCreate):
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())

    if data.content is None:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT project_id FROM chapters WHERE id = ?", (data.chapter_id,)
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, f"Chapter {data.chapter_id} not found")
            project_id = row[0]
        data.content = _get_content(project_id, data.chapter_id)

    wc = _word_count(data.content)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """INSERT INTO checkpoints (id, chapter_id, name, content, word_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cid, data.chapter_id, data.name, data.content, wc, now),
        )
        await conn.commit()
    return CheckpointOut(id=cid, chapter_id=data.chapter_id, name=data.name,
                         content=data.content, word_count=wc, created_at=now)


@router.delete("/{checkpoint_id}", status_code=204)
async def delete_checkpoint(checkpoint_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT id FROM checkpoints WHERE id = ?", (checkpoint_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Checkpoint not found")
        await conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
        await conn.commit()


@router.post("/{checkpoint_id}/restore")
async def restore_checkpoint(checkpoint_id: str, data: RestoreRequest | None = None):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)
        )
        cp_row = await cur.fetchone()
        if not cp_row:
            raise HTTPException(404, "Checkpoint not found")

        chapter_id = cp_row[1]

        if data is not None and data.content is not None:
            now = datetime.now(timezone.utc).isoformat()
            wc = _word_count(data.content)
            auto_name = (f"Auto-save before restore "
                         f"({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')})")
            restore_cid = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO checkpoints (id, chapter_id, name, content, word_count, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (restore_cid, chapter_id, auto_name, data.content, wc, now),
            )
            await conn.commit()

    return {
        "checkpoint_id": checkpoint_id,
        "chapter_id": chapter_id,
        "restored_content": cp_row[3],
        "restored_word_count": cp_row[4],
        "message": f"Restored from checkpoint '{cp_row[2]}'.",
    }
