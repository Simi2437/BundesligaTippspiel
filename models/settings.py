from db.database import get_db


def get_setting(key: str, default: str = None) -> str:
    row = get_db().execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return row[0] if row else default

def set_setting(key: str, value: str):
    get_db().execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    get_db().commit()
