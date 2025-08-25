import sqlite3
from typing import List, Dict

from app.backend.db.database_backend import get_db
from app.backend.models.settings import get_setting
from app.backend.services.external_game_data.game_data_provider import spiel_service
from app.openligadb.db.database_openligadb import get_oldb

DATA_SOURCE = spiel_service.get_data_source_name()  # z.B. "openligadb"

def get_tipp(user_id, spiel_id):
    row = get_db().execute(
        'SELECT tipp_heim, tipp_gast FROM tipps WHERE user_id = ? AND spiel_id = ? AND datenquelle = ?',
        (user_id, spiel_id, DATA_SOURCE)
    ).fetchone()
    return {'tipp_heim': row[0], 'tipp_gast': row[1]} if row else None

def save_tipp(user_id, spiel_id, heim, gast):
    conn = get_db()
    conn.execute('''
        INSERT INTO tipps (user_id, spiel_id, datenquelle, tipp_heim, tipp_gast)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, spiel_id, datenquelle)
        DO UPDATE SET tipp_heim=excluded.tipp_heim, tipp_gast=excluded.tipp_gast
    ''', (user_id, spiel_id, DATA_SOURCE, heim, gast))
    conn.commit()

def get_tipp_statistik(user_id):
    conn = get_db()
    total = spiel_service.get_anzahl_spiele()
    total_sonder = 5
    getippt = conn.execute(
        'SELECT COUNT(*) FROM tipps WHERE user_id = ? AND datenquelle = ?',
        (user_id, DATA_SOURCE)
    ).fetchone()[0]
    getippt_sonder = conn.execute(
        "SELECT COUNT(*) from tipp_sonder ts where ts.user_id = ? and ts.kategorie = 'Platzierung'", [user_id]
    ).fetchone()[0]
    return getippt + getippt_sonder, (total + total_sonder) - (getippt + getippt_sonder)

def count_tipps_for_spiel(spiel_id: int) -> int:
    db = get_db()
    result = db.execute(
        "SELECT COUNT(*) FROM tipps WHERE spiel_id = ? AND datenquelle = ?",
        (spiel_id, DATA_SOURCE)
    ).fetchone()
    return result[0] if result else 0

def get_enhanced_tipp_statistik(user_id: int) -> dict:
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.execute('''
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN tipp_heim IS NULL OR tipp_gast IS NULL THEN 1 ELSE 0 END) AS offen,
            SUM(CASE WHEN tipp_heim = tipp_gast THEN 1 ELSE 0 END) AS unentschieden,
            SUM(CASE WHEN ABS(tipp_heim - tipp_gast) = 1 THEN 1 ELSE 0 END) AS tor_diff_1,
            SUM(CASE WHEN ABS(tipp_heim - tipp_gast) > 1 THEN 1 ELSE 0 END) AS tor_diff_gt_1
        FROM tipps
        WHERE user_id = ?
    ''', (user_id,))

    row = cursor.fetchone()
    if row['total'] is not None and row['offen'] is not None:
        return {
            'getippt': row['total'] - row['offen'],
            'offen': row['offen'],
            'unentschieden': row['unentschieden'],
            'tor_diff_1': row['tor_diff_1'],
            'tor_diff_gt_1': row['tor_diff_gt_1'],
        }
    return {
        'getippt': 0,
        'offen': 0,
        'unentschieden': 0,
        'tor_diff_1': 0,
        'tor_diff_gt_1': 0,
    }


