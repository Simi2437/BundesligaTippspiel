from datetime import datetime

from app.backend.db.database_backend import get_db


def get_setting(key: str, default: str = None) -> str:
    row = get_db().execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return row[0] if row else default

def set_setting(key: str, value: str):
    get_db().execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    get_db().commit()


def is_tipp_ende_passed() -> bool:
    tipp_ende_str = get_setting('tipp_ende')
    if not tipp_ende_str:
        return False  # Kein Datum gesetzt = immer offen
    try:
        tipp_ende = datetime.fromisoformat(tipp_ende_str)
        return datetime.now() > tipp_ende
    except Exception:
        return False  # Bei Parsing-Fehler lieber offen lassen