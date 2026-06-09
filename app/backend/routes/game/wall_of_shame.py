from nicegui import ui

from app.backend.models.tipps import get_tipp_statistik, get_enhanced_tipp_statistik
from app.backend.models.user import get_user_by_id, get_all_users
from app.backend.models.sondertipps import get_aktuelle_saison, get_available_saisons
from app.backend.uielements.pagestructure import inner_page

def get_wall_of_shame_title(quote: float) -> str:
    if quote >= 98:
        return "👑 Maschine"
    elif quote >= 90:
        return "🔥 Hardcore"
    elif quote >= 80:
        return "💪 Aktivist"
    elif quote >= 70:
        return "📊 Solide"
    elif quote >= 60:
        return "😐 Durchschnitt"
    elif quote >= 50:
        return "🤏 Lückenfüller"
    elif quote >= 40:
        return "🦥 Gelegenheitsgast"
    elif quote >= 30:
        return "🫥 Halbwacher"
    elif quote >= 20:
        return "🤡 Trittbrettfahrer"
    elif quote >= 10:
        return "💤 Tiefschläfer"
    elif quote > 0:
        return "🪦 Totalausfall"
    else:
        return "👻 Phantom"


@inner_page("/stats/wall_of_shame")
def wall_of_shame():

    ui.label("🧱 Wall of Shame – Wer ist der faulste Tipper?").classes("text-2xl font-bold mb-4")

    alle_saisons = get_available_saisons()
    aktuelle = get_aktuelle_saison()
    selected_saison = {'value': aktuelle if aktuelle in alle_saisons else (alle_saisons[0] if alle_saisons else None)}

    @ui.refreshable
    def build_wall(saison: str):
        stats = []
        all_users = get_all_users()

        for user in all_users:
            getippt, offen = get_tipp_statistik(user['id'], saison=saison)
            enhanced_stats = get_enhanced_tipp_statistik(user['id'], saison=saison)
            stats.append(
                {"user_id": user["id"],
                 "getippt": getippt,
                 "offen": offen,
                 'unentschieden': enhanced_stats['unentschieden'],
                 'diff1': enhanced_stats['tor_diff_1'],
                 'diffX': enhanced_stats['tor_diff_gt_1'],
                 }
            )

        rows = []
        for stat in sorted(stats, key=lambda x: x['getippt']):
            user = get_user_by_id(stat['user_id'])
            total = stat['getippt'] + stat['offen']
            quote = round((stat['getippt'] / total * 100), 1) if total > 0 else 0
            spruch = get_wall_of_shame_title(quote)
            rows.append({
                'user': user['username'],
                'getippt': stat['getippt'],
                'offen': stat['offen'],
                'quote': f"{quote}%",
                'spruch': spruch,
                'unentschieden': stat['unentschieden'],
                'diff1': stat['diff1'],
                'diffX': stat['diffX'],
            })

        ui.table(columns=[
            {'name': 'titel', 'label': 'Titel', 'field': 'spruch'},
            {'name': 'user', 'label': 'Benutzer', 'field': 'user'},
            {'name': 'getippt', 'label': 'Getippt', 'field': 'getippt'},
            {'name': 'offen', 'label': 'Offen', 'field': 'offen'},
            {'name': 'quote', 'label': 'Tippquote', 'field': 'quote'},
            {'name': 'unentschieden', 'label': 'Unentschieden', 'field': 'unentschieden'},
            {'name': 'diff1', 'label': 'Tor diff 1', 'field': 'diff1'},
            {'name': 'diffX', 'label': 'Tor diff größer 1', 'field': 'diffX'},
        ], rows=rows).classes("w-full")

    if len(alle_saisons) > 1:
        def on_saison_change(e):
            selected_saison['value'] = e.value
            build_wall.refresh(e.value)

        ui.select(
            options=alle_saisons,
            value=selected_saison['value'],
            label="Saison",
            on_change=on_saison_change,
        ).classes("mb-4").props("outlined dense")

    if selected_saison['value']:
        build_wall(selected_saison['value'])
    else:
        ui.label("Keine Saison-Daten verfügbar.").classes("text-gray-500")

