"""Project CRUD router."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/projects", tags=["projects"])

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"


# ── Pydantic models ──────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    subtitle: str = ""
    author: str = ""
    genre: str = ""


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    title: str
    subtitle: str
    author: str
    genre: str
    created_at: str
    updated_at: str


# ── helpers ─────────────────────────────────────────────────────────────────

def _row_to_project(row) -> ProjectOut:
    return ProjectOut(
        id=row[0], title=row[1], subtitle=row[2] or "", author=row[3] or "",
        genre=row[4] or "", created_at=row[5], updated_at=row[6]
    )


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ProjectOut])
async def list_projects():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, title, subtitle, author, genre, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        )
        rows = await cur.fetchall()
    return [_row_to_project(r) for r in rows]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT id, title, subtitle, author, genre, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return _row_to_project(row)


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate):
    now = datetime.now(timezone.utc).isoformat()
    pid = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """INSERT INTO projects (id, title, subtitle, author, genre, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pid, data.title, data.subtitle, data.author, data.genre, now, now),
        )
        await conn.commit()
    return ProjectOut(
        id=pid, title=data.title, subtitle=data.subtitle,
        author=data.author, genre=data.genre, created_at=now, updated_at=now
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, data: ProjectUpdate):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Project not found")

        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if updates:
            updates["updated_at"] = now
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [project_id]
            await conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", vals)
            await conn.commit()

        cur = await conn.execute(
            "SELECT id, title, subtitle, author, genre, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        )
        row = await cur.fetchone()
    return _row_to_project(row)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not await cur.fetchone():
            raise HTTPException(404, "Project not found")
        await conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await conn.commit()
