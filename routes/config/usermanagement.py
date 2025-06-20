from nicegui import ui

from models.user import get_all_users, get_user_rights, set_user_rights, reset_user_password_to_null
from services import auth_service

AVAILABLE_RIGHTS = ['admin']

@ui.page("/config/users")
def config_users():
    ui.label("🔧 Benutzerverwaltung").classes('text-2xl mb-4')

    for user in get_all_users():
        rights = get_user_rights(user['id'])

        with ui.card().classes('mb-4'):
            ui.label(f'👤 {user["username"]}').classes('text-lg')

            checkboxes = {
                right: ui.checkbox(right, value=(right in rights))
                for right in AVAILABLE_RIGHTS
            }

            def speichern(u=user, checks=checkboxes):
                selected = [r for r, cb in checks.items() if cb.value]
                set_user_rights(u['id'], selected)
                ui.notify(f'✅ Rechte für {u["username"]} gespeichert')

            ui.button('💾 Rechte speichern', on_click=speichern).props('flat').classes('text-blue')

            def reset_pwd(u=user):
                reset_user_password_to_null(u['id'])
                ui.notify(f'🔐 Passwort für {u["username"]} zurückgesetzt. Benutzer muss neues Passwort vergeben.')

            ui.button('🛠️ Passwort zurücksetzen', on_click=reset_pwd).props('flat').classes('text-red')
