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
        if auth_service.register(username.value, password.value, email.value):
            ui.notify("Registration successful")
            ui.navigate.to("/login")
        else:
            ui.notify("Username exists")

    ui.button("Register", on_click=handle_register)