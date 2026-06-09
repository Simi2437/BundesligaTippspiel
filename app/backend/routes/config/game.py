from zoneinfo import ZoneInfo

from nicegui import ui
from datetime import datetime, timezone

from app.backend.models.settings import get_setting, set_setting
from app.backend.models.user_meta import reset_last_reminder_timestamp, get_last_reminder_timestamp
from app.backend.services.auth_service import is_admin_user
from app.backend.services.external_game_data.game_data_provider import spiel_service
from app.backend.uielements.pagestructure import inner_page_async


def _platz_label(k: int, n: int) -> str:
    """Erzeugt ein sprechendes Label für den k-ten Platz in einer n-Team-Liga."""
    if k == 1:
        return 'Platz 1 (Meister)'
    if k == 2:
        return 'Platz 2 (Vize)'
    if k == n - 1:
        return f'Platz {k} (Relegation)'
    if k == n:
        return f'Platz {k} (Absteiger)'
    return f'Platz {k}'


def _default_punkte(k: int, n: int) -> int:
    """Liefert den Standard-Punktwert für Platz k in einer n-Team-Liga."""
    if k == 1:
        return 10
    if k == 2:
        return 7
    if k == 3:
        return 5
    if k in (n - 1, n):
        return 5
    return 0


def _migrate_settings_to_tables(n: int, aktuelle_saison: str):
    """
    Einmalige Migration: Überträgt alte Settings-basierte Konfiguration in die neuen Tabellen.
    Wird nur ausgeführt, wenn die neuen Tabellen noch keine Daten enthalten.
    """
    from app.backend.models.finale import (
        get_sonder_punkte_schema, set_sonder_punkte_schema,
        get_alle_finale_ergebnisse, set_finale_ergebnis,
    )

    # Punkteschema migrieren (nur wenn Tabelle noch leer)
    if not get_sonder_punkte_schema():
        schema = {}
        for k in range(1, n + 1):
            raw = get_setting(f'sonder_punkte_platz_{k}')
            schema[k] = int(raw) if raw and raw.isdigit() else _default_punkte(k, n)
        set_sonder_punkte_schema(schema)

    # Finale-Ergebnisse migrieren (nur wenn für diese Saison noch keine Daten)
    if not get_alle_finale_ergebnisse(aktuelle_saison):
        for k in range(1, n + 1):
            old_val = (
                get_setting(f'finale_platz_{aktuelle_saison}_{k}')
                or get_setting(f'finale_platz_{k}')
            )
            if old_val and old_val.isdigit():
                set_finale_ergebnis(aktuelle_saison, k, int(old_val))


