from datetime import datetime, timezone

from app.backend.db.database_backend import get_db
from app.backend.services.external_game_data.game_data_provider import spiel_service


def get_setting(key: str, default: str = None) -> str:
    row = get_db().execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    return row[0] if row else default

def set_setting(key: str, value: str):
    get_db().execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    get_db().commit()


def is_tipp_ende_passed() -> bool:
    tipp_ende_str = get_setting('tipp_ende')

    if not tipp_ende_str:
        # automatisches Initial-Setzen beim ersten Aufruf
        first_match = spiel_service.get_erstes_match_datum()
        if first_match:
            tipp_ende_str = first_match.replace("Z", "+00:00")
            set_setting("tipp_ende", tipp_ende_str)
        else:
            return False  # Keine Spiele, kein Ende

    try:
        tipp_ende = datetime.fromisoformat(tipp_ende_str)
        return datetime.now(timezone.utc) > tipp_ende
    except Exception:
        return False  # Bei Fehler = Tipp offen



def get_days_until_tippende() -> int:
    tipp_ende_str = get_setting("tipp_ende")
    if not tipp_ende_str:
        return -1  # oder None / 0 je nachdem
    try:
        tipp_ende = datetime.fromisoformat(tipp_ende_str).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        delta = tipp_ende - now
        return max(delta.days, 0)
    except Exception as e:
        return -1