import sqlite3
from datetime import datetime, timezone, timedelta
import logging
logging.basicConfig(level=logging.INFO)

import requests

from app.openligadb.db.database_openligadb import get_oldb


OPENLIGADB_SHORTCUT = 'bl1'
OPENLIGADB_SEASON_FALLBACK = '2025'


def _get_api_url() -> str:
    """Liest die konfigurierte Saison aus den Settings und baut die API-URL zusammen."""
    try:
        from app.backend.models.settings import get_setting
        season = get_setting('openligadb_season', OPENLIGADB_SEASON_FALLBACK)
    except Exception:
        season = OPENLIGADB_SEASON_FALLBACK
    return f'https://api.openligadb.de/getmatchdata/{OPENLIGADB_SHORTCUT}/{season}'


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
        logging.info(f"⚠️ Fehler beim Parsen von 'last_sync': {e}")
        return True  # Im Fehlerfall lieber synchronisieren


class OpenLigaImportError(Exception):
    pass


def is_season_over() -> bool:
    """Gibt True zurück wenn alle Spiele in der lokalen DB beendet sind und das letzte Spiel in der Vergangenheit liegt."""
    conn = get_oldb()
    total = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    if total == 0:
        return False
    unfinished = conn.execute("SELECT COUNT(*) FROM matches WHERE is_finished = 0").fetchone()[0]
    if unfinished > 0:
        return False
    row = conn.execute("SELECT MAX(match_date_utc) FROM matches").fetchone()
    if not row or not row[0]:
        return False
    try:
        last_match = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
        return datetime.now(timezone.utc) > last_match
    except Exception:
        return False


def import_matches(force_import: bool = False):
    if not force_import:
        try:
            from app.backend.models.settings import get_setting
            if get_setting('sync_disabled', 'false') == 'true':
                logging.info("ℹ️ OpenLigaDB-Sync ist manuell deaktiviert.")
                return
        except Exception:
            pass
        if is_season_over():
            logging.info("ℹ️ Saison beendet – OpenLigaDB-Sync wird übersprungen.")
            return
        if not is_sync_due(minutes=120):
            return

    api_url = _get_api_url()
    logging.info(f"🔄 Starte Sync: {api_url}")

    try:
        response = requests.get(api_url)
    except requests.RequestException as e:
        logging.info(f"❌ Fehler beim Abrufen der Daten: {e}")
        raise OpenLigaImportError(f"Fehler beim Abrufen der Daten: {e}")

    try:
        data = response.json()
    except ValueError as e:
        raise OpenLigaImportError(f"Fehler beim Parsen des JSON: {e}")

    conn = get_oldb()
    updated_spieltage = set()
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

        updated_spieltage.add(group['id'])

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
        # Update user points for this match
        try:
            from app.backend.models.tipps import aktualisiere_punkte_fuer_spiel
            aktualisiere_punkte_fuer_spiel(match_id)
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Punkte für Spiel {match_id}: {e}")

    conn.commit()
    # Trigger Kommentator email only for the latest finished Spieltag
    try:
        from app.backend.models.spieltage import get_highest_finished_spieltag
        from app.backend.models.settings import get_last_kommentator_spieltag, set_last_kommentator_spieltag
        from app.backend.tasks.send_tipp_reminder_emails import versende_kommentator_punkte_email
        highest = get_highest_finished_spieltag()
        if highest:
            last_sent = get_last_kommentator_spieltag()
            if highest['nummer'] > last_sent:
                logging.info(f"Spieltag {highest['nummer']} ist jetzt komplett! Kommentator wird ausgelöst.")
                success = versende_kommentator_punkte_email(highest['id'])
                if success:
                    set_last_kommentator_spieltag(highest['nummer'])
                else:
                    logging.info(f"Kommentator-Mail für Spieltag {highest['nummer']} fehlgeschlagen, set_last_kommentator_spieltag wird NICHT gesetzt!")
    except Exception as e:
        logging.info(f"Fehler beim Auslösen des Kommentator-Triggers: {e}")
    now = datetime.now(timezone.utc).isoformat()
    conn.execute('REPLACE INTO sync_meta (key, value) VALUES (?, ?)', ('last_sync', now))
    conn.commit()


def fetch_endtabelle(shortcut: str = 'bl1', season: str = None) -> list:
    """
    Ruft die Abschlusstabelle von OpenLigaDB ab und mappt sie auf lokale Team-IDs.

    Args:
        shortcut: Liga-Kürzel (z.B. 'bl1')
        season: Saison als Jahreszahl-String (z.B. '2024'). Falls None, wird die neueste
                Saison aus der lokalen DB verwendet.

    Returns:
        Liste von Dicts mit keys: platz (int), team_id (int|None), team_name (str), matched (bool)
    """
    conn = get_oldb()
    conn.row_factory = sqlite3.Row

    if season is None:
        row = conn.execute(
            "SELECT season FROM leagues WHERE shortcut = ? ORDER BY season DESC LIMIT 1",
            (shortcut,)
        ).fetchone()
        if not row:
            raise OpenLigaImportError("Keine Saison in der lokalen DB gefunden.")
        season = str(row['season'])

    url = f'https://api.openligadb.de/getbltable/{shortcut}/{season}'
    logging.info(f"Lade Endtabelle von: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise OpenLigaImportError(f"Fehler beim Abrufen der Endtabelle: {e}")
    except ValueError as e:
        raise OpenLigaImportError(f"Fehler beim Parsen der Endtabelle (JSON): {e}")

    result = []
    for i, entry in enumerate(data, start=1):
        team_info_id = entry.get('teamInfoId')
        team_name_api = entry.get('teamName', '')

        # 1. Versuch: Matching per ID
        row = conn.execute(
            "SELECT id, name FROM teams WHERE id = ?", (team_info_id,)
        ).fetchone()

        # 2. Fallback: exakter Namens-Match (case-insensitive)
        if not row:
            row = conn.execute(
                "SELECT id, name FROM teams WHERE LOWER(name) = LOWER(?)", (team_name_api,)
            ).fetchone()

        # 3. Fallback: LIKE-Matching (Teilstring)
        if not row:
            row = conn.execute(
                "SELECT id, name FROM teams WHERE LOWER(name) LIKE LOWER(?)", (f'%{team_name_api}%',)
            ).fetchone()

        if row:
            result.append({
                'platz': i,
                'team_id': row['id'],
                'team_name': row['name'],
                'matched': True,
            })
        else:
            logging.warning(f"Kein lokales Team für '{team_name_api}' (ID {team_info_id}) gefunden.")
            result.append({
                'platz': i,
                'team_id': None,
                'team_name': team_name_api,
                'matched': False,
            })

    return result
