from datetime import datetime

from nicegui import ui

from app.models.settings import get_setting, is_tipp_ende_passed
from app.services.auth_service import current_user
from app.models.spieltage import get_all_spieltage, get_spiele_by_spieltag
from app.models.tipps import get_tipp, save_tipp


@ui.page("/game/tippen")
def tippen():
    user = current_user()
    if not user:
        ui.notify("Nicht eingeloggt")
        ui.navigate.to("/")
        return

    tipp_abgabe_erlaubt = not is_tipp_ende_passed()

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("📋 Deine Tipps").classes("text-xl")

        tipp_ende_str = get_setting("tipp_ende")
        if tipp_ende_str:
            try:
                tipp_ende = datetime.fromisoformat(tipp_ende_str)
                ui.label(f'Tippende: {tipp_ende.strftime("%d.%m.%Y %H:%M")}').classes("text-sm text-gray-600")
            except Exception:
                ui.label("⚠️ Tippende-Format ungültig").classes("text-sm text-red-500")
        else:
            ui.label("⚠️ Admin muss Tippende konfigurieren").classes("text-sm text-orange-600")

    for spieltag in get_all_spieltage():
        with ui.card().classes("w-full my-3"):
            ui.label(f'Spieltag {spieltag["nummer"]}').classes("text-lg font-bold")
            spiele = get_spiele_by_spieltag(spieltag["id"])
            for spiel in spiele:
                tipp = get_tipp(user["id"], spiel["id"]) or {"tipp_heim": None, "tipp_gast": None}
                with ui.row().classes("items-center gap-4"):
                    ui.label(f'{spiel["heim"]} vs {spiel["gast"]}').classes("w-30")
                    tipp_heim = (
                        ui.number(value=tipp["tipp_heim"], min=0)
                        .classes("w-20 text-center")
                        .props("outlined dense")
                    )
                    if not tipp_abgabe_erlaubt:
                        tipp_heim.props("readonly")
                        tipp_heim.tooltip("Tippen ist nicht mehr möglich, da das Tippende erreicht ist.")
                    ui.label(f":")
                    tipp_gast = (
                        ui.number(value=tipp["tipp_gast"], min=0)
                        .classes("w-20 text-center")
                        .props("outlined dense")
                    )
                    if not tipp_abgabe_erlaubt:
                        tipp_gast.props("readonly")
                        tipp_gast.tooltip("Tippen ist nicht mehr möglich, da das Tippende erreicht ist.")

                    def auto_speichern():
                        save_tipp(user["id"], spiel["id"], tipp_heim.value, tipp_gast.value)
                        ui.notify("Automatischer Tipp gespeichert")

                    tipp_heim.on("change", auto_speichern)
                    tipp_gast.on("change", auto_speichern)

                    def speichern(s_id=spiel["id"], th=tipp_heim, tg=tipp_gast):
                        save_tipp(user["id"], s_id, th.value, tg.value)
                        ui.notify("Tipp gespeichert")

                    tooltip_text = "Tipp speichern" if tipp_abgabe_erlaubt else "Tippabgabe nicht mehr möglich"

                    ui.button("💾", on_click=speichern).props(
                        "flat" + ("" if tipp_abgabe_erlaubt else " disable")
                    ).classes("text-green").tooltip(tooltip_text)
