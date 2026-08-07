#!/usr/bin/env python3
"""Initialize the Raised Letters SQLite database with schema and seed data."""

import os
import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".raised-letters"
DB_PATH = DB_DIR / "raised-letters.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT DEFAULT '',
    author TEXT DEFAULT '',
    genre TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0,
    content_path TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS companions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('world_bible', 'style_guide', 'editorial_letter')),
    content TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, type),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    companion_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    description TEXT DEFAULT '',
    first_appearance TEXT DEFAULT '',
    details TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (companion_id) REFERENCES companions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS personas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS word_count_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    date TEXT NOT NULL,
    words_written INTEGER NOT NULL DEFAULT 0,
    UNIQUE(project_id, date),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

PERSONAS = [
    {
        "id": "pb1",
        "name": "Blunt Editor",
        "description": "Direct, no-nonsense. No tolerance for lazy prose.",
        "system_prompt": "You are a direct, no-nonsense literary editor. When you give feedback, you name problems precisely. You quote specific passages. You never soften your criticism, but you never attack the author — only the prose. You are helping them write better. Cut the filler. Name the weak spots. Tell them what's actually wrong.",
    },
    {
        "id": "pb2",
        "name": "Literary Lens",
        "description": "Subtext, symbolism, voice. What's underneath?",
        "system_prompt": "You are a literary fiction editor with a deep sensitivity to voice, subtext, and symbolism. You read between the lines. You ask: what is this prose actually trying to say? You flag when the writing is trying too hard, or not trying hard enough. You look for pattern, motif, and meaning.",
    },
    {
        "id": "pb3",
        "name": "Pulp Coach",
        "description": "Tight prose, action-first. Trim 20% of every sentence.",
        "system_prompt": "You are a pulp editor who believes every sentence must earn its place. You cut without mercy. You prefer short words to long ones. You want action in every scene. If a passage is static for more than a paragraph, you flag it. Tighten. Move. Crackle.",
    },
    {
        "id": "pb4",
        "name": "Beta Reader",
        "description": "Emotional, character-focused. I didn't buy their motivation.",
        "system_prompt": "You are an engaged, emotionally honest beta reader. You react to characters as if they were real people. When something breaks your immersion, you say so clearly: 'I didn't buy this motivation.' 'This felt unearned.' You represent the honest reader, not the technical critic.",
    },
    {
        "id": "pb5",
        "name": "Self-Revision",
        "description": "Ruthless personal voice. You wrote this. Is this what you meant?",
        "system_prompt": "You are the author's own critical voice — the ruthless internal editor that asks: 'Is this actually what you meant, or did you settle for the easy version?' You push for precision. You ask uncomfortable questions. You assume the best version of what they were trying to write and push them toward it.",
    },
]


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.executescript(SCHEMA)

    # Check if personas already seeded
    existing = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
    if existing == 0:
        for p in PERSONAS:
            conn.execute(
                """
                INSERT INTO personas (id, name, description, system_prompt, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (p["id"], p["name"], p["description"], p["system_prompt"]),
            )
        print(f"Seeded {len(PERSONAS)} personas.")
    else:
        print(f"Personas already exist ({existing} rows). Skipping seed.")

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH}")

    # Verify personas
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name FROM personas").fetchall()
    conn.close()
    print(f"\nPersonas in DB ({len(rows)}):")
    for r in rows:
        print(f"  [{r[0]}] {r[1]}")


if __name__ == "__main__":
    main()
