from nicegui import ui

from services.auth_service import logout, current_user


def page():

    user = current_user()

    if not user:
        ui.navigate.to("/login")
        return
    ui.label(f"Welcome {user["username"]}, Role: {user["role"]}")
    ui.button("Logout", on_click=lambda: ui.navigate.to("/logout"))

    if user["role"] == "admin":
        ui.button("🛠 Teams verwalten", on_click=lambda : ui.navigate.to("config/teams"))
        ui.button("🛠 Spieltage verwalten", on_click=lambda : ui.navigate.to("config/spieltage"))

