from zoneinfo import ZoneInfo

from nicegui import ui
from datetime import datetime, timezone

from app.backend.models.settings import get_setting, set_setting
from app.backend.models.user_meta import reset_last_reminder_timestamp, get_last_reminder_timestamp
from app.backend.services.auth_service import is_admin_user
from app.backend.services.external_game_data.game_data_provider import spiel_service
from app.backend.uielements.pagestructure import inner_page_async


@inner_page_async("/config/game")
async def config_game():
    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return

    await ui.context.client.connected()
    timezone_str = await ui.run_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    browser_tz = ZoneInfo(timezone_str or "UTC")

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
                # Robustly handle both string and object input
                if isinstance(tipp_datum.value, str):
                    date_obj = datetime.strptime(tipp_datum.value, '%Y-%m-%d').date()
                else:
                    date_obj = tipp_datum.value  # already a datetime.date

                if isinstance(tipp_uhrzeit.value, str):
                    time_obj = datetime.strptime(tipp_uhrzeit.value, '%H:%M').time()
                else:
                    time_obj = tipp_uhrzeit.value  # already a datetime.time

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

        # --- Punkteschema Sondertipps ---
        alle_teams = spiel_service.get_alle_teams() if spiel_service else []
        n = len(alle_teams)

        ui.label('🎯 Punkte pro richtig getippter Sondertipp-Position').classes('text-lg font-bold mt-4')
        ui.label('Wird beim Berechnen des Finales verwendet.').classes('text-sm text-gray-600')

        punkte_positionen = [
            (1,   'Platz 1 (Meister)',     'sonder_punkte_platz_1',        '10'),
            (2,   'Platz 2 (Vize)',         'sonder_punkte_platz_2',        '7'),
            (3,   'Platz 3',                'sonder_punkte_platz_3',        '5'),
            (n-1, f'Platz {n-1} (Relegation)', 'sonder_punkte_platz_vorletzt', '5'),
            (n,   f'Platz {n} (Absteiger)', 'sonder_punkte_platz_letzt',    '5'),
        ] if n >= 5 else []

        punkte_inputs = {}
        for _, label_txt, setting_key, default in punkte_positionen:
            val = get_setting(setting_key, default)
            punkte_inputs[setting_key] = ui.number(
                label=label_txt, value=int(val), min=0
            ).props('outlined dense')

        def save_punkteschema():
            for key, inp in punkte_inputs.items():
                set_setting(key, str(int(inp.value or 0)))
            ui.notify('✅ Punkteschema gespeichert')

        ui.button('💾 Speichern', on_click=save_punkteschema)

        ui.separator()

        # --- Saisonfinale ---
        ui.label('🏁 Saisonfinale – Echte Endplatzierungen eintragen').classes('text-lg font-bold mt-4')
        ui.label('Trage die echten Endplatzierungen ein und berechne anschließend die Sondertipp-Punkte.').classes('text-sm text-gray-600')

        team_options = [t['name'] for t in alle_teams]
        team_name_to_id = {t['name']: t['id'] for t in alle_teams}
        team_id_to_name = {t['id']: t['name'] for t in alle_teams}

        finale_positionen = [
            (1,   'Platz 1 (Meister)',      'finale_platz_1'),
            (2,   'Platz 2 (Vize)',          'finale_platz_2'),
            (3,   'Platz 3',                 'finale_platz_3'),
            (n-1, f'Platz {n-1} (Relegation)', 'finale_platz_vorletzt'),
            (n,   f'Platz {n} (Absteiger)',  'finale_platz_letzt'),
        ] if n >= 5 else []

        finale_dropdowns = {}
        for _, label_txt, setting_key in finale_positionen:
            team_id_str = get_setting(setting_key)
            current_team = team_id_to_name.get(int(team_id_str)) if team_id_str and team_id_str.isdigit() else None
            finale_dropdowns[setting_key] = ui.select(
                options=team_options, value=current_team, label=label_txt
            ).props('outlined')

        def berechne_finale():
            # Finale-Ergebnisse speichern
            for key, dropdown in finale_dropdowns.items():
                if dropdown.value and dropdown.value in team_name_to_id:
                    set_setting(key, str(team_name_to_id[dropdown.value]))
            # Punkte berechnen
            try:
                from app.backend.models.sondertipps import berechne_sondertipp_punkte, get_aktuelle_saison
                saison = get_aktuelle_saison()
                treffer = berechne_sondertipp_punkte(saison)
                ui.notify(f'✅ Punkte berechnet! {treffer} korrekte Tipps gefunden.')
            except Exception as e:
                ui.notify(f'❌ Fehler: {e}')

        ui.button('🏁 Punkte berechnen', on_click=berechne_finale).props('color=green')

        ui.separator()

        def reset_reminder():
            reset_last_reminder_timestamp()

        ui.label('🔔 Tipp-Erinnerung').classes('text-lg font-bold mt-4')
        ui.label(f'🔄 Letzte Erinnerung war am: {get_last_reminder_timestamp() or "Nie"}')
        ui.button('🔁 Letzte Erinnerung zurücksetzen', on_click=reset_reminder).props('color=red')
