"""
Database layer — SQLite for local dev, swap DATABASE_URL for Supabase/Postgres in prod.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("agentops.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_full   TEXT NOT NULL,
            pr_number   INTEGER NOT NULL,
            result_json TEXT NOT NULL,
            posted      INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(repo_full, pr_number)
        )""")
        conn.commit()


def save_review(repo_full: str, pr_number: int, result: dict):
    init_db()
    with _conn() as conn:
        conn.execute("""
        INSERT INTO reviews (repo_full, pr_number, result_json)
        VALUES (?, ?, ?)
        ON CONFLICT(repo_full, pr_number) DO UPDATE SET
            result_json = excluded.result_json,
            posted = 0,
            created_at = datetime('now')
        """, (repo_full, pr_number, json.dumps(result)))
        conn.commit()


def get_review(repo_full: str, pr_number: int) -> dict | None:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM reviews WHERE repo_full=? AND pr_number=?",
            (repo_full, pr_number)
        ).fetchone()
    if not row:
        return None
    data = json.loads(row["result_json"])
    data["_meta"] = {
        "posted":     bool(row["posted"]),
        "created_at": row["created_at"],
    }
    return data


def mark_posted(repo_full: str, pr_number: int):
    init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE reviews SET posted=1 WHERE repo_full=? AND pr_number=?",
            (repo_full, pr_number)
        )
        conn.commit()
