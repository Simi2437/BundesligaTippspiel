import sqlite3

from app.backend.db.database_backend import get_db


def user_count():
    conn = get_db()
    result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    return result[0] if result else 0


def get_all_users():
    rows = get_db().execute("SELECT id, username, is_approved, email FROM users").fetchall()
    return [{"id": r[0], "username": r[1], "is_approved": r[2], "email": r[3]} for r in rows]


def create_user(username, password_hash, email):
    try:
        conn = get_db()

        conn.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)", (username, password_hash, email)
        )
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]

        if user_count() == 1:
            right_id = conn.execute("SELECT id FROM rights WHERE name = ?", ("admin",)).fetchone()[0]
            conn.execute("INSERT INTO user_rights (user_id, right_id) VALUES (?, ?)", (user_id, right_id))
            conn.execute("UPDATE users SET is_approved = TRUE WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_credentials(username, password):
    conn = get_db()
    cur = conn.execute("SELECT id, username FROM users WHERE username = ? AND password_hash = ?", (username, password))
    row = cur.fetchone()
    return {"id": row[0], "username": row[1]} if row else None


def get_user_by_name(username):
    conn = get_db()
    cur = conn.execute("SELECT id, username, password_hash, is_approved FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    return {"id": row[0], "username": row[1], "password_hash": row[2], "is_approved": row[3]} if row else None


def get_user_rights(user_id: int) -> list:
    conn = get_db()
    cur = conn.execute(
        """
        SELECT r.name FROM rights r
        JOIN user_rights ur ON r.id = ur.right_id
        WHERE ur.user_id = ?
    """,
        (user_id,),
    )
    return [row[0] for row in cur.fetchall()]


def set_user_rights(user_id: int, rights: list[str]):
    db = get_db()
    db.execute("DELETE FROM user_rights WHERE user_id = ?", (user_id,))

    for right_name in rights:
        # ID der Berechtigung ermitteln
        result = db.execute("SELECT id FROM rights WHERE name = ?", (right_name,)).fetchone()
        if result is None:
            # Wenn das Recht noch nicht existiert, automatisch hinzufügen
            db.execute("INSERT INTO rights (name) VALUES (?)", (right_name,))
            right_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            right_id = result[0]

        db.execute("INSERT INTO user_rights (user_id, right_id) VALUES (?, ?)", (user_id, right_id))

    db.commit()

def set_user_approval(user_id: int, approved: bool):
    db = get_db()
    db.execute('UPDATE users SET is_approved = ? WHERE id = ?', (int(approved), user_id))
    db.commit()

def reset_user_password_to_null(user_id: int):
    db = get_db()
    db.execute("UPDATE users SET password_hash = NULL WHERE id = ?", (user_id,))
    db.commit()


def set_user_password(username: str, password_hash: str):
    # password_hash = hash_password(password)
    get_db().execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
    get_db().commit()
