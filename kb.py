import sqlite3
import threading
from pathlib import Path
from typing import Any, List, Dict

from hnet.dynamic_chunker import DynamicChunker

DB_PATH = Path("data/kb.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS entries(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, data TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(kind, data, content='entries', content_rowid='id')"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN INSERT INTO entries_fts(rowid, kind, data) VALUES (new.id, new.kind, new.data); END;"
    )
    return conn


def add_entry(**data: Any):
    with _lock:
        conn = _connect()
        conn.execute("INSERT INTO entries(kind,data) VALUES(?,?)", (data.get("kind"), str(data)))
        conn.commit()
        conn.close()


def last(n: int = 5) -> List[dict]:
    conn = _connect()
    rows = conn.execute("SELECT id, kind, data, ts FROM entries ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    conn.close()
    return [dict(id=r[0], kind=r[1], data=r[2], ts=r[3]) for r in rows]


def search(q: str) -> List[dict]:
    conn = _connect()
    rows = conn.execute("SELECT rowid, kind, data FROM entries_fts WHERE entries_fts MATCH ?", (q,)).fetchall()
    conn.close()
    return [dict(id=r[0], kind=r[1], data=r[2]) for r in rows]


def ingest_text(text: str, meta: Dict[str, Any] | None = None) -> None:
    """Ingest long text using dynamic chunking and store each chunk."""
    ch = DynamicChunker(max_tokens=800, overlap_tokens=80)
    for idx, chunk in enumerate(ch.chunk(text)):
        add_entry(kind="kb_chunk", chunk_index=idx, text=chunk, meta=meta or {})


def get(entry_id: int) -> dict:
    conn = _connect()
    row = conn.execute("SELECT id, kind, data, ts FROM entries WHERE id=?", (entry_id,)).fetchone()
    conn.close()
    if row:
        return dict(id=row[0], kind=row[1], data=row[2], ts=row[3])
    return {}
