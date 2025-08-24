from nicegui import ui
from app.backend.models.user import get_all_users
from app.backend.db.database_backend import get_db

@ui.page("/punktetabelle")
def punktetabelle():
    ui.label("🏆 Punktetabelle").classes("text-2xl my-4")
    users = get_all_users()
    db = get_db()
    rows = []
    for user in users:
        user_id = user["id"]
        username = user["username"]
        punkte = db.execute(
            "SELECT SUM(punkte) FROM tipps WHERE user_id = ?", (user_id,)
        ).fetchone()[0] or 0
        rows.append({"username": username, "punkte": punkte})
    columns = [
        {"name": "username", "label": "Benutzer", "field": "username", "align": "center"},
        {"name": "punkte", "label": "Gesamtpunkte", "field": "punkte", "align": "center"},
    ]
    with ui.table(columns=columns, rows=rows).classes("w-full").props('dense bordered separator="cell"'):
        pass
