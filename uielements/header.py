from nicegui import ui

from services.auth_service import current_user, logout


def build_header():
    user = current_user()
    if not user:
        return

    with ui.header().classes('bg-primary text-white'):
        ui.label(f'⚽ Tippspiel - Eingeloggt als {user["username"]} ({user["role"]})')
        ui.button('🏠 Start', on_click=lambda: ui.navigate.to('/')).props('flat').classes('text-white')
        if user['role'] == 'admin':
            ui.button('Teams', on_click=lambda: ui.navigate.to('/config/teams')).props('flat').classes('text-white')
            ui.button('Spieltage', on_click=lambda: ui.navigate.to('/config/spieltage')).props('flat').classes('text-white')
        ui.button('Logout', on_click=lambda: (logout(), ui.navigate.to('/login'))).props('flat').classes('text-white')