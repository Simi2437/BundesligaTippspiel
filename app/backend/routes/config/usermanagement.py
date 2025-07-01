from nicegui import ui

from app.backend.models.user import get_all_users, get_user_rights, set_user_rights, reset_user_password_to_null, \
    set_user_approval, delete_user_by_id
from app.backend.services.auth_service import is_admin_user

AVAILABLE_RIGHTS = ['admin']

@ui.page("/config/users")
def config_users():
    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return
    ui.label("🔧 Benutzerverwaltung").classes('text-2xl mb-4')

    for user in get_all_users():
        rights = get_user_rights(user['id'])
        is_approved = user.get('is_approved', False) == 1


        with ui.card().classes('mb-4'):
            ui.label(f'👤 {user["username"]}').classes('text-lg')

            checkboxes = {
                right: ui.checkbox(right, value=(right in rights))
                for right in AVAILABLE_RIGHTS
            }

            approved_checkbox = ui.checkbox('✅ Freigeschaltet', value=is_approved)

            def speichern(u=user, checks=checkboxes, approval_cb=approved_checkbox):
                selected = [r for r, cb in checks.items() if cb.value]
                set_user_rights(u['id'], selected)
                set_user_approval(u['id'], approval_cb.value)
                ui.notify(f'✅ Rechte für {u["username"]} gespeichert')

            def confirm_delete(u=user):
                with ui.dialog() as dialog:
                    with ui.card().classes('w-full max-w-md'):
                        ui.label(f"❗ Benutzer '{u['username']}' wirklich löschen?")
                        confirm_input = ui.input(label='Gib "delete" ein zur Bestätigung').props('outlined dense')
                        with ui.row().classes("justify-end"):
                            ui.button('Abbrechen', on_click=dialog.close)
                            def really_delete():
                                if confirm_input.value.strip().lower() == 'delete':
                                    delete_user_by_id(u['id'])
                                    ui.notify(f"🗑️ Benutzer {u['username']} gelöscht.")
                                    ui.run_javascript('location.reload()')
                                else:
                                    ui.notify('❌ Falsche Bestätigung. Tippe exakt "delete".')
                            ui.button('Löschen', color='red', on_click=really_delete)
                dialog.open()

            ui.button('🗑️ Benutzer löschen', on_click=confirm_delete).props('flat').classes('text-red-600')

            ui.button('💾 Rechte speichern', on_click=speichern).props('flat').classes('text-blue')

            def reset_pwd(u=user):
                reset_user_password_to_null(u['id'])
                ui.notify(f'🔐 Passwort für {u["username"]} zurückgesetzt. Benutzer muss neues Passwort vergeben.')

            ui.button('🛠️ Passwort zurücksetzen', on_click=reset_pwd).props('flat').classes('text-red')
