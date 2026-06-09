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


def _default_punkte(k: int, n: int) -> str:
    """Liefert den Standard-Punktwert für Platz k in einer n-Team-Liga."""
    defaults = {1: '10', 2: '7', 3: '5'}
    if k in defaults:
        return defaults[k]
    if k == n - 1 or k == n:
        return '5'
    return '0'


def _migrate_old_sonder_settings(n: int):
    """Migriert alte Setting-Keys (vorletzt/letzt) in die neuen numerischen Keys."""
    migration_map = {
        'finale_platz_vorletzt': f'finale_platz_{n - 1}',
        'finale_platz_letzt': f'finale_platz_{n}',
        'sonder_punkte_platz_vorletzt': f'sonder_punkte_platz_{n - 1}',
        'sonder_punkte_platz_letzt': f'sonder_punkte_platz_{n}',
        # Alte fehlerhafte Keys aus früherer Version
        'finale_platz_1': 'finale_platz_1',  # kein Rename nötig, nur der Vollständigkeit halber
        'sonder_punkte_platz_1': 'sonder_punkte_platz_1',
        'finale_platz_2': 'finale_platz_2',
        'sonder_punkte_platz_2': 'sonder_punkte_platz_2',
        'finale_platz_3': 'finale_platz_3',
        'sonder_punkte_platz_platz_3': f'sonder_punkte_platz_3',  # möglicher Schreibfehler aus Altversion
    }
    for old_key, new_key in migration_map.items():
        if old_key == new_key:
            continue
        old_val = get_setting(old_key)
        if old_val is not None and get_setting(new_key) is None:
            set_setting(new_key, old_val)


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

    # Einmalige Migration alter Setting-Keys
    if n >= 5:
        _migrate_old_sonder_settings(n)

    with ui.column().classes('w-full max-w-xl m-auto mt-8 gap-4'):
        ui.label('🛠️ Spielkonfiguration').classes('text-2xl mb-4')

        saison_name_input = ui.input('Saisonname', value=get_setting('saison_name', 'Saison 2025/26'))

        # Hole bestehendes Datum/Zeit
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
        from app.openligadb.services.importer import is_season_over
        season_over = is_season_over()
        ui.label('🔄 API-Sync').classes('text-lg font-bold mt-4')
        ui.label(f'Saison-Status: {"✅ Beendet (alle Spiele abgeschlossen)" if season_over else "🟢 Aktiv"}').classes('text-sm text-gray-600')
        sync_disabled_val = get_setting('sync_disabled', 'false') == 'true'
        sync_disabled_cb = ui.checkbox('Sync manuell deaktivieren', value=sync_disabled_val)

        def save_sync():
            set_setting('sync_disabled', 'true' if sync_disabled_cb.value else 'false')
            ui.notify('✅ Sync-Einstellung gespeichert')

        ui.button('💾 Speichern', on_click=save_sync)

        ui.separator()

        if n >= 5:
            # --- Punkteschema Sondertipps ---
            ui.label('🎯 Punkte pro richtig getippter Sondertipp-Position').classes('text-lg font-bold mt-4')
            ui.label(
                'Plätze mit 0 Punkten werden im Tipp-Formular nicht angezeigt.'
            ).classes('text-sm text-gray-600')

            punkte_inputs: dict = {}
            for k in range(1, n + 1):
                setting_key = f'sonder_punkte_platz_{k}'
                val = get_setting(setting_key, _default_punkte(k, n))
                punkte_inputs[k] = ui.number(
                    label=_platz_label(k, n), value=int(val or 0), min=0
                ).props('outlined dense')

            def save_punkteschema():
                for k, inp in punkte_inputs.items():
                    set_setting(f'sonder_punkte_platz_{k}', str(int(inp.value or 0)))
                ui.notify('✅ Punkteschema gespeichert')

            ui.button('💾 Speichern', on_click=save_punkteschema)

            ui.separator()

            # --- Saisonfinale ---
            team_options = [t['name'] for t in alle_teams]
            team_name_to_id = {t['name']: t['id'] for t in alle_teams}
            team_id_to_name = {t['id']: t['name'] for t in alle_teams}

            ui.label('🏁 Saisonfinale – Echte Endplatzierungen eintragen').classes('text-lg font-bold mt-4')
            ui.label(
                'Trage die echten Endplatzierungen ein oder lade sie direkt von OpenLigaDB. '
                'Danach "Speichern & Punkte berechnen" klicken.'
            ).classes('text-sm text-gray-600')

            finale_dropdowns: dict = {}  # k → (setting_key, ui.select)
            for k in range(1, n + 1):
                setting_key = f'finale_platz_{k}'
                team_id_str = get_setting(setting_key)
                current_team = team_id_to_name.get(int(team_id_str)) if team_id_str and team_id_str.isdigit() else None
                finale_dropdowns[k] = (
                    setting_key,
                    ui.select(
                        options=team_options,
                        value=current_team,
                        label=_platz_label(k, n),
                        clearable=True,
                    ).props('outlined'),
                )

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
                            _, dropdown = finale_dropdowns[platz]
                            if entry['matched'] and entry['team_id'] is not None:
                                team_name = team_id_to_name.get(entry['team_id'])
                                if team_name:
                                    dropdown.set_value(team_name)
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
                        ui.notify(f'✅ Endtabelle geladen ({matched} Teams). Bitte prüfen und dann speichern.', type='positive')
                except Exception as e:
                    ui.notify(f'❌ Fehler beim Laden von OpenLigaDB: {e}', type='negative')

            def speichern_und_berechnen():
                """Speichert die Endplatzierungen und berechnet die Sondertipp-Punkte."""
                for k, (setting_key, dropdown) in finale_dropdowns.items():
                    if dropdown.value and dropdown.value in team_name_to_id:
                        set_setting(setting_key, str(team_name_to_id[dropdown.value]))
                try:
                    from app.backend.models.sondertipps import berechne_sondertipp_punkte, get_aktuelle_saison
                    saison = get_aktuelle_saison()
                    treffer = berechne_sondertipp_punkte(saison)
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
