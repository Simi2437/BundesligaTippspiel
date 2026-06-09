import sqlite3
from typing import List, Optional, Dict
from app.backend.db.database_backend import get_db
from app.openligadb.db.database_openligadb import get_oldb


def save_sondertipp(user_id: int, saison: str, kategorie: str, platz: int, team_id: int):
    db = get_db()
    db.execute('''
        INSERT OR REPLACE INTO tipp_sonder (user_id, saison, kategorie, platz, team_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, saison, kategorie, platz, team_id))
    db.commit()


def get_sondertipps(user_id: int, saison: str, kategorie: Optional[str] = None) -> List[Dict]:
    db = get_db()
    db.row_factory = sqlite3.Row
    query = 'SELECT platz, team_id, kategorie FROM tipp_sonder WHERE user_id = ? AND saison = ?'
    params = [user_id, saison]

    if kategorie:
        query += ' AND kategorie = ?'
        params.append(kategorie)

    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def delete_sondertipp(user_id: int, saison: str, kategorie: str, platz: int):
    db = get_db()
    db.execute('''
        DELETE FROM tipp_sonder WHERE user_id = ? AND saison = ? AND kategorie = ? AND platz = ?
    ''', (user_id, saison, kategorie, platz))
    db.commit()


def get_all_sondertipps_for_saison(saison: str, kategorie: str) -> List[Dict]:
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.execute('''
        SELECT user_id, platz, team_id, punkte FROM tipp_sonder
        WHERE saison = ? AND kategorie = ?
        ORDER BY platz
    ''', (saison, kategorie))
    return [dict(row) for row in cursor.fetchall()]


def berechne_sondertipp_punkte(saison: str) -> int:
    """
    Berechnet die Punkte für alle Sondertipps der gegebenen Saison und schreibt sie in die DB.
    Liest Finale-Ergebnisse aus der Tabelle finale_ergebnisse und das Punkteschema
    aus sonder_punkte_schema. Gibt die Anzahl der korrekt getippten Positionen zurück.
    """
    from app.backend.models.finale import get_finale_ergebnis, get_sonder_punkte

    db = get_db()
    db.row_factory = sqlite3.Row

    # Alle Tipps für die Saison laden
    tipps = db.execute(
        "SELECT user_id, platz, team_id FROM tipp_sonder WHERE saison = ? AND kategorie = 'Platzierung'",
        (saison,)
    ).fetchall()

    if not tipps:
        return 0

    # Lade konfigurierte Finale-Ergebnisse und Punkte für jeden vorkommenden Platz
    platz_values = sorted(set(tipp['platz'] for tipp in tipps))
    korrekte: Dict[int, tuple] = {}  # platz → (correct_team_id, punkte_wert)
    for platz in platz_values:
        team_id = get_finale_ergebnis(saison, platz)
        if team_id is not None:
            punkte = get_sonder_punkte(platz, default=0)
            korrekte[platz] = (team_id, punkte)

    if not korrekte:
        return 0

    # Punkte berechnen und in DB schreiben
    treffer = 0
    for tipp in tipps:
        platz = tipp['platz']
        if platz in korrekte:
            correct_team_id, punkte_wert = korrekte[platz]
            earned = punkte_wert if tipp['team_id'] == correct_team_id else 0
            db.execute(
                "UPDATE tipp_sonder SET punkte = ? WHERE user_id = ? AND saison = ? AND kategorie = 'Platzierung' AND platz = ?",
                (earned, tipp['user_id'], saison, platz)
            )
            if earned > 0:
                treffer += 1
    db.commit()
    return treffer


def get_aktuelle_saison(shortcut: str = 'bl1') -> str:
    conn = get_oldb()
    cursor = conn.execute('''
        SELECT season
        FROM leagues
        WHERE shortcut = ?
        ORDER BY season DESC
        LIMIT 1
    ''', (shortcut,))
    row = cursor.fetchone()
    return str(row[0]) if row else 'Unbekannt'


def get_available_saisons(shortcut: str = 'bl1') -> list:
    """
    Gibt alle verfügbaren Saisons aus der OpenLigaDB zurück (neueste zuerst).
    Nur Saisons der gegebenen Liga (shortcut).
    """
    conn = get_oldb()
    cursor = conn.execute(
        'SELECT DISTINCT season FROM leagues WHERE shortcut = ? ORDER BY season DESC',
        (shortcut,)
    )
    return [str(row[0]) for row in cursor.fetchall()]


