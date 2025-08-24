from nicegui import ui

from app.backend.models.tipps import get_tipp_statistik
from app.backend.models.user import get_user_rights
from app.backend.services.auth_service import current_user


def page():

    user = current_user()

    if not user:
        ui.navigate.to("/login")
        return
    ui.label(f"Willkommen {user['username']}")
    ui.button('🔢 Tippen', on_click=lambda: ui.navigate.to('/game/tippen'))
    ui.button('📊 Übersicht', on_click=lambda: ui.navigate.to('/uebersicht'))
    ui.button('🚪 Logout', on_click=lambda: ui.navigate.to('/logout'))
    ui.button('💩 Wall of Shame', on_click=lambda: ui.navigate.to('/stats/wall_of_shame'))
    ui.button('🏆 Punktetabelle', on_click=lambda: ui.navigate.to('/punktetabelle'))
    #ui.button('🧑‍💻 Registrieren', on_click=lambda: ui.navigate.to('/register'))


    getippt, offen = get_tipp_statistik(user['id'])
    ui.label(f'Du hast {getippt} von {getippt + offen} Spielen getippt.')

    ui.echart({
        'tooltip': {'trigger': 'item'},
        'legend': {'bottom': '0%'},
        "color": ["#4CAF50", "#FF5500"],
        'series': [{
            'name': 'Tipp-Status',
            'type': 'pie',
            'radius': '60%',
            'data': [
                {'value': getippt, 'name': 'Getippt'},
                {'value': offen, 'name': 'Offen'},
            ],
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 10,
                    'shadowOffsetX': 0,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    }).classes('w-96 h-96')

    if "admin" in get_user_rights(user["id"]):
        #ui.button('📋 Konfiguration Teams', on_click=lambda: ui.navigate.to('/config/teams'))
        #ui.button('📅 Konfiguration Spieltage', on_click=lambda: ui.navigate.to('/config/spieltage'))
        ui.button("📅 Konfiguration Spiel", on_click=lambda: ui.navigate.to("/config/game"))
        ui.button('📄 LOG anzeigen', on_click=lambda: ui.navigate.to('/log'))
        ui.button("👥 Konfiguration Benutzer", on_click=lambda: ui.navigate.to("/config/users"))
        ui.button("💬 Kommentator anweisen", on_click=lambda: ui.navigate.to("/admin/kommentator"))

