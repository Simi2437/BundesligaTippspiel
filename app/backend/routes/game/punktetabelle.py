from nicegui import ui
from app.backend.models.user import get_all_users
from app.backend.db.database_backend import get_db
from app.backend.uielements.pagestructure import inner_page


@inner_page("/punktetabelle")
def punktetabelle():
    ui.label("🏆 Punktetabelle").classes("text-2xl my-4")
    users = get_all_users()
    db = get_db()
    user_points = []
    for user in users:
        user_id = user["id"]
        username = user["username"]
        punkte = db.execute(
            "SELECT SUM(punkte) FROM tipps WHERE user_id = ?", (user_id,)
        ).fetchone()[0] or 0
        user_points.append({"username": username, "punkte": punkte})

    # Sortiere nach Punkten absteigend
    user_points.sort(key=lambda x: x["punkte"], reverse=True)
    # Vergib Platzierung
    total_users = len(user_points)
    for idx, user in enumerate(user_points, start=1):
        # Emoji logic
        if idx == 1:
            emoji = "🥇"
        elif idx == 2:
            emoji = "🥈"
        elif idx == 3:
            emoji = "🥉"
        elif idx == total_users:
            emoji = "🫣"
        elif idx == total_users - 1 and total_users > 3:
            emoji = "🥲"
        else:
            emoji = "😎"
        user["platz"] = f"{emoji} {idx}"

    columns = [
        {"name": "platz", "label": "Platz", "field": "platz", "align": "center"},
        {"name": "username", "label": "Benutzer", "field": "username", "align": "center"},
        {"name": "punkte", "label": "Gesamtpunkte", "field": "punkte", "align": "center"},
    ]
    with ui.table(columns=columns, rows=user_points).classes("w-full").props('dense bordered separator="cell"'):
        pass
