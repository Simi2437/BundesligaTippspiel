import sqlite3

from db.database import get_db


def user_count():
    conn = get_db()
    result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
    return result[0] if result else 0

def create_user(username, password_hash, email):
    try:
        conn = get_db()

        conn.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                     (username, password_hash, email))
        user_id = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()[0]

        if user_count() == 1:
            right_id = conn.execute('SELECT id FROM rights WHERE name = ?', ('admin',)).fetchone()[0]
            conn.execute('INSERT INTO user_rights (user_id, right_id) VALUES (?, ?)', (user_id, right_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_credentials(username, password):
    conn = get_db()
    cur = conn.execute('SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
                       (username, password))
    row = cur.fetchone()
    return {'id': row[0], 'username': row[1]} if row else None

def get_user_rights(user_id: int) -> list:
    conn = get_db()
    cur = conn.execute('''
        SELECT r.name FROM rights r
        JOIN user_rights ur ON r.id = ur.right_id
        WHERE ur.user_id = ?
    ''', (user_id,))
    return [row[0] for row in cur.fetchall()]