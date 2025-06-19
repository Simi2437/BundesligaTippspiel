from nicegui import ui
from services.auth_service import current_user
from models.spieltage import get_all_spieltage, get_spiele_by_spieltag
from models.tipps import get_tipp, save_tipp

@ui.page('/tippen')
def tippen():
    user = current_user()
    if not user:
        ui.notify('Nicht eingeloggt')
        ui.navigate.to('/')
        return

    ui.label('⚽ Deine Tipps').classes('text-xl font-bold')

    for spieltag in get_all_spieltage():
        with ui.card().classes('w-full my-3'):
            ui.label(f'Spieltag {spieltag["nummer"]}').classes('text-lg font-bold')
            spiele = get_spiele_by_spieltag(spieltag["id"])
            for s in spiele:
                tipp = get_tipp(user['id'], s['id']) or {'tipp_heim': '', 'tipp_gast': ''}
                with ui.row().classes('items-center gap-4'):
                    ui.label(f'{s["heim"]} vs {s["gast"]}').classes('w-60')
                    tipp_heim = ui.number(value=tipp['tipp_heim'], min=0).classes('w-20')
                    tipp_gast = ui.number(value=tipp['tipp_gast'], min=0).classes('w-20')

                    def speichern(s_id=s['id'], th=tipp_heim, tg=tipp_gast):
                        save_tipp(user['id'], s_id, th.value, tg.value)
                        ui.notify('Tipp gespeichert')

                    ui.button('💾', on_click=speichern).props('flat').classes('text-green')
