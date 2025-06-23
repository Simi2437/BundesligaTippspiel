from nicegui import ui
from starlette.requests import Request

from app.services import auth_service
from app.services.auth_service import is_admin_user


@ui.page("/config/reset_password")
def reset_password_page(request: Request):
    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return
    username = request.query_params.get('username', '')

    ui.label('🔁 Neues Passwort vergeben')

    username_input = ui.input('Benutzername', value=username).props('readonly')
    new_password = ui.input('Neues Passwort', password=True)

    def speichern():
        auth_service.set_user_password_unhashed(username_input.value, new_password.value)
        ui.notify('✅ Passwort gesetzt, bitte einloggen')
        ui.navigate.to('/login')

    ui.button('💾 Passwort speichern', on_click=speichern)
