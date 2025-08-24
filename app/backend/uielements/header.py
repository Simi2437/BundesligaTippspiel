from nicegui import ui

from app.backend.models.user import get_user_rights
from app.backend.services.auth_service import current_user


def build_header():
    user = current_user()
    if not user:
        user = {"username": "Unknown User", "role": "Please Login"}

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("ml-auto items-center"):
            ui.label(f'⚽ Tippspiel - Eingeloggt als {user["username"]}')
            ui.button("🏠 Home", on_click=lambda: ui.navigate.to("/")).props("flat").classes("text-white")
            nav_menu = ui.menu().props('anchor="bottom right" self="top right"')
            with nav_menu:
                with ui.list().classes('w-full'):
                    ui.item("🏠 Home", on_click=lambda: ui.navigate.to("/")).props("flat")
                    ui.item("🔢 Tippen", on_click=lambda: ui.navigate.to("/game/tippen")).props("flat")
                    ui.item('📊 Übersicht', on_click=lambda: ui.navigate.to('/uebersicht')).props('flat')
                    ui.item('💩 Wall of Shame', on_click=lambda: ui.navigate.to('/stats/wall_of_shame'))
                    ui.item('🏆 Punktetabelle', on_click=lambda: ui.navigate.to('/punktetabelle')).props('flat')
                    ui.item("🚪 Logout", on_click=lambda: ui.navigate.to("/logout")).props("flat")
                    if user["username"] == "Unknown User":
                        ui.item("🧑‍💻 Registrieren", on_click=lambda: ui.navigate.to("/register")).props("flat")
                    if "id" in user and "admin" in get_user_rights(user["id"]):
                        #ui.item("⚙️ Admin", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                        #ui.item("📋 Konfiguration Teams", on_click=lambda: ui.navigate.to("/config/teams")).props("flat")
                        # ui.item("📅 Konfiguration Spieltage", on_click=lambda: ui.navigate.to("/config/spieltage")).props(
                        #     "flat"
                        # )
                        ui.item("📅 Konfiguration Spiel", on_click=lambda: ui.navigate.to("/config/game")).props("flat")
                        ui.item('📄 LOG anzeigen', on_click=lambda: ui.navigate.to('/log'))
                        ui.item("👥 Konfiguration Benutzer", on_click=lambda: ui.navigate.to("/config/users")).props(
                            "flat")
                        ui.item("💬 Kommentator anweisen", on_click=lambda: ui.navigate.to("/admin/kommentator")).props(
                            "flat")

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
