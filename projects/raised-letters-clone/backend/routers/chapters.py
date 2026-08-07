"""Chapter CRUD + reorder router."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/chapters", tags=["chapters"])

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"
MANUSCRIPT_ROOT = Path.home() / ".raised-letters" / "manuscripts"


def _chapter_content_path(project_id: str, chapter_id: str) -> Path:
    return MANUSCRIPT_ROOT / project_id / f"{chapter_id}.txt"


def _get_content(project_id: str, chapter_id: str) -> str:
    path = _chapter_content_path(project_id, chapter_id)
    if path.exists():
        return path.read_text()
    return ""


def _put_content(project_id: str, chapter_id: str, content: str) -> str:
    path = _chapter_content_path(project_id, chapter_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return str(path)


def _delete_content(project_id: str, chapter_id: str):
    path = _chapter_content_path(project_id, chapter_id)
    if path.exists():
        path.unlink()
    try:
        project_dir = path.parent
        if project_dir.exists() and not any(project_dir.iterdir()):
            project_dir.rmdir()
    except Exception:
        pass


def _word_count(text: str) -> int:
    return len(text.split())


# ── Pydantic models ──────────────────────────────────────────────────────────

class ChapterCreate(BaseModel):
    project_id: str
    title: str
    content: str = ""
    order_index: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None


class ChapterOut(BaseModel):
    id: str
    project_id: str
    title: str
    order_index: int
    content_path: str
    word_count: int
    content: str = ""
    created_at: str
    updated_at: str


class ReorderRequest(BaseModel):
    chapter_ids: list[str]


def _row_to_chapter(row) -> ChapterOut:
    pid = row[1]
    cid = row[0]
    content = _get_content(pid, cid)
    return ChapterOut(
        id=row[0], project_id=row[1], title=row[2], order_index=row[3],
        content_path=row[4], word_count=row[5], content=content,
        created_at=row[6], updated_at=row[7]
    )


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/for-project/{project_id}", response_model=list[ChapterOut])
async def list_chapters(project_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """SELECT id, project_id, title, order_index, content_path, word_count, created_at, updated_at
               FROM chapters WHERE project_id = ? ORDER BY order_index""",
            (project_id,),
        )
        rows = await cur.fetchall()
    return [_row_to_chapter(r) for r in rows]


@router.get("/{chapter_id}", response_model=ChapterOut)
async def get_chapter(chapter_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """SELECT id, project_id, title, order_index, content_path, word_count, created_at, updated_at
               FROM chapters WHERE id = ?""",
            (chapter_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Chapter not found")
    return _row_to_chapter(row)


@router.post("", response_model=ChapterOut, status_code=201)
async def create_chapter(data: ChapterCreate):
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())
    content_path = _put_content(data.project_id, cid, data.content)
    wc = _word_count(data.content)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """INSERT INTO chapters (id, project_id, title, order_index, content_path, word_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, data.project_id, data.title, data.order_index, content_path, wc, now, now),
        )
        await conn.commit()
    return ChapterOut(
        id=cid, project_id=data.project_id, title=data.title,
        order_index=data.order_index, content_path=content_path,
        word_count=wc, content=data.content, created_at=now, updated_at=now
    )


@router.patch("/{chapter_id}", response_model=ChapterOut)
async def update_chapter(chapter_id: str, data: ChapterUpdate):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Chapter not found")

        updates = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.order_index is not None:
            updates["order_index"] = data.order_index
        if data.content is not None:
            content_path = _put_content(row[1], chapter_id, data.content)
            updates["content_path"] = content_path
            updates["word_count"] = _word_count(data.content)

        if updates:
            updates["updated_at"] = now
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [chapter_id]
            await conn.execute(f"UPDATE chapters SET {set_clause} WHERE id = ?", vals)
            await conn.commit()

        cur = await conn.execute(
            """SELECT id, project_id, title, order_index, content_path, word_count, created_at, updated_at
               FROM chapters WHERE id = ?""",
            (chapter_id,),
        )
        updated = await cur.fetchone()
    return _row_to_chapter(updated)


@router.delete("/{chapter_id}", status_code=204)
async def delete_chapter(chapter_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT project_id FROM chapters WHERE id = ?", (chapter_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Chapter not found")
        await conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
        await conn.commit()
        project_id = row[0]
    _delete_content(project_id, chapter_id)


@router.post("/reorder/{project_id}", response_model=list[ChapterOut])
async def reorder_chapters(project_id: str, data: ReorderRequest):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        for idx, cid in enumerate(data.chapter_ids):
            await conn.execute(
                "UPDATE chapters SET order_index = ?, updated_at = ? WHERE id = ? AND project_id = ?",
                (idx, now, cid, project_id),
            )
        await conn.commit()
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """SELECT id, project_id, title, order_index, content_path, word_count, created_at, updated_at
               FROM chapters WHERE project_id = ? ORDER BY order_index""",
            (project_id,),
        )
        rows = await cur.fetchall()
    return [_row_to_chapter(r) for r in rows]
