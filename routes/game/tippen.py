from datetime import datetime

from nicegui import ui

from models.settings import get_setting
from services.auth_service import current_user
from models.spieltage import get_all_spieltage, get_spiele_by_spieltag
from models.tipps import get_tipp, save_tipp

@ui.page('/game/tippen')
def tippen():
    user = current_user()
    if not user:
        ui.notify('Nicht eingeloggt')
        ui.navigate.to('/')
        return

    with ui.row().classes('w-full items-center justify-between'):
        ui.label('📋 Deine Tipps').classes('text-xl')

        tipp_ende_str = get_setting('tipp_ende')
        if tipp_ende_str:
            try:
                tipp_ende = datetime.fromisoformat(tipp_ende_str)
                ui.label(f'Tippende: {tipp_ende.strftime("%d.%m.%Y %H:%M")}').classes('text-sm text-gray-600')
            except Exception:
                ui.label('⚠️ Tippende-Format ungültig').classes('text-sm text-red-500')
        else:
            ui.label('⚠️ Admin muss Tippende konfigurieren').classes('text-sm text-orange-600')



    for spieltag in get_all_spieltage():
        with ui.card().classes('w-full my-3'):
            ui.label(f'Spieltag {spieltag["nummer"]}').classes('text-lg font-bold')
            spiele = get_spiele_by_spieltag(spieltag["id"])
            for spiel in spiele:
                tipp = get_tipp(user['id'], spiel['id']) or {'tipp_heim': None, 'tipp_gast': None}
                with ui.row().classes('items-center gap-4'):
                    ui.label(f'{spiel["heim"]} vs {spiel["gast"]}').classes('w-30')
                    tipp_heim = ui.number(value=tipp['tipp_heim'], min=0).classes('w-20')
                    ui.label(f":")
                    tipp_gast = ui.number(value=tipp['tipp_gast'], min=0).classes('w-20')

                    def speichern(s_id=spiel['id'], th=tipp_heim, tg=tipp_gast):
                        save_tipp(user['id'], s_id, th.value, tg.value)
                        ui.notify('Tipp gespeichert')

                    ui.button('💾', on_click=speichern).props('flat').classes('text-green')
