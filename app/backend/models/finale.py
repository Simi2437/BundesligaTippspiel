import sqlite3
from typing import Dict, Optional

from app.backend.db.database_backend import get_db


# ---------------------------------------------------------------------------
# Finale Ergebnisse (saison-spezifisch)
# ---------------------------------------------------------------------------

def get_finale_ergebnis(saison: str, platz: int) -> Optional[int]:
    """Gibt die Team-ID für den gegebenen Platz in der gegebenen Saison zurück."""
    row = get_db().execute(
        'SELECT team_id FROM finale_ergebnisse WHERE saison = ? AND platz = ?',
        (saison, platz)
    ).fetchone()
    return row[0] if row else None


def get_alle_finale_ergebnisse(saison: str) -> Dict[int, int]:
    """Gibt alle Finale-Ergebnisse für eine Saison als {platz: team_id} zurück."""
    db = get_db()
    db.row_factory = sqlite3.Row
    rows = db.execute(
        'SELECT platz, team_id FROM finale_ergebnisse WHERE saison = ? ORDER BY platz',
        (saison,)
    ).fetchall()
    return {row['platz']: row['team_id'] for row in rows}


def set_finale_ergebnis(saison: str, platz: int, team_id: int):
    """Setzt die Endplatzierung für einen Platz in einer Saison."""
    db = get_db()
    db.execute(
        'INSERT OR REPLACE INTO finale_ergebnisse (saison, platz, team_id) VALUES (?, ?, ?)',
        (saison, platz, team_id)
    )
    db.commit()


def delete_finale_ergebnis(saison: str, platz: int):
    """Löscht eine Endplatzierung."""
    db = get_db()
    db.execute(
        'DELETE FROM finale_ergebnisse WHERE saison = ? AND platz = ?',
        (saison, platz)
    )
    db.commit()


def set_alle_finale_ergebnisse(saison: str, ergebnisse: Dict[int, int]):
    """Setzt alle Endplatzierungen für eine Saison auf einmal (ersetzt vorherige Einträge)."""
    db = get_db()
    for platz, team_id in ergebnisse.items():
        db.execute(
            'INSERT OR REPLACE INTO finale_ergebnisse (saison, platz, team_id) VALUES (?, ?, ?)',
            (saison, platz, team_id)
        )
    db.commit()


# ---------------------------------------------------------------------------
# Sonder-Punkteschema (global / saisonübergreifend)
# ---------------------------------------------------------------------------

def get_sonder_punkte_schema() -> Dict[int, int]:
    """Gibt das gesamte Punkteschema als {platz: punkte} zurück."""
    db = get_db()
    db.row_factory = sqlite3.Row
    rows = db.execute('SELECT platz, punkte FROM sonder_punkte_schema ORDER BY platz').fetchall()
    return {row['platz']: row['punkte'] for row in rows}


def get_sonder_punkte(platz: int, default: int = 0) -> int:
    """Gibt die konfigurierten Punkte für einen bestimmten Platz zurück."""
    row = get_db().execute(
        'SELECT punkte FROM sonder_punkte_schema WHERE platz = ?', (platz,)
    ).fetchone()
    return row[0] if row else default


def set_sonder_punkte_schema(schema: Dict[int, int]):
    """Speichert das gesamte Punkteschema auf einmal."""
    db = get_db()
    for platz, punkte in schema.items():
        db.execute(
            'INSERT OR REPLACE INTO sonder_punkte_schema (platz, punkte) VALUES (?, ?)',
            (platz, punkte)
        )
    db.commit()

