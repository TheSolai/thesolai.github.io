"""
Raised Letters Clone — FastAPI Backend
"""
import aiosqlite
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import projects, chapters, checkpoints, companions, ai

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Raised Letters Clone API",
    description="Editorial companion for fiction writers",
    version="0.1.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(checkpoints.router)
app.include_router(companions.router)
app.include_router(ai.router)


# ── Database path ─────────────────────────────────────────────────────────────

DB_PATH = Path.home() / ".raised-letters" / "raised-letters.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── DB helper functions (used by routers and other modules) ──────────────────

async def db_execute(query: str, params: tuple = ()) -> aiosqlite.Cursor:
    """Execute a write query and commit."""
    conn = await aiosqlite.connect(DB_PATH)
    cur = await conn.execute(query, params)
    await conn.commit()
    await conn.close()
    return cur


async def db_fetchall(query: str, params: tuple = ()) -> list:
    """Fetch all rows."""
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    rows = await conn.execute_fetchall(query, params)
    await conn.close()
    return rows


async def db_fetchone(query: str, params: tuple = ()) -> aiosqlite.Row | None:
    """Fetch one row."""
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    row = await conn.execute_fetchone(query, params)
    await conn.close()
    return row


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "db": str(DB_PATH)}


@app.get("/")
async def root():
    return {
        "app": "Raised Letters Clone API",
        "version": "0.1.0",
        "docs": "/docs",
    }