def get_tipps_for_spieltag(spieltag_id: int, datenquelle: str):
    # Schritt 1: Match-IDs aus OpenLigaDB holen
    conn_ol = get_oldb()
    conn_ol.row_factory = sqlite3.Row
    match_rows = conn_ol.execute(
        'SELECT id FROM matches WHERE group_id = ?', (spieltag_id,)
    ).fetchall()
    match_ids = [row['id'] for row in match_rows]

    if not match_ids:
        return []

    # Schritt 2: Tipps aus lokaler DB holen
    conn = get_db()
    conn.row_factory = sqlite3.Row
    placeholders = ','.join('?' for _ in match_ids)
    query = f'''
        SELECT t.spiel_id, t.tipp_heim, t.tipp_gast, t.punkte, u.username
        FROM tipps t
        JOIN users u ON u.id = t.user_id
        WHERE t.datenquelle = ?
          AND t.spiel_id IN ({placeholders})
    '''
    params = [datenquelle] + match_ids
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_tipps_for_user_by_spieltag(spieltag_id: int, user_id: int, datenquelle: str) -> List[Dict]:
    # Step 1: Hol alle Match-IDs für diesen Spieltag
    conn_ol = get_oldb()
    conn_ol.row_factory = sqlite3.Row
    matches = conn_ol.execute(
        "SELECT id FROM matches WHERE group_id = ?", (spieltag_id,)
    ).fetchall()
    match_ids = [row["id"] for row in matches]

    if not match_ids:
        return []

    # Step 2: Hol alle Tipps zu diesen Matches aus der Tipp-Datenbank
    db = get_db()
    db.row_factory = sqlite3.Row
    placeholders = ','.join('?' for _ in match_ids)
    query = f"""
        SELECT t.spiel_id, t.tipp_heim, t.tipp_gast, t.punkte, u.username
        FROM tipps t
        JOIN users u ON u.id = t.user_id
        WHERE t.user_id = ?
          AND t.datenquelle = ?
          AND t.spiel_id IN ({placeholders})
    """
    params = [user_id, datenquelle] + match_ids
    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def aktualisiere_punkte_fuer_spiel(spiel_id: int):
    """
    Berechnet und aktualisiert die Punkte für alle Tipps zu einem Spiel nach der Bundesliga-Regel.
    """
    from app.backend.services.external_game_data.game_data_provider import spiel_service
    result = spiel_service.get_final_result_for_match(spiel_id)
    if not result:
        print(f"Kein Ergebnis für Spiel {spiel_id} vorhanden.")
        return
    try:
        tore_heim, tore_gast = map(int, result.split(":"))
    except Exception as e:
        print(f"Fehler beim Parsen des Ergebnisses: {result}")
        return
    db = get_db()
    db.row_factory = sqlite3.Row
    tipps = db.execute(
        "SELECT id, tipp_heim, tipp_gast FROM tipps WHERE spiel_id = ? AND datenquelle = ?",
        (spiel_id, DATA_SOURCE)
    ).fetchall()
    for tipp in tipps:
        punkte = 0
        tipp_heim = tipp["tipp_heim"]
        tipp_gast = tipp["tipp_gast"]
        if tipp_heim is None or tipp_gast is None:
            continue
        # Unentschieden
        if tore_heim == tore_gast:
            if tipp_heim == tipp_gast:
                if tipp_heim == tore_heim:
                    punkte = 3  # Exaktes Unentschieden
                elif abs(tipp_heim - tore_heim) == 1:
                    punkte = 2  # Unentschieden, 1 Tor daneben
                else:
                    punkte = 1  # Unentschieden, aber weiter weg
            else:
                punkte = 0
        else:
            # Sieg/Tendenz
            if tipp_heim == tore_heim and tipp_gast == tore_gast:
                punkte = 3  # Exaktes Ergebnis
            elif (tipp_heim - tipp_gast) == (tore_heim - tore_gast):
                punkte = 2  # Richtige Tordifferenz
            elif (tipp_heim > tipp_gast and tore_heim > tore_gast) or (tipp_heim < tipp_gast and tore_heim < tore_gast):
                punkte = 1  # Richtige Tendenz
            else:
                punkte = 0
        db.execute("UPDATE tipps SET punkte = ? WHERE id = ?", (punkte, tipp["id"]))
    db.commit()

def create_punkte_user_context(spieltag_id: int) -> str:
    """
    Erstellt einen Kontext-String mit Punkteständen pro User für einen Spieltag und Gesamt.
    """
    from app.backend.models.user import get_all_users
    db = get_db()
    # Hole alle Spiele des Spieltags aus OpenLigaDB
    conn_ol = get_oldb()
    spiele = conn_ol.execute("SELECT id FROM matches WHERE group_id = ?", (spieltag_id,)).fetchall()
    spiel_ids = [row[0] for row in spiele]
    if not spiel_ids:
        return "Keine Spiele für diesen Spieltag gefunden."
    # Hole alle User
    users = get_all_users()
    beschreibungen = []
    for user in users:
        user_id = user["id"]
        username = user["username"]
        # Punkte für diesen Spieltag
        placeholders = ','.join('?' for _ in spiel_ids)
        punkte_spieltag = db.execute(
            f"SELECT SUM(punkte) FROM tipps WHERE user_id = ? AND spiel_id IN ({placeholders})",
            [user_id] + spiel_ids
        ).fetchone()[0] or 0
        # Gesamtpunkte
        gesamt_punkte = db.execute(
            "SELECT SUM(punkte) FROM tipps WHERE user_id = ?",
            (user_id,)
        ).fetchone()[0] or 0
        beschreibungen.append(f"{username}: {punkte_spieltag} Punkte am Spieltag, {gesamt_punkte} Gesamt")
    return "\n".join(beschreibungen)

def get_all_tipp_statistiken() -> List[dict]:
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.execute('''
        SELECT user_id,
               SUM(CASE WHEN tipp_heim IS NOT NULL AND tipp_gast IS NOT NULL THEN 1 ELSE 0 END) AS getippt,
               SUM(CASE WHEN tipp_heim IS NULL OR tipp_gast IS NULL THEN 1 ELSE 0 END) AS offen
        FROM tipps
        GROUP BY user_id
    ''')
    return [dict(row) for row in cursor.fetchall()]
