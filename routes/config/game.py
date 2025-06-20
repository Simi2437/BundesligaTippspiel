from nicegui import ui
from datetime import datetime

from models.settings import get_setting, set_setting


@ui.page("/config/game")
def config_game():
    with ui.column().classes('w-full max-w-xl m-auto mt-8 gap-4'):
        ui.label('🛠️ Spielkonfiguration').classes('text-2xl mb-4')

        saison_name_input = ui.input('Saisonname', value=get_setting('saison_name', 'Saison 2025/26'))

        # Hole bestehendes Datum/Zeit
        tipp_ende_str = get_setting('tipp_ende')
        try:
            tipp_dt = datetime.fromisoformat(tipp_ende_str) if tipp_ende_str else datetime.now()
        except Exception:
            tipp_dt = datetime.now()

        ui.label('⏰ Tippende konfigurieren').classes('text-lg font-bold mt-4')
        ui.label('Bis zu diesem Zeitpunkt dürfen Tipps abgegeben werden.').classes('text-sm text-gray-600')
        tipp_datum = ui.date(value=tipp_dt.date()).props('label=Tipp-Ende (Datum)')
        tipp_uhrzeit = ui.time(value=tipp_dt.time()).props('label=Tipp-Ende (Uhrzeit)')

        def speichern():
            combined = datetime.combine(tipp_datum.value, tipp_uhrzeit.value)
            set_setting('saison_name', saison_name_input.value)
            set_setting('tipp_ende', combined.isoformat())
            ui.notify('✅ Einstellungen gespeichert')

        ui.button('💾 Speichern', on_click=speichern)
