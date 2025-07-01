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
    cursor = db.execute('''
        SELECT user_id, platz, team_id FROM tipp_sonder
        WHERE saison = ? AND kategorie = ?
        ORDER BY platz
    ''', (saison, kategorie))
    return [dict(row) for row in cursor.fetchall()]


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
    return str(row['season']) if row else 'Unbekannt'

