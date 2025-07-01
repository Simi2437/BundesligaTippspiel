from nicegui import ui

from app.backend.services import auth_service
from app.backend.uielements.pagestructure import inner_page


@inner_page("/register")
def register_page():
    ui.label("Register")
    email = ui.input("E-Mail")
    username = ui.input("Username")
    password = ui.input("Password", password=True)

    def handle_register():
        if not username.value.strip():
            ui.notify("❌ Bitte einen Benutzernamen angeben.")
            return
        if not password.value.strip():
            ui.notify("❌ Bitte ein Passwort angeben.")
            return
        if not email.value.strip():
            ui.notify("❌ Bitte eine E-Mail-Adresse angeben. Sonst bekommst du nix mit.")
            return
        if auth_service.register(username.value, password.value, email.value):
            ui.notify("Registration successful")
            ui.navigate.to("/login")
        else:
            ui.notify("Username exists")

    ui.button("Register", on_click=handle_register)