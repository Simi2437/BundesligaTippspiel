from nicegui import ui

from db.database import get_db
from models.user import get_user_rights
from services.auth_service import current_user


@ui.page("/log")
def show_log():
    user = current_user()

    if "admin" not in get_user_rights(user["id"]):
        ui.notify("Zugriff verweigert")
        ui.navigate.to("/")
        return

    rows = (
        get_db()
        .execute("SELECT timestamp, user, action, context FROM action_log ORDER BY id DESC LIMIT 100")
        .fetchall()
    )

    ui.label("🗂️ Action Log").classes("text-2xl mb-4")
    with ui.table(
        columns=["Zeit", "Benutzer", "Aktion", "Details"], rows=[[r[0], r[1], r[2], r[3] or ""] for r in rows]
    ).classes("w-full"):
        pass
