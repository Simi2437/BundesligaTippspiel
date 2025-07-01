import sqlite3
from typing import List, Dict

from app.backend.services.external_game_data.base_gamedata_service import BaseGameDataService
from app.openligadb.db.database_openligadb import get_oldb


class OpenLigaGameDataService(BaseGameDataService):

    def get_data_source_name(self):
        return "openligadb"

    def get_spieltage(self) -> List[Dict]:
        conn = get_oldb()
        conn.row_factory = sqlite3.Row
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


    def get_anzahl_spiele(self) -> int:
        conn = get_oldb()
        result = conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]
        return result

    def get_erstes_match_datum(self) -> str:
        conn = get_oldb()
        row = conn.execute("SELECT MIN(match_date_utc) AS first_match FROM matches").fetchone()
        return row["first_match"] if row and row["first_match"] else None

    def get_alle_teams(self) -> list[dict]:
        conn = get_oldb()
        cursor = conn.execute('SELECT id, name FROM teams ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]