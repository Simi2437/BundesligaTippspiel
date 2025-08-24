from fastapi import APIRouter, Response
from openpyxl import Workbook
from tempfile import NamedTemporaryFile
from app.backend.models.tipps import get_tipps_for_spieltag
from app.backend.services.external_game_data.game_data_provider import spiel_service
import os

router = APIRouter()

@router.get("/api/export_tipps_excel")
def export_tipps_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "Tipps"
    ws.append(["Spieltag", "Spiel", "Ergebnis", "Benutzer", "Tipp", "Punkte"])
    for spieltag in spiel_service.get_spieltage():
        spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
        tipps = get_tipps_for_spieltag(spieltag["id"], spiel_service.get_data_source_name())
        for spiel in spiele:
            result = spiel_service.get_final_result_for_match(spiel["id"])
            for tipp in tipps:
                if tipp["spiel_id"] != spiel["id"]:
                    continue
                tipp_str = f'{tipp["tipp_heim"]}:{tipp["tipp_gast"]}' if tipp["tipp_heim"] is not None and tipp["tipp_gast"] is not None else "-"
                punkte = tipp.get("punkte")
                ws.append([
                    spieltag["order_number"],
                    f'{spiel["heim"]} vs {spiel["gast"]}',
                    result if result else "-",
                    tipp["username"],
                    tipp_str,
                    punkte if punkte is not None else "-"
                ])
    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        wb.save(tmp.name)
        tmp.seek(0)
        data = tmp.read()
    os.unlink(tmp.name)
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=BundesligaTippspiel_Tipps.xlsx"})
