from nicegui import ui

from app.backend.services import auth_service
from app.backend.uielements.pagestructure import inner_page


@inner_page("/login")
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

        if result == "NOT_APPROVED":
            ui.notify("🔒 Nutzer ist noch nicht freigeschaltet. Ein Administrator muss den Nutzer freischalten.")
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

    ui.button("Noch kein Konto Registrieren", on_click=lambda: ui.navigate.to("/register"))
    # Button zum Öffnen
    ui.button("🔑 Passwort vergessen?", on_click=dialog.open).props("flat color=secondary")