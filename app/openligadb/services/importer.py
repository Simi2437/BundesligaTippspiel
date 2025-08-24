import sqlite3
from datetime import datetime, timezone, timedelta

import requests

from app.openligadb.db.database_openligadb import get_oldb


# OpenLiga API Endpoint
API_URL = 'https://api.openligadb.de/getmatchdata/bl1/2025'

def is_sync_due(minutes: int) -> bool:
    conn = get_oldb()
    conn.row_factory = sqlite3.Row

    row = conn.execute("SELECT value FROM sync_meta WHERE key = 'last_sync'").fetchone()
    if not row:
        return True  # Noch nie synchronisiert

    try:
        last_sync = datetime.fromisoformat(row["value"])
        return datetime.now(timezone.utc) - last_sync >= timedelta(minutes=minutes)
    except Exception as e:
        print(f"⚠️ Fehler beim Parsen von 'last_sync': {e}")
        return True  # Im Fehlerfall lieber synchronisieren


class OpenLigaImportError(Exception):
    pass

def import_matches():
    if not is_sync_due(minutes=120):
        return

    try:
        response = requests.get(API_URL)
    except requests.RequestException as e:
        print(f"❌ Fehler beim Abrufen der Daten: {e}")
        raise OpenLigaImportError(f"Fehler beim Abrufen der Daten: {e}")

    try:
        data = response.json()
    except ValueError as e:
        raise OpenLigaImportError(f"Fehler beim Parsen des JSON: {e}")

    conn = get_oldb()
    for match in data:
        # Only process finished matches
        if not match.get('matchIsFinished', False):
            continue

        match_id = match['matchID']
        # Check if local DB already has a final result for this match
        local_result = conn.execute(
            "SELECT 1 FROM match_results WHERE match_id = ? AND result_type_id = 2 LIMIT 1",
            (match_id,)
        ).fetchone()
        # If final result exists, skip unless lastUpdateDateTime changed
        if local_result:
            existing = conn.execute('SELECT last_update FROM matches WHERE id = ?', (match_id,)).fetchone()
            if existing and existing[0] == match['lastUpdateDateTime']:
                continue  # Already up to date

        league = {
            'id': match['leagueId'],
            'shortcut': match['leagueShortcut'],
            'name': match['leagueName'],
            'season': match['leagueSeason']
        }
        group = {
            'id': match['group']['groupID'],
            'league_id': league['id'],
            'name': match['group']['groupName'],
            'order_number': match['group']['groupOrderID']
        }
        team1 = match['team1']
        team2 = match['team2']

        conn.execute('INSERT OR IGNORE INTO leagues (id, shortcut, name, season) VALUES (?, ?, ?, ?)',
                     (league['id'], league['shortcut'], league['name'], league['season']))
        conn.execute('INSERT OR IGNORE INTO groups (id, league_id, name, order_number) VALUES (?, ?, ?, ?)',
                     (group['id'], group['league_id'], group['name'], group['order_number']))
        conn.execute('INSERT OR IGNORE INTO teams (id, name, short_name, icon_url) VALUES (?, ?, ?, ?)',
                     (team1['teamId'], team1['teamName'], team1['shortName'], team1['teamIconUrl']))
        conn.execute('INSERT OR IGNORE INTO teams (id, name, short_name, icon_url) VALUES (?, ?, ?, ?)',
                     (team2['teamId'], team2['teamName'], team2['shortName'], team2['teamIconUrl']))

        existing = conn.execute('SELECT last_update FROM matches WHERE id = ?', (match_id,)).fetchone()
        if existing:
            if existing[0] != match['lastUpdateDateTime']:
                conn.execute('''
                    UPDATE matches SET 
                        league_id = ?, group_id = ?, team1_id = ?, team2_id = ?, 
                        match_date_utc = ?, match_date_local = ?, is_finished = ?, 
                        last_update = ?, viewers = ?
                    WHERE id = ?
                ''', (
                    league['id'], group['id'], team1['teamId'], team2['teamId'],
                    match['matchDateTimeUTC'], match['matchDateTime'],
                    match['matchIsFinished'], match['lastUpdateDateTime'],
                    match.get('numberOfViewers'), match_id
                ))
        else:
            conn.execute('''
                INSERT INTO matches (
                    id, league_id, group_id, team1_id, team2_id, 
                    match_date_utc, match_date_local, is_finished, last_update, viewers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    match_id, league['id'], group['id'],
                    team1['teamId'], team2['teamId'],
                    match['matchDateTimeUTC'], match['matchDateTime'],
                    match['matchIsFinished'], match['lastUpdateDateTime'],
                    match.get('numberOfViewers')
                ))

        # Always update results for finished matches (if new or changed)
        conn.execute('DELETE FROM match_results WHERE match_id = ?', (match_id,))
        for result in match.get('matchResults', []):
            conn.execute('''
                INSERT INTO match_results (
                    match_id, result_type_id, name, points_team1, points_team2
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                match_id,
                result.get('resultTypeID'),
                result.get('resultName'),
                result.get('pointsTeam1'),
                result.get('pointsTeam2')
            ))

    conn.commit()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute('REPLACE INTO sync_meta (key, value) VALUES (?, ?)', ('last_sync', now))
    conn.commit()
