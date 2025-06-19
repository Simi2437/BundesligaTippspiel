from nicegui import ui

from services import auth_service
from services.auth_service import SESSION_COOKIE


def login_page():
    ui.label('Login')
    username = ui.input("Username")
    password = ui.input("Password", password = True)

    def handle_login():

        token = auth_service.login(username.value, password.value)
        if token:
            ui.navigate.to("/")
        else:
            ui.notify("Login failed")

    ui.button("Login", on_click=handle_login)

def register_page():
    ui.label("Register")
    username = ui.input("Username")
    password = ui.input("Password", password=True)

    def handle_register():
        if auth_service.register(username.value, password.value):
            ui.notify("Registration successful")
            ui.navigate.to("/login")
        else:
            ui.notify("Username exists")

    ui.button("Register", on_click=handle_register)
