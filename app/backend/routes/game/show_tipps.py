from nicegui import ui

from app.backend.models.settings import is_tipp_ende_passed
from app.backend.models.tipps import get_tipps_for_spieltag, get_tipps_for_user_by_spieltag
from app.backend.services.auth_service import current_user
from app.backend.services.external_game_data.game_data_provider import spiel_service

@ui.page("/uebersicht")
def show_all_tipps():
    from app.backend.uielements.header import build_header
    build_header()
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

            # Fallback: recalculate points for matches with missing punkte
            from app.backend.models.tipps import aktualisiere_punkte_fuer_spiel
            for spiel in spiele:
                result = spiel_service.get_final_result_for_match(spiel["id"])
                # Hole is_finished aus der DB
                from app.openligadb.db.database_openligadb import get_oldb
                conn_ol = get_oldb()
                is_finished_row = conn_ol.execute(
                    "SELECT is_finished FROM matches WHERE id = ?", (spiel["id"],)
                ).fetchone()
                is_finished = is_finished_row[0] if is_finished_row else 0

                if result and is_finished:
                    missing_punkte = any(
                        t.get("punkte") is None
                        for t in tipps
                        if t["spiel_id"] == spiel["id"]
                    )
                    if missing_punkte:
                        try:
                            aktualisiere_punkte_fuer_spiel(spiel["id"])
                        except Exception as e:
                            print(f"Fehler beim Nachberechnen der Punkte für Spiel {spiel['id']}: {e}")

            usernames = sorted({t["username"] for t in tipps})

            columns = [
                {"name": "spiel", "label": "Spiel", "field": "spiel", "align": "center"},
                {"name": "result", "label": "Ergebnis", "field": "result", "align": "center"},
            ] + [
                {"name": username, "label": username, "field": username, "align": "center"} for username in usernames
            ]

            tipp_lookup = {}
            for t in tipps:
                tipp_str = f'{t["tipp_heim"]}:{t["tipp_gast"]}' if t["tipp_heim"] is not None and t["tipp_gast"] is not None else "-"
                punkte = t.get("punkte")
                tipp_lookup[(t["spiel_id"], t["username"])] = (tipp_str, punkte)

            rows = []
            for spiel in spiele:
                result = spiel_service.get_final_result_for_match(spiel["id"])
                row = {
                    "spiel": f'{spiel["heim"]} vs {spiel["gast"]}',
                    "result": result if result else "-"
                }
                for username in usernames:
                    tipp_str, punkte = tipp_lookup.get((spiel["id"], username), ("-", None))
                    if tipp_str == "-":
                        row[username] = "-"
                    else:
                        row[username] = f"{tipp_str} ({punkte})" if punkte is not None else f"{tipp_str} –"
                rows.append(row)

            with ui.table(columns=columns, rows=rows).classes("w-full").props(
                    'dense bordered separator="cell"'
            ):
                pass

    else:
        ui.label("Deine Tippübersicht")
        ui.button("🖨️ Drucken", on_click=lambda: ui.run_javascript("window.print()"))\
            .classes("mb-4 no-print")

        for spieltag in spiel_service.get_spieltage():
            spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
            tipps = get_tipps_for_user_by_spieltag(spieltag["id"], user["id"], spiel_service.get_data_source_name())

            ui.label(f'Spieltag {spieltag["order_number"]}').classes("text-xl mt-6")
            # Fallback: recalculate points for matches with missing punkte
            from app.backend.models.tipps import aktualisiere_punkte_fuer_spiel
            for spiel in spiele:
                result = spiel_service.get_final_result_for_match(spiel["id"])
                # Hole is_finished aus der DB
                from app.openligadb.db.database_openligadb import get_oldb
                conn_ol = get_oldb()
                is_finished_row = conn_ol.execute(
                    "SELECT is_finished FROM matches WHERE id = ?", (spiel["id"],)
                ).fetchone()
                is_finished = is_finished_row[0] if is_finished_row else 0

                if result and is_finished:
                    missing_punkte = any(
                        t.get("punkte") is None
                        for t in tipps
                        if t["spiel_id"] == spiel["id"]
                    )
                    if missing_punkte:
                        try:
                            aktualisiere_punkte_fuer_spiel(spiel["id"])
                        except Exception as e:
                            print(f"Fehler beim Nachberechnen der Punkte für Spiel {spiel['id']}: {e}")

            columns = [
                {"name": "spiel", "label": "Spiel", "field": "spiel", "align": "center"},
                {"name": "result", "label": "Ergebnis", "field": "result", "align": "center"},
                {"name": "tipp", "label": "Tipp", "field": "tipp", "align": "center"},
            ]

            rows = []
            for tipp in tipps:
                spiel = next((s for s in spiele if s["id"] == tipp["spiel_id"]), None)
                if not spiel:
                    continue
                result = spiel_service.get_final_result_for_match(spiel["id"])
                tipp_str = f'{tipp["tipp_heim"]}:{tipp["tipp_gast"]}' if tipp["tipp_heim"] is not None and tipp["tipp_gast"] is not None else "-"
                punkte = tipp.get("punkte")
                if tipp_str == "-":
                    tipp_display = "-"
                else:
                    tipp_display = f"{tipp_str} ({punkte})" if punkte is not None else f"{tipp_str} –"
                rows.append({
                    "spiel": f'{spiel["heim"]} vs {spiel["gast"]}',
                    "result": result if result else "-",
                    "tipp": tipp_display,
                })

            with ui.table(columns=columns, rows=rows).classes("w-full").props(
                'dense bordered separator="cell"'
            ):
                pass
