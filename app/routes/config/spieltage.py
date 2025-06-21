from nicegui import ui

from app.db.database import get_db
from app.models.spieltage import get_all_spieltage, get_spiele_by_spieltag, add_spiel, update_spiel, delete_spiel
from app.models.teams import get_all_teams
from app.models.tipps import count_tipps_for_spiel
from app.models.user import get_user_rights
from app.services.auth_service import current_user


def init_spieltage():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM spieltage").fetchone()[0]
    if count == 0:
        for i in range(1, 35):  # 1 bis 34
            conn.execute("INSERT INTO spieltage (nummer) VALUES (?)", (i,))
        conn.commit()


@ui.page("/config/spieltage")
def config_spieltage():
    user = current_user()
    if not user or "admin" not in get_user_rights(user["id"]):
        ui.notify("Kein Zugriff")
        ui.navigate.to("/")
        return

    ui.label("📅 Spieltage verwalten")
    teams = get_all_teams()
    team_options = [(t["name"], t["id"]) for t in teams]
    for spieltag in get_all_spieltage():
        render_spieltag(spieltag, team_options)


def render_spieltag(spieltag, team_options):
    with ui.card().classes("w-full"):
        ui.label(f'Spieltag {spieltag["nummer"]}').classes("text-lg font-bold")

        spieltag_block = ui.column()

        def render_spiele():
            spieltag_block.clear()
            spiele = get_spiele_by_spieltag(spieltag["id"])
            with spieltag_block:
                for s in spiele:
                    with ui.row().classes("items-center gap-4"):
                        heim_sel = (
                            ui.select(team_options, value=(s["heim"], s["heim_id"])).props("dense").classes("w-48")
                        )
                        gast_sel = (
                            ui.select(team_options, value=(s["gast"], s["gast_id"])).props("dense").classes("w-48")
                        )

                        def speichern(s_id=s["id"], h_sel=heim_sel, g_sel=gast_sel):
                            if h_sel.value[1] == g_sel.value[1]:
                                ui.notify("Gleiche Teams nicht erlaubt")
                                return
                            update_spiel(s_id, h_sel.value[1], g_sel.value[1])
                            ui.notify("Gespeichert")
                            render_spiele()

                        def löschen():
                            tipps_count = count_tipps_for_spiel(s["id"])
                            if tipps_count > 0:
                                dialog = ui.dialog().props('persistent').classes('w-[400px]')

                                with dialog:
                                    with ui.card().classes('p-4'):
                                        ui.label(f'⚠️ Für dieses Spiel existieren {tipps_count} Tipps.')
                                        ui.label('Trotzdem löschen?').classes('text-red-700 text-sm mt-1')

                                        with ui.row().classes('justify-end mt-4'):
                                            ui.button('Abbrechen', on_click=dialog.close).props('color=blue text-white')

                                            def confirmed_delete():
                                                delete_spiel(s["id"])
                                                ui.notify("Spiel gelöscht")
                                                render_spiele()
                                                dialog.close()

                                            ui.button('LÖSCHEN', on_click=confirmed_delete).props('color=red text-white')

                                dialog.open()
                            else:
                                delete_spiel(s["id"])
                                ui.notify("Spiel gelöscht")
                                render_spiele()

                        ui.button("💾", on_click=speichern).props("flat").classes("text-green")
                        ui.button("🗑", on_click=löschen).props("flat").classes("text-red")

        render_spiele()
        # neue Spiel-Eingabe
        with ui.row().classes("items-center gap-4"):
            heim = ui.select(team_options, label="Heimteam")
            gast = ui.select(team_options, label="Gastteam")

            def speichern(heim_id=heim, gast_id=gast, sid=spieltag["id"]):
                if heim_id.value == gast_id.value:
                    ui.notify("Heim- und Gastteam dürfen nicht gleich sein")
                    return
                add_spiel(sid, heim_id.value[1], gast_id.value[1])
                ui.notify("Spiel hinzugefügt")
                render_spiele()

            ui.button("➕ Spiel hinzufügen", on_click=speichern).props("flat").classes("bg-primary text-white")
