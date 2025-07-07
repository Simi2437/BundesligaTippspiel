from datetime import datetime, timedelta, timezone

from app.backend.models.settings import get_days_until_tippende
from app.backend.models.user_meta import get_last_reminder_timestamp, set_last_reminder_timestamp
from app.backend.services.llm_service import kommentator_admin_commando, create_user_context, create_tipp_user_context
from app.backend.services.mail_service import send_email_to_all_users


def ist_morgens():
    jetzt = datetime.now()
    return 6 <= jetzt.hour < 10

def was_last_sent_arround(time):
    return 6 <= time.hour < 10

def versende_kommentator_tipp_reminder():

    now = datetime.now()
    last_sent = get_last_reminder_timestamp()
    if last_sent:
        adjusted_last_sent = last_sent - timedelta(hours=12)
        if (now - adjusted_last_sent).days < 3:
            print(f"Letzter Reminder (adjusted) war am {adjusted_last_sent}, noch keine 3 Tage vergangen.")
            return

    if not ist_morgens():
        print("Nicht im Morgen-Zeitfenster. Reminder wird nicht gesendet.")
        if not last_sent or abs(now - last_sent) > timedelta(days=4):
            print(f"Letzter Reminder war am {last_sent or 'Nie'}, mehr als 3 Tage her. Reminder wird trotzdem gesendet.")
        else:
            return

    set_last_reminder_timestamp()

    days_left = get_days_until_tippende()

    dringlichkeit = ""
    if days_left == 0:
        dringlichkeit = "Heute ist die letzte Chance zu tippen! "
    elif days_left == 1:
        dringlichkeit = "Nur noch 1 Tag bis Tippende! "
    elif days_left >= 2:
        dringlichkeit = f"Nur noch {days_left} Tage bis zum Tippende! "

    kontext = create_tipp_user_context()  # enthält Statistiken, z. B. Tippquote pro User
    prompt = (
        f"{dringlichkeit}"
        "Erinnere die Teilnehmer des Bundesliga-Tippspiels ans Tippen und wielang man noch tippen kann. "
        "Werde vor allem bei denen deutlicher, die kaum getippt haben. "
        "Du darfst humorvoll, ironisch und ein bisschen frech sein – "
        "aber bleibe respektvoll und unterhaltsam. Max. 3-4 Sätze."
        "Auf deutsch."
    )
    text = kommentator_admin_commando(prompt, kontext)
    return send_email_to_all_users(text)
