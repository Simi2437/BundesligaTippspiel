import sqlite3

from db.database import get_db


def user_count():
    conn = get_db()
    result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
    return result[0] if result else 0

def create_user(username, password_hash, role=None):
    try:
        conn = get_db()

        if role is None:
            role = "admin" if user_count() == 0 else "user"

        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                     (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_credentials(username, password):
    conn = get_db()
    cur = conn.execute('SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?',
                       (username, password))
    row = cur.fetchone()
    return {'id': row[0], 'username': row[1], 'role': row[2]} if row else None