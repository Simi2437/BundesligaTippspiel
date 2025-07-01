import sqlite3
from datetime import datetime

from app.backend.db.database_backend import get_db
from typing import Optional

def set_user_meta(user_id: int, key: str, value: str):
    db = get_db()
    db.execute('''
        INSERT OR REPLACE INTO user_meta (user_id, key, value)
        VALUES (?, ?, ?)
    ''', (user_id, key, value))
    db.commit()

def get_user_meta(user_id: int, key: str) -> Optional[str]:
    db = get_db()
    cursor = db.execute('''
        SELECT value FROM user_meta
        WHERE user_id = ? AND key = ?
    ''', (user_id, key))
    row = cursor.fetchone()
    return row["value"] if row else None

REMINDER_KEY = "LAST_REMINDER_SENT"

def get_last_reminder_timestamp():
    db = get_db()
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT value FROM sync_meta WHERE key = ?", (REMINDER_KEY,)).fetchone()
    if row:
        return datetime.fromisoformat(row["value"])
    return None

def set_last_reminder_timestamp():
    db = get_db()
    timestamp = datetime.now().isoformat()
    db.execute(
        "INSERT OR REPLACE INTO sync_meta (key, value) VALUES (?, ?)",
        (REMINDER_KEY, timestamp),
    )
    db.commit()