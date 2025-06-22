from nicegui import ui

from app.models.settings import is_tipp_ende_passed
from app.models.spieltage import (
    get_spiele_by_spieltag,
    get_all_spieltage,
    get_tipps_by_spieltag,
    get_tipps_for_user_by_spieltag,
)
from app.services.auth_service import current_user


@ui.page("/uebersicht")
def show_all_tipps():
    user = current_user()

    ui.add_head_html(
        """
    <style>
    @media print {
        .no-print {
            display: none !important;
        }
    }
    </style>
    """
    )

    if is_tipp_ende_passed():
        ui.label("📄 Übersicht aller Tipps").classes("text-2xl my-4")
        ui.button("🖨️ Drucken", on_click=lambda: ui.run_javascript("window.print()")).classes("mb-4 no-print")

        for spieltag in get_all_spieltage():
            spiele = get_spiele_by_spieltag(spieltag["id"])
            tipps = get_tipps_by_spieltag(spieltag["id"])

            ui.label(f'Spieltag {spieltag["nummer"]}').classes("text-xl mt-6")

            columns = [
                {"name": "spiel", "label": "Spiel", "field": "spiel", "align": "center"},
                {"name": "benutzer", "label": "Benutzer", "field": "benutzer", "align": "center"},
                {"name": "tipp_heim", "label": "Tipp Heim", "field": "tipp_heim", "align": "center"},
                {"name": "tipp_gast", "label": "Tipp Gast", "field": "tipp_gast", "align": "center"},
            ]

            with ui.table(columns=columns, rows=[]).classes("w-full").props(
                    'dense bordered separator="cell"'
            ) as table:
                for tipp in tipps:
                    spiel = next((s for s in spiele if s["id"] == tipp["spiel_id"]), None)
                    if not spiel:
                        continue

                    table.rows.append(
                        {
                            "spiel": f'{spiel["heim"]} vs {spiel["gast"]}',
                            "benutzer": user["username"],
                            "tipp_heim": tipp["tipp_heim"] if tipp and tipp["tipp_heim"] is not None else "",
                            "tipp_gast": tipp["tipp_gast"] if tipp and tipp["tipp_gast"] is not None else "",
                        }
                    )
    else:
        ui.label("Deine Tippübersicht")
        ui.button("🖨️ Drucken", on_click=lambda: ui.run_javascript("window.print()")).classes("mb-4 no-print")

        for spieltag in get_all_spieltage():
            spiele = get_spiele_by_spieltag(spieltag["id"])
            tipps = get_tipps_for_user_by_spieltag(spieltag["id"], user["id"])

            ui.label(f'Spieltag {spieltag["nummer"]}').classes("text-xl mt-6")
            columns = [
                {"name": "spiel", "label": "Spiel", "field": "spiel", "align": "center"},
                {"name": "benutzer", "label": "Benutzer", "field": "benutzer", "align": "center"},
                {"name": "tipp_heim", "label": "Tipp Heim", "field": "tipp_heim", "align": "center"},
                {"name": "tipp_gast", "label": "Tipp Gast", "field": "tipp_gast", "align": "center"},
            ]

            with ui.table(columns=columns, rows=[]).classes("w-full").props(
                'dense bordered separator="cell"'
            ) as table:
                for tipp in tipps:
                    spiel = next((s for s in spiele if s["id"] == tipp["spiel_id"]), None)
                    if not spiel:
                        continue

                    table.rows.append(
                        {
                            "spiel": f'{spiel["heim"]} vs {spiel["gast"]}',
                            "benutzer": user["username"],
                            "tipp_heim": tipp["tipp_heim"] if tipp and tipp["tipp_heim"] is not None else "",
                            "tipp_gast": tipp["tipp_gast"] if tipp and tipp["tipp_gast"] is not None else "",
                        }
                    )
