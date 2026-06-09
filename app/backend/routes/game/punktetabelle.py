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
        spiel_punkte = db.execute(
            "SELECT SUM(punkte) FROM tipps WHERE user_id = ?", (user_id,)
        ).fetchone()[0] or 0
        sonder_punkte = db.execute(
            "SELECT SUM(punkte) FROM tipp_sonder WHERE user_id = ? AND punkte IS NOT NULL", (user_id,)
        ).fetchone()[0] or 0
        gesamt = spiel_punkte + sonder_punkte
        user_points.append({
            "username": username,
            "spiel_punkte": spiel_punkte,
            "sonder_punkte": sonder_punkte,
            "gesamt": gesamt,
        })

    user_points.sort(key=lambda x: x["gesamt"], reverse=True)
    total_users = len(user_points)
    for idx, user in enumerate(user_points, start=1):
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

    sonder_berechnet = any(u["sonder_punkte"] > 0 for u in user_points)

    columns = [
        {"name": "platz",        "label": "Platz",           "field": "platz",        "align": "center"},
        {"name": "username",     "label": "Benutzer",        "field": "username",     "align": "center"},
        {"name": "spiel_punkte", "label": "Spieltag-Punkte", "field": "spiel_punkte", "align": "center"},
    ]
    if sonder_berechnet:
        columns.append({"name": "sonder_punkte", "label": "🏆 Sonder-Punkte", "field": "sonder_punkte", "align": "center"})
        columns.append({"name": "gesamt",        "label": "🎯 Gesamt",         "field": "gesamt",        "align": "center"})
    else:
        columns.append({"name": "spiel_punkte_alias", "label": "Gesamtpunkte", "field": "spiel_punkte", "align": "center"})
        # remove duplicate – just use spiel_punkte as gesamt label
        columns = [
            {"name": "platz",        "label": "Platz",         "field": "platz",        "align": "center"},
            {"name": "username",     "label": "Benutzer",      "field": "username",     "align": "center"},
            {"name": "spiel_punkte", "label": "Gesamtpunkte",  "field": "spiel_punkte", "align": "center"},
        ]

    with ui.table(columns=columns, rows=user_points).classes("w-full").props('dense bordered separator="cell"'):
        pass
