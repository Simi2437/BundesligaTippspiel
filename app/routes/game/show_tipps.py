
from nicegui import ui

from app.models.settings import is_tipp_ende_passed
from app.models.spieltage import get_spiele_by_spieltag, get_all_spieltage, get_tipps_by_spieltag, \
    get_tipps_for_user_by_spieltag
from app.services.auth_service import current_user


@ui.page('/game/show_tipps')
def show_all_tipps():
    user = current_user()

    ui.add_head_html("""
    <style>
    @media print {
        .no-print {
            display: none !important;
        }
    }
    </style>
    """)


    if is_tipp_ende_passed():
        ui.label('📄 Übersicht aller Tipps').classes('text-2xl my-4')
        ui.button('🖨️ Drucken', on_click=lambda: ui.run_javascript('window.print()')).classes('mb-4 no-print')

        for spieltag in get_all_spieltage():
            spiele = get_spiele_by_spieltag(spieltag['id'])
            tipps = get_tipps_by_spieltag(spieltag['id'])

            ui.label(f'Spieltag {spieltag["nummer"]}').classes('text-xl mt-6')

            with ui.table(columns=['Spiel', 'Benutzer', 'Tipp Heim', 'Tipp Gast'], rows=[]).classes('w-full') as table:
                for tipp in tipps:
                    user = tipp['username']
                    spiel = next((s for s in spiele if s['id'] == tipp['spiel_id']), None)
                    if not spiel:
                        continue

                    table.rows.append({
                        'Spiel': f'{spiel["heim_name"]} vs {spiel["gast_name"]}',
                        'Benutzer': user,
                        'Tipp Heim': tipp['tipp_heim'],
                        'Tipp Gast': tipp['tipp_gast']
                    })
    else:
        ui.label("Deine Tippübersicht")
        ui.button('🖨️ Drucken', on_click=lambda: ui.run_javascript('window.print()')).classes('mb-4 no-print')

        for spieltag in get_all_spieltage():
            spiele = get_spiele_by_spieltag(spieltag['id'])
            tipps = get_tipps_for_user_by_spieltag(spieltag['id'], user["id"])

            ui.label(f'Spieltag {spieltag["nummer"]}').classes('text-xl mt-6')

            with ui.table(columns=['Spiel', 'Benutzer', 'Tipp Heim', 'Tipp Gast'], rows=[]).classes('w-full') as table:
                for tipp in tipps:
                    user = tipp['username']
                    spiel = next((s for s in spiele if s['id'] == tipp['spiel_id']), None)
                    if not spiel:
                        continue

                    table.rows.append({
                        'Spiel': f'{spiel["heim_name"]} vs {spiel["gast_name"]}',
                        'Benutzer': user,
                        'Tipp Heim': tipp['tipp_heim'],
                        'Tipp Gast': tipp['tipp_gast']
                    })