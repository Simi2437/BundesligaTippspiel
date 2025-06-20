from nicegui import ui

from models.user import get_user_rights
from services.auth_service import logout, current_user


def page():

    user = current_user()

    if not user:
        ui.navigate.to("/login")
        return
    ui.label(f"Willkommen {user['username']}")
    ui.button('🔢 Tippen', on_click=lambda: ui.navigate.to('/game/tippen')).props('flat')
    ui.button('🚪 Logout', on_click=lambda: ui.navigate.to('/logout')).props('flat')
    ui.button('🧑‍💻 Registrieren', on_click=lambda: ui.navigate.to('/register')).props('flat')

    if "admin" in get_user_rights(user["id"]):
        ui.button('📋 Konfiguration Teams', on_click=lambda: ui.navigate.to('/config/teams')).props('flat')
        ui.button('📅 Konfiguration Spieltage', on_click=lambda: ui.navigate.to('/config/spieltage')).props('flat')
        ui.button("📅 Konfiguration Spiel", on_click=lambda: ui.navigate.to("/config/spiel")).props("flat")

