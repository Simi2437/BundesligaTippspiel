from datetime import datetime
from zoneinfo import ZoneInfo

from nicegui import ui

from app.backend.models.settings import get_setting, is_tipp_ende_passed
from app.backend.services.auth_service import current_user
from app.backend.models.tipps import get_tipp, save_tipp
from app.backend.services.external_game_data.game_data_provider import spiel_service

async def get_user_timezone() -> str:
    tz = await ui.run_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    return tz or 'UTC'

@ui.page("/game/tippen")
async def tippen():
    user = current_user()
    if not user:
        ui.notify("Nicht eingeloggt")
        ui.navigate.to("/")
        return
    await ui.context.client.connected()  # sicherstellen, dass wir mit dem Client reden können

    timezone_str = await ui.run_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    browser_tz = ZoneInfo(timezone_str or "UTC")

    tipp_abgabe_erlaubt = not is_tipp_ende_passed()

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("📋 Deine Tipps").classes("text-xl")

        tipp_ende_str = get_setting("tipp_ende")
        if tipp_ende_str:
            try:
                tipp_ende = datetime.fromisoformat(tipp_ende_str)
                tipp_ende_local = tipp_ende.astimezone(browser_tz)
                ui.label(f'Tippende: {tipp_ende_local.strftime("%d.%m.%Y %H:%M")} ({timezone_str})').classes("text-sm text-gray-600")
            except Exception:
                ui.label("⚠️ Tippende-Format ungültig").classes("text-sm text-red-500")
        else:
            ui.label("⚠️ Admin muss Tippende konfigurieren").classes("text-sm text-orange-600")


    # 🔄 NEU: Spieltage und Spiele über Service laden
    for spieltag in spiel_service.get_spieltage():
        with ui.card().classes("w-full my-3"):
            ui.label(f'Spieltag {spieltag["order_number"]}: {spieltag["name"]}').classes("text-lg font-bold")
            spiele = spiel_service.get_spiele_by_spieltag(spieltag["id"])
            for spiel in spiele:
                tipp = get_tipp(user["id"], spiel["id"]) or {"tipp_heim": None, "tipp_gast": None}
                with ui.column().classes("gap-2 w-full"):
                    ui.label(f'{spiel["heim"]} vs {spiel["gast"]}').classes("w-30")
                    with ui.row().classes("items-center gap-2"):
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

                        def auto_speichern_func(s_id, th, tg):
                            def speichern():
                                save_tipp(user["id"], s_id, th.value, tg.value)
                                ui.notify("Automatischer Tipp gespeichert")
                            return speichern

                        tipp_heim.on("change", auto_speichern_func(spiel["id"], tipp_heim, tipp_gast))
                        tipp_gast.on("change", auto_speichern_func(spiel["id"], tipp_heim, tipp_gast))

                        def speichern_func(s_id, th, tg):
                            def speichern():
                                save_tipp(user["id"], s_id, th.value, tg.value)
                                ui.notify("Tipp gespeichert")
                            return speichern

                        tooltip_text = "Tipp speichern" if tipp_abgabe_erlaubt else "Tippabgabe nicht mehr möglich"

                        ui.button("💾", on_click=speichern_func(spiel["id"], tipp_heim, tipp_gast)).props(
                            "flat" + ("" if tipp_abgabe_erlaubt else " disable")
                        ).classes("text-green").tooltip(tooltip_text)