@inner_page_async("/config/game")
async def config_game():
    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return

    await ui.context.client.connected()
    timezone_str = await ui.run_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    browser_tz = ZoneInfo(timezone_str or "UTC")

    alle_teams = spiel_service.get_alle_teams() if spiel_service else []
    n = len(alle_teams)

    from app.backend.models.sondertipps import get_aktuelle_saison
    aktuelle_saison = get_aktuelle_saison()

    # Einmalige Migration alter Settings in die neuen Tabellen
    if n >= 5:
        _migrate_settings_to_tables(n, aktuelle_saison)

    with ui.column().classes('w-full max-w-xl m-auto mt-8 gap-4'):
        ui.label('🛠️ Spielkonfiguration').classes('text-2xl mb-4')

        saison_name_input = ui.input('Saisonname', value=get_setting('saison_name', 'Saison 2025/26'))

        tipp_ende_str = get_setting('tipp_ende')
        try:
            tipp_dt = datetime.fromisoformat(tipp_ende_str) if tipp_ende_str else datetime.now(browser_tz)
            tipp_dt_locale = tipp_dt.astimezone(browser_tz)
        except Exception:
            tipp_dt_locale = datetime.now(browser_tz)

        ui.label('⏰ Tippende konfigurieren').classes('text-lg font-bold mt-4')
        ui.label('Bis zu diesem Zeitpunkt dürfen Tipps abgegeben werden.').classes('text-sm text-gray-600')
        tipp_datum = ui.date(value=tipp_dt_locale.date()).props('label=Tipp-Ende (Datum)')
        tipp_uhrzeit = ui.time(value=tipp_dt_locale.time()).props('label=Tipp-Ende (Uhrzeit)')

        def speichern():
            try:
                if isinstance(tipp_datum.value, str):
                    date_obj = datetime.strptime(tipp_datum.value, '%Y-%m-%d').date()
                else:
                    date_obj = tipp_datum.value
                if isinstance(tipp_uhrzeit.value, str):
                    time_obj = datetime.strptime(tipp_uhrzeit.value, '%H:%M').time()
                else:
                    time_obj = tipp_uhrzeit.value
                naive_dt = datetime.combine(date_obj, time_obj)
                aware_dt = naive_dt.replace(tzinfo=browser_tz)
                utc_dt = aware_dt.astimezone(timezone.utc)
                set_setting('saison_name', saison_name_input.value)
                set_setting('tipp_ende', utc_dt.isoformat())
                ui.notify('✅ Einstellungen gespeichert')
            except Exception as e:
                ui.notify(f'❌ Fehler beim Speichern: {e}')

        ui.button('💾 Speichern', on_click=speichern)

        ui.separator()

        # --- Sync-Konfiguration ---
        from app.openligadb.services.importer import is_season_over, OPENLIGADB_SEASON_FALLBACK, OPENLIGADB_SHORTCUT
        season_over = is_season_over()
        ui.label('🔄 API-Sync').classes('text-lg font-bold mt-4')
        ui.label(
            f'Saison-Status: {"✅ Beendet (alle Spiele abgeschlossen)" if season_over else "🟢 Aktiv"}'
        ).classes('text-sm text-gray-600')

        current_season = get_setting('openligadb_season', OPENLIGADB_SEASON_FALLBACK)
        api_url_preview = f'https://api.openligadb.de/getmatchdata/{OPENLIGADB_SHORTCUT}/{current_season}'
        ui.label('⚽ Saison (OpenLigaDB)').classes('text-sm font-semibold mt-2')
        ui.label(f'Aktuelle API-URL: {api_url_preview}').classes('text-xs text-gray-500 mb-1')
        season_input = ui.input(
            label='Saison-Jahr (z. B. 2026)',
            value=current_season,
        ).props('outlined dense').classes('w-48')
        ui.label('Tipp: Saison wechseln → neues Jahr eintragen → erst testen, dann speichern.') \
            .classes('text-xs text-gray-400 mb-2')

        api_check_label = ui.label('').classes('text-sm')
        api_check_state = {'ok': False}

        def check_api():
            import requests as _requests
            new_season = season_input.value.strip()
            if not new_season.isdigit() or len(new_season) != 4:
                api_check_label.set_text('❌ Kein gültiges Saison-Jahr.')
                api_check_label.classes(remove='text-green-600', add='text-red-600')
                api_check_state['ok'] = False
                return
            url = f'https://api.openligadb.de/getmatchdata/{OPENLIGADB_SHORTCUT}/{new_season}'
            try:
                resp = _requests.get(url, timeout=8)
                resp.raise_for_status()
                data = resp.json()
                count = len(data) if isinstance(data, list) else '?'
                api_check_label.set_text(f'✅ Endpunkt erreichbar – {count} Spiele gefunden ({url})')
                api_check_label.classes(remove='text-red-600', add='text-green-600')
                api_check_state['ok'] = True
            except _requests.exceptions.HTTPError as e:
                api_check_label.set_text(f'❌ HTTP-Fehler: {e}')
                api_check_label.classes(remove='text-green-600', add='text-red-600')
                api_check_state['ok'] = False
            except Exception as e:
                api_check_label.set_text(f'❌ Verbindungsfehler: {e}')
                api_check_label.classes(remove='text-green-600', add='text-red-600')
                api_check_state['ok'] = False

        sync_disabled_val = get_setting('sync_disabled', 'false') == 'true'
        sync_disabled_cb = ui.checkbox('Sync manuell deaktivieren', value=sync_disabled_val)

        def save_sync():
            new_season = season_input.value.strip()
            if not new_season.isdigit() or len(new_season) != 4:
                ui.notify('❌ Saison muss eine 4-stellige Jahreszahl sein (z. B. 2026)', type='negative')
                return
            if not api_check_state['ok']:
                ui.notify('⚠️ Bitte erst den API-Endpunkt erfolgreich testen bevor du speicherst.', type='warning')
                return
            set_setting('openligadb_season', new_season)
            set_setting('sync_disabled', 'true' if sync_disabled_cb.value else 'false')
            updated_url = f'https://api.openligadb.de/getmatchdata/{OPENLIGADB_SHORTCUT}/{new_season}'
            ui.notify(f'✅ Gespeichert – neue API-URL: {updated_url}')

        with ui.row().classes('gap-2 mt-1'):
            ui.button('🔍 Endpunkt testen', on_click=check_api).props('color=blue outline')
            ui.button('💾 Speichern', on_click=save_sync)

        ui.separator()

        if n >= 5:
            from app.backend.models.finale import (
                get_sonder_punkte_schema, set_sonder_punkte_schema,
                get_alle_finale_ergebnisse, set_alle_finale_ergebnisse,
            )

            # --- Punkteschema Sondertipps ---
            ui.label('🎯 Punkte pro richtig getippter Sondertipp-Position').classes('text-lg font-bold mt-4')
            ui.label(
                'Plätze mit 0 Punkten werden im Tipp-Formular nicht angezeigt.'
            ).classes('text-sm text-gray-600')

            schema_aktuell = get_sonder_punkte_schema()
            punkte_inputs: dict = {}
            for k in range(1, n + 1):
                val = schema_aktuell.get(k, _default_punkte(k, n))
                punkte_inputs[k] = ui.number(
                    label=_platz_label(k, n), value=val, min=0
                ).props('outlined dense')

            def save_punkteschema():
                set_sonder_punkte_schema({k: int(inp.value or 0) for k, inp in punkte_inputs.items()})
                ui.notify('✅ Punkteschema gespeichert')

            ui.button('💾 Speichern', on_click=save_punkteschema)

            ui.separator()

            # --- Saisonfinale ---
            team_options = [t['name'] for t in alle_teams]
            team_name_to_id = {t['name']: t['id'] for t in alle_teams}
            team_id_to_name = {t['id']: t['name'] for t in alle_teams}

            ui.label('🏁 Saisonfinale – Echte Endplatzierungen eintragen').classes('text-lg font-bold mt-4')
            ui.label(
                f'Saison {aktuelle_saison} – Trage die Endplatzierungen ein oder lade sie von OpenLigaDB. '
                'Danach "Speichern & Punkte berechnen" klicken.'
            ).classes('text-sm text-gray-600')

            ergebnisse_aktuell = get_alle_finale_ergebnisse(aktuelle_saison)
            finale_dropdowns: dict = {}  # k → ui.select
            for k in range(1, n + 1):
                team_id = ergebnisse_aktuell.get(k)
                current_team = team_id_to_name.get(team_id) if team_id else None
                finale_dropdowns[k] = ui.select(
                    options=team_options,
                    value=current_team,
                    label=_platz_label(k, n),
                    clearable=True,
                ).props('outlined')

            async def lade_von_openligadb():
                """Lädt die aktuelle Endtabelle von OpenLigaDB und befüllt die Dropdowns."""
                try:
                    import sqlite3 as _sqlite3
                    from app.openligadb.services.importer import fetch_endtabelle
                    from app.openligadb.db.database_openligadb import get_oldb

                    conn = get_oldb()
                    conn.row_factory = _sqlite3.Row
                    row = conn.execute(
                        "SELECT shortcut, season FROM leagues ORDER BY season DESC LIMIT 1"
                    ).fetchone()
                    shortcut = row['shortcut'] if row else 'bl1'
                    season = str(row['season']) if row else None

                    tabelle = fetch_endtabelle(shortcut=shortcut, season=season)

                    unmatched = []
                    matched = 0
                    for entry in tabelle:
                        platz = entry['platz']
                        if platz in finale_dropdowns:
                            if entry['matched'] and entry['team_id'] is not None:
                                team_name = team_id_to_name.get(entry['team_id'])
                                if team_name:
                                    finale_dropdowns[platz].set_value(team_name)
                                    matched += 1
                                else:
                                    unmatched.append(f"Platz {platz}: {entry['team_name']}")
                            else:
                                unmatched.append(f"Platz {platz}: {entry['team_name']}")

                    if unmatched:
                        ui.notify(
                            f"⚠️ {matched} Teams geladen. Nicht gefunden: {', '.join(unmatched[:5])}"
                            f"{'...' if len(unmatched) > 5 else ''}",
                            type='warning',
                            timeout=8000,
                        )
                    else:
                        ui.notify(
                            f'✅ Endtabelle geladen ({matched} Teams). Bitte prüfen und dann speichern.',
                            type='positive',
                        )
                except Exception as e:
                    ui.notify(f'❌ Fehler beim Laden von OpenLigaDB: {e}', type='negative')

            def speichern_und_berechnen():
                """Speichert Endplatzierungen in finale_ergebnisse und berechnet Sondertipp-Punkte."""
                ergebnisse: dict = {}
                for k, dropdown in finale_dropdowns.items():
                    if dropdown.value and dropdown.value in team_name_to_id:
                        ergebnisse[k] = team_name_to_id[dropdown.value]
                set_alle_finale_ergebnisse(aktuelle_saison, ergebnisse)
                try:
                    from app.backend.models.sondertipps import berechne_sondertipp_punkte
                    treffer = berechne_sondertipp_punkte(aktuelle_saison)
                    ui.notify(f'✅ Gespeichert & Punkte berechnet! {treffer} korrekte Tipps gefunden.')
                except Exception as e:
                    ui.notify(f'❌ Fehler beim Berechnen: {e}')

            with ui.row().classes('gap-2 mt-2 flex-wrap'):
                ui.button('🌐 Von OpenLigaDB laden', on_click=lade_von_openligadb).props('color=blue')
                ui.button('🏁 Speichern & Punkte berechnen', on_click=speichern_und_berechnen).props('color=green')

        ui.separator()

        def reset_reminder():
            reset_last_reminder_timestamp()

        ui.label('🔔 Tipp-Erinnerung').classes('text-lg font-bold mt-4')
        ui.label(f'🔄 Letzte Erinnerung war am: {get_last_reminder_timestamp() or "Nie"}')
        ui.button('🔁 Letzte Erinnerung zurücksetzen', on_click=reset_reminder).props('color=red')
