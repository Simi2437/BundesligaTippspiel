from nicegui import ui

from app.backend.models.tipps import get_all_tipp_statistiken, get_tipp_statistik, get_enhanced_tipp_statistik
from app.backend.models.user import get_user_by_id, get_all_users
from app.backend.services.auth_service import is_admin_user
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

    stats = []
    all_users = get_all_users()

    for user in all_users:
        getippt, offen = get_tipp_statistik(user['id'])
        enhanced_stats = get_enhanced_tipp_statistik(user['id'])
        stats.append(
            {"user_id":user["id"],
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
