import sqlite3
from pathlib import Path
from threading import Lock
import time

DB_PATH = Path('data/kb.db')
LOCK = Lock()


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('''CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL,
        kind TEXT,
        topic TEXT,
        data TEXT
    )''')
    conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(data, content='entries', content_rowid='id')''')
    return conn


def add_entry(kind: str, topic: str, data: str):
    with LOCK:
        conn = _connect()
        ts = time.time()
        cur = conn.cursor()
        cur.execute('INSERT INTO entries (ts, kind, topic, data) VALUES (?,?,?,?)', (ts, kind, topic, data))
        rowid = cur.lastrowid
        cur.execute('INSERT INTO entries_fts(rowid, data) VALUES (?,?)', (rowid, data))
        conn.commit()
        conn.close()
        return rowid


def last(n: int = 10):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT id, ts, kind, topic, data FROM entries ORDER BY id DESC LIMIT ?', (n,))
    rows = cur.fetchall()
    conn.close()
    return rows


def search(query: str, limit: int = 20):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT e.id, e.ts, e.kind, e.topic, e.data FROM entries e JOIN entries_fts f ON e.id=f.rowid WHERE entries_fts MATCH ? ORDER BY e.id DESC LIMIT ?', (query, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def get(entry_id: int):
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT id, ts, kind, topic, data FROM entries WHERE id=?', (entry_id,))
    row = cur.fetchone()
    conn.close()
    return row
