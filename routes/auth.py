from nicegui import ui

from services import auth_service
from services.auth_service import SESSION_COOKIE


def login_page():
    ui.label("Login")
    username = ui.input("Username")
    password = ui.input("Password", password=True)

    def handle_login():
        result = auth_service.login(username.value, password.value)

        if result == "RESET_REQUIRED":
            ui.notify("🔁 Passwort muss neu gesetzt werden")
            ui.navigate.to(f"/config/reset_password?username={username.value}")
            return

        if not result:
            ui.notify("❌ Login fehlgeschlagen")
            return

        ui.navigate.to("/")

    ui.button("Login", on_click=handle_login)
    # 👉 Passwort vergessen Button
    dialog = ui.dialog()
    with dialog:
        with ui.card().classes("p-4"):
            ui.label("❗ Passwort vergessen")
            ui.label(
                "Bitte wende dich an den Administrator,\num dein Passwort zurückzusetzen. \n"
                "(Der Admin muss in der Konfiguration Nutzer das Passwort zurücksetzen)"
            ).classes("text-sm text-gray-700")
            ui.button("OK", on_click=dialog.close).props("color=primary")

    # Button zum Öffnen
    ui.button("🔑 Passwort vergessen?", on_click=dialog.open).props("flat color=secondary")


def register_page():
    ui.label("Register")
    email = ui.input("E-Mail")
    username = ui.input("Username")
    password = ui.input("Password", password=True)

    def handle_register():
        if auth_service.register(username.value, password.value, email.value):
            ui.notify("Registration successful")
            ui.navigate.to("/login")
        else:
            ui.notify("Username exists")

    ui.button("Register", on_click=handle_register)
