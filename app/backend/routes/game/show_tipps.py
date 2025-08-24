from nicegui import ui
import io
from openpyxl import Workbook

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
        def generate_tipps_excel():
            wb = Workbook()
            ws = wb.active
            ws.title = "Tipps"
            # Sammle alle Usernamen aus allen Tipps aller Spieltage
            all_usernames = set()
            spieltage = spiel_service.get_spieltage()
            for spieltag in spieltage:
                tipps = get_tipps_for_spieltag(spieltag["id"], spiel_service.get_data_source_name())
                all_usernames.update(t["username"] for t in tipps)
            usernames = sorted(all_usernames)
            ws.append(["Spieltag", "Spiel", "Ergebnis"] + usernames)
            for spieltag in spieltage:
                spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
                tipps = get_tipps_for_spieltag(spieltag["id"], spiel_service.get_data_source_name())
                tipp_lookup = {}
                for t in tipps:
                    tipp_str = f'{t["tipp_heim"]}:{t["tipp_gast"]}' if t["tipp_heim"] is not None and t["tipp_gast"] is not None else "-"
                    punkte = t.get("punkte")
                    tipp_lookup[(t["spiel_id"], t["username"])] = f"{tipp_str} ({punkte})" if punkte is not None else f"{tipp_str} –"
                for spiel in spiele:
                    result = spiel_service.get_final_result_for_match(spiel["id"])
                    row = [spieltag["order_number"], f'{spiel["heim"]} vs {spiel["gast"]}', result if result else "-"]
                    for username in usernames:
                        row.append(tipp_lookup.get((spiel["id"], username), "-"))
                    ws.append(row)
            # Sondertipps/Platzierungstipps exportieren
            from app.backend.models.sondertipps import get_aktuelle_saison, get_all_sondertipps_for_saison
            saison = get_aktuelle_saison()
            platzierungstipps = get_all_sondertipps_for_saison(saison, "Platzierung")
            # Hole alle Usernamen aus den Sondertipps dazu
            from app.backend.models.user import get_user_by_id
            alle_teams = spiel_service.get_alle_teams()
            team_id_to_name = {team["id"]: team["name"] for team in alle_teams}
            # Finde alle Plätze, die getippt wurden
            alle_plaetze = sorted({t["platz"] for t in platzierungstipps})
            # Mapping: user_id -> username
            user_id_to_name = {}
            for tipp in platzierungstipps:
                if tipp["user_id"] not in user_id_to_name:
                    user = get_user_by_id(tipp["user_id"])
                    user_id_to_name[tipp["user_id"]] = user["username"] if user else str(tipp["user_id"])
            # Sheet für Sondertipps
            ws_sonder = wb.create_sheet("Sondertipps")
            ws_sonder.append(["Username"] + [f"Platz {p}" for p in alle_plaetze])
            # Für jeden User: Zeile mit getippten Teams pro Platz
            for user_id, username in user_id_to_name.items():
                row = [username]
                for platz in alle_plaetze:
                    team_name = next((team_id_to_name[t["team_id"]] for t in platzierungstipps if t["user_id"] == user_id and t["platz"] == platz), "-")
                    row.append(team_name)
                ws_sonder.append(row)
            bio = io.BytesIO()
            wb.save(bio)
            bio.seek(0)
            return bio.read()


        def download_excel():
            data = generate_tipps_excel()
            ui.download(data, "BundesligaTippspiel_Tipps.xlsx")
        ui.button("📥 Excel-Export", on_click=download_excel).classes("mb-4 no-print")

        # Sondertipps/Platzierungstipps Übersicht
        from app.backend.models.sondertipps import get_aktuelle_saison, get_all_sondertipps_for_saison
        saison = get_aktuelle_saison()
        platzierungstipps = get_all_sondertipps_for_saison(saison, "Platzierung")
        from app.backend.models.user import get_user_by_id
        alle_teams = spiel_service.get_alle_teams()
        team_id_to_name = {team["id"]: team["name"] for team in alle_teams}
        alle_plaetze = sorted({t["platz"] for t in platzierungstipps})
        user_id_to_name = {}
        for tipp in platzierungstipps:
            if tipp["user_id"] not in user_id_to_name:
                user = get_user_by_id(tipp["user_id"])
                user_id_to_name[tipp["user_id"]] = user["username"] if user else str(tipp["user_id"])
        # Tabelle vorbereiten
        columns = [
            {"name": "username", "label": "Username", "field": "username", "align": "center"}
        ] + [
            {"name": f"platz_{p}", "label": f"Platz {p}", "field": f"platz_{p}", "align": "center"} for p in alle_plaetze
        ]
        rows = []
        for user_id, username in user_id_to_name.items():
            row = {"username": username}
            for platz in alle_plaetze:
                team_name = next((team_id_to_name[t["team_id"]] for t in platzierungstipps if t["user_id"] == user_id and t["platz"] == platz), "-")
                row[f"platz_{platz}"] = team_name
            rows.append(row)
        ui.label("🏆 Sondertipps – Saisonprognose").classes("text-xl mt-6")
        with ui.table(columns=columns, rows=rows).classes("w-full mb-8").props('dense bordered separator="cell"'):
            pass

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
