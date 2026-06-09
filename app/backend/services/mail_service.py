import os
import smtplib
import logging
logging.basicConfig(level=logging.INFO)
from email.message import EmailMessage

from app.backend.models.user import get_all_users

footer = """
----
🏠 Zum Tippspiel: https://it-ketterl.de/tippspiel/
🔢 Tippen: https://it-ketterl.de/tippspiel/game/tippen
📊 Wall of Shame ansehen: https://it-ketterl.de/tippspiel/stats/wall_of_shame
📊 Deine Tippübersicht: https://it-ketterl.de/tippspiel/uebersicht
"""

html_footer = """
<hr>
<p>
🏠 <a href='https://it-ketterl.de/tippspiel/'>Zum Tippspiel</a><br>
🔢 <a href='https://it-ketterl.de/tippspiel/game/tippen'>Tippen</a><br>
📊 <a href='https://it-ketterl.de/tippspiel/stats/wall_of_shame'>Wall of Shame ansehen</a><br>
📊 <a href='https://it-ketterl.de/tippspiel/uebersicht'>Deine Tippübersicht</a>
</p>
"""

def send_email(to_address, subject, body, html_body=None):
    logging.info(f"[MAIL] Sende Mail an {to_address} mit Betreff '{subject}'...")
    if os.environ.get("MAIL_PASSWORD", None) is None:
        raise ValueError("MAIL_PASSWORD environment variable is not set.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "tippmaster@it-ketterl.de"
    msg["To"] = to_address
    message = f"{body.strip()}\n{footer}"
    msg.set_content(message)
    if html_body:
        msg.add_alternative(f"{html_body}{html_footer}", subtype="html")
    with smtplib.SMTP_SSL("smtp.strato.de", 465) as smtp:
        mail_password = os.environ.get("MAIL_PASSWORD")
        if not mail_password:
            raise ValueError("MAIL_PASSWORD environment variable is not set.")
        smtp.login("tippmaster@it-ketterl.de", mail_password)
        smtp.send_message(msg)
    logging.info(f"[MAIL] Mail an {to_address} erfolgreich versendet.")


def send_email_to_all_users(text: str):
    users = get_all_users()
    sent = 0
    failed = 0
    message = f"{text.strip()}"
    for user in users:
        email = user.get("email")
        if not email:
            continue
        try:
            send_email(email, "📢 Neue Nachricht vom Tippspiel Kommentator", message)
            sent += 1
        except Exception as e:
            failed += 1
            logging.error(f"Fehler bei {email}: {e}")
    return sent, failed

def send_email_to_all_users_html(html: str, subject: str = "📢 Neue Nachricht vom Tippspiel Kommentator"):
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        email = user.get("email")
        if not email:
            continue
        try:
            send_email(email, subject, "", html_body=html)
            sent += 1
        except Exception as e:
            failed += 1
            logging.error(f"Fehler bei {email}: {e}")
    return sent, failed

def send_email_to_selected_users(text: str, user_ids: list):
    from app.backend.models.user import get_user_by_id
    sent = 0
    failed = 0
    message = f"{text.strip()}"
    for user_id in user_ids:
        user = get_user_by_id(user_id)
        email = user.get("email") if user else None
        if not email:
            continue
        try:
            send_email(email, "📢 Neue Nachricht vom Tippspiel Kommentator", message)
            sent += 1
        except Exception as e:
            failed += 1
            logging.error(f"Fehler bei {email}: {e}")
    return sent, failed

def send_email_to_selected_users_html(html: str, user_ids: list, subject: str = "📢 Neue Nachricht vom Tippspiel Kommentator"):
    from app.backend.models.user import get_user_by_id
    sent = 0
    failed = 0
    for user_id in user_ids:
        user = get_user_by_id(user_id)
        email = user.get("email") if user else None
        if not email:
            continue
        try:
            send_email(email, subject, "", html_body=html)
            sent += 1
        except Exception as e:
            failed += 1
            logging.error(f"Fehler bei {email}: {e}")
    return sent, failed
