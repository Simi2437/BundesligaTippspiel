from nicegui import ui

from models.user import get_user_rights
from services.auth_service import current_user, logout


def build_header():
    user = current_user()
    if not user:
        user = {"username": "Unknown User", "role": "Please Login"}

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("ml-auto items-center"):
            ui.label(f'⚽ Tippspiel - Eingeloggt als {user["username"]}')
            ui.button("🏠 Home", on_click=lambda: ui.navigate.to("/")).props("flat text-white")
            nav_menu = ui.menu().props('anchor="bottom right" self="top right"')
            with nav_menu:
                ui.button("🔢 Tippen", on_click=lambda: ui.navigate.to("/game/tippen")).props("flat")
                ui.button("🚪 Logout", on_click=lambda: ui.navigate.to("/logout")).props("flat")
                ui.button("🧑‍💻 Registrieren", on_click=lambda: ui.navigate.to("/register")).props("flat")
                if "id" in user and "admin" in get_user_rights(user["id"]):
                    ui.button("⚙️ Admin", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                    ui.button("📋 Konfiguration Teams", on_click=lambda: ui.navigate.to("/config/teams")).props("flat")
                    ui.button("📅 Konfiguration Spieltage", on_click=lambda: ui.navigate.to("/config/spieltage")).props(
                        "flat"
                    )
                    ui.button("📅 Konfiguration Spiel", on_click=lambda: ui.navigate.to("/config/spiel")).props("flat")
            ui.button(icon="menu").props("flat round dense").classes("text-white").on(
                "click", lambda e: nav_menu.open()
            )


#
#        ui.button('🏠 Start', on_click=lambda: ui.navigate.to('/')).props('flat').classes('text-white')
#        ui.button('⚽ Deine Tipps', on_click=lambda: ui.navigate.to('/game/tippen')).props('flat').classes('text-white')
#        if user['role'] == 'admin':
#            ui.button('(Config) Teams', on_click=lambda: ui.navigate.to('/config/teams')).props('flat').classes('text-white')
#            ui.button('(Config) Spieltage', on_click=lambda: ui.navigate.to('/config/spieltage')).props('flat').classes('text-white')
#        ui.button('Logout', on_click=lambda: (logout(), ui.navigate.to('/login'))).props('flat').classes('text-white')
