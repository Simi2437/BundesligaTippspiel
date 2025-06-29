from nicegui import ui

from app.backend.models.settings import is_tipp_ende_passed
from app.backend.models.tipps import get_tipps_for_spieltag, get_tipps_for_user_by_spieltag
from app.backend.services.auth_service import current_user
from app.backend.services.external_game_data.game_data_provider import spiel_service

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
        ui.button("🖨️ Drucken", on_click=lambda: ui.run_javascript("window.print()"))\
            .classes("mb-4 no-print")

        for spieltag in spiel_service.get_spieltage():
            spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
            tipps = get_tipps_for_spieltag(spieltag["id"], spiel_service.get_data_source_name())

            ui.label(f'Spieltag {spieltag["order_number"]}').classes("text-xl mt-6")

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
                            "benutzer": tipp["username"],
                            "tipp_heim": tipp["tipp_heim"] if tipp["tipp_heim"] is not None else "",
                            "tipp_gast": tipp["tipp_gast"] if tipp["tipp_gast"] is not None else "",
                        }
                    )
    else:
        ui.label("Deine Tippübersicht")
        ui.button("🖨️ Drucken", on_click=lambda: ui.run_javascript("window.print()"))\
            .classes("mb-4 no-print")

        for spieltag in spiel_service.get_spieltage():
            spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
            tipps = get_tipps_for_user_by_spieltag(spieltag["id"], user["id"], spiel_service.get_data_source_name())

            if len(tipps) > 0:
                pass

            ui.label(f'Spieltag {spieltag["order_number"]}').classes("text-xl mt-6")
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
                            "tipp_heim": tipp["tipp_heim"] if tipp["tipp_heim"] is not None else "",
                            "tipp_gast": tipp["tipp_gast"] if tipp["tipp_gast"] is not None else "",
                        }
                    )
