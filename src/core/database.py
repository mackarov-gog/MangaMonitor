# src/core/database.py
"""
Минимальная синхронная обёртка SQLite для хранения манги/глав/страниц.
DB и папки data/ создаются в корне проекта (MangaMonitor/data).
"""
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

# Project root: ../.. from src/core (file is src/core/database.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "db.sqlite"

_schema = """
CREATE TABLE IF NOT EXISTS manga (
    id INTEGER PRIMARY KEY,
    title TEXT,
    url TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS chapter (
    id INTEGER PRIMARY KEY,
    manga_id INTEGER,
    title TEXT,
    url TEXT UNIQUE,
    saved INTEGER DEFAULT 0,
    FOREIGN KEY(manga_id) REFERENCES manga(id)
);
CREATE TABLE IF NOT EXISTS page (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER,
    page_index INTEGER,
    url TEXT,
    local_path TEXT,
    FOREIGN KEY(chapter_id) REFERENCES chapter(id)
);
"""

def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    return conn

def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.executescript(_schema)
    conn.commit()
    conn.close()

def ensure_manga(title: str, url: str) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO manga(title, url) VALUES (?, ?)", (title, url))
    conn.commit()
    cur.execute("SELECT id FROM manga WHERE url = ?", (url,))
    row = cur.fetchone()
    mid = row[0] if row else None
    conn.close()
    return mid

def ensure_chapter(manga_id: int, title: str, url: str) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO chapter(manga_id, title, url) VALUES (?, ?, ?)", (manga_id, title, url))
    conn.commit()
    cur.execute("SELECT id FROM chapter WHERE url = ?", (url,))
    row = cur.fetchone()
    cid = row[0] if row else None
    conn.close()
    return cid

def save_page(chapter_id: int, page_index: int, url: str, local_path: Optional[str] = None):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO page(chapter_id, page_index, url, local_path) VALUES (?, ?, ?, ?)",
        (chapter_id, page_index, url, local_path)
    )
    conn.commit()
    conn.close()

def mark_chapter_saved(chapter_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE chapter SET saved = 1 WHERE id = ?", (chapter_id,))
    conn.commit()
    conn.close()

def get_manga_list() -> List[Tuple]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, url FROM manga")
    rows = cur.fetchall()
    conn.close()
    return rows
