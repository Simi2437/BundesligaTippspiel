import sqlite3
from typing import List, Dict, Optional

from app.backend.services.external_game_data.base_gamedata_service import BaseGameDataService
from app.openligadb.db.database_openligadb import get_oldb


class OpenLigaGameDataService(BaseGameDataService):

    def get_data_source_name(self):
        return "openligadb"

    def get_available_saisons(self) -> List[str]:
        """Gibt alle vorhandenen Saisons aus der leagues-Tabelle zurück (neueste zuerst)."""
        conn = get_oldb()
        rows = conn.execute("SELECT DISTINCT season FROM leagues ORDER BY season DESC").fetchall()
        return [str(row[0]) for row in rows]

    def get_spieltage(self, saison: Optional[str] = None) -> List[Dict]:
        """Gibt alle Spieltage zurück. Mit saison-Parameter wird nach Saison gefiltert."""
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
        if saison is not None:
            cursor = conn.execute(
                """
                SELECT DISTINCT g.id, g.name, g.order_number
                FROM groups g
                JOIN leagues l ON g.league_id = l.id
                WHERE CAST(l.season AS TEXT) = ?
                ORDER BY g.order_number
                """,
                (saison,)
            )
        else:
            cursor = conn.execute("SELECT DISTINCT id, name, order_number FROM groups ORDER BY order_number")
        result = [dict(row) for row in cursor.fetchall()]
        return result

    def get_spiele_by_spieltag(self, spieltag_id: int) -> List[Dict]:
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT m.id AS id,
                   t1.name AS heim,
                   t2.name AS gast,
                   m.match_date_utc AS spielzeit
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE m.group_id = ?
            ORDER BY m.match_date_utc
        """, (spieltag_id,))
        result = [dict(row) for row in cursor.fetchall()]
        return result

    def get_match_by_id(self, match_id: int) -> Dict:
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT m.*, t1.name AS team1_name, t2.name AS team2_name
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE m.id = ?
        """, (match_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

    def get_anzahl_spiele(self, saison: Optional[str] = None) -> int:
        """Zählt Spiele die einem sichtbaren Spieltag zugeordnet sind. Optional nach Saison gefiltert."""
        conn = get_oldb()
        if saison is not None:
            result = conn.execute(
                """
                SELECT COUNT(*) FROM matches m
                JOIN groups g ON m.group_id = g.id
                JOIN leagues l ON g.league_id = l.id
                WHERE CAST(l.season AS TEXT) = ?
                """,
                (saison,)
            ).fetchone()[0]
        else:
            result = conn.execute(
                'SELECT COUNT(*) FROM matches m JOIN groups g ON m.group_id = g.id'
            ).fetchone()[0]
        return result

    def get_erstes_match_datum(self, saison: Optional[str] = None) -> str:
        conn = get_oldb()
        if saison is not None:
            row = conn.execute(
                """
                SELECT MIN(m.match_date_utc) AS first_match
                FROM matches m
                JOIN groups g ON m.group_id = g.id
                JOIN leagues l ON g.league_id = l.id
                WHERE CAST(l.season AS TEXT) = ?
                """,
                (saison,)
            ).fetchone()
        else:
            row = conn.execute("SELECT MIN(match_date_utc) AS first_match FROM matches").fetchone()
        return row["first_match"] if row and row["first_match"] else None

    def get_alle_teams(self) -> list[dict]:
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT id, name FROM teams ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]

    def get_final_result_for_match(self, match_id: int) -> Optional[str]:
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT points_team1, points_team2 FROM match_results
            WHERE match_id = ? AND result_type_id = 2
            LIMIT 1
            """, (match_id,)
        )
        row = cursor.fetchone()
        if row and row["points_team1"] is not None and row["points_team2"] is not None:
            return f"{row['points_team1']}:{row['points_team2']}"
        return None


