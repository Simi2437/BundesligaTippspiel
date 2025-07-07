from zoneinfo import ZoneInfo

from nicegui import ui
from datetime import datetime, timezone

from app.backend.models.settings import get_setting, set_setting
from app.backend.models.user_meta import reset_last_reminder_timestamp, get_last_reminder_timestamp
from app.backend.services.auth_service import is_admin_user
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
            date_obj = datetime.strptime(tipp_datum.value, '%Y-%m-%d').date()
            time_obj = datetime.strptime(tipp_uhrzeit.value, '%H:%M').time()
            locale_combined = datetime.combine(date_obj, time_obj)

            local_dt = locale_combined.astimezone(browser_tz)
            utc_dt = local_dt.astimezone(timezone.utc)

            set_setting('saison_name', saison_name_input.value)
            set_setting('tipp_ende', utc_dt.isoformat())
            ui.notify('✅ Einstellungen gespeichert')

        ui.button('💾 Speichern', on_click=speichern)

        ui.separator()

        def reset_reminder():
            reset_last_reminder_timestamp()

        ui.label('🔔 Tipp-Erinnerung').classes('text-lg font-bold mt-4')
        ui.label(f'🔄 Letzte Erinnerung war am: {get_last_reminder_timestamp() or "Nie"}')
        ui.button('🔁 Letzte Erinnerung zurücksetzen', on_click=reset_reminder).props('color=red')
