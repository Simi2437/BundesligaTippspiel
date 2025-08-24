import os
import smtplib
from email.message import EmailMessage

from app.backend.models.user import get_all_users

footer = """
    
----
🏠 Zum Tippspiel: https://it-ketterl.de/tippspiel/
🔢 Tippen: https://it-ketterl.de/tippspiel/game/tippen
📊 Wall of Shame ansehen: https://it-ketterl.de/tippspiel/stats/wall_of_shame
📊 Deine Tippübersicht: https://it-ketterl.de/tippspiel/uebersicht
    """

def send_email(to_address, subject, body, html_body=None):
    if os.environ.get("MAIL_PASSWORD", None) is None:
        raise ValueError("MAIL_PASSWORD environment variable is not set.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "tippmaster@it-ketterl.de"
    msg["To"] = to_address
    message = f"{body.strip()}\n{footer}"
    msg.set_content(message)
    if html_body:
        msg.add_alternative(f"{html_body}{footer}", subtype="html")
    with smtplib.SMTP_SSL("smtp.strato.de", 465) as smtp:
        mail_password = os.environ.get("MAIL_PASSWORD")
        if not mail_password:
            raise ValueError("MAIL_PASSWORD environment variable is not set.")
        smtp.login("tippmaster@it-ketterl.de", mail_password)
        smtp.send_message(msg)

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
            print(f"Fehler bei {email}: {e}")
    return sent, failed

def send_email_to_all_users_html(html: str):
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        email = user.get("email")
        if not email:
            continue
        try:
            send_email(email, "📢 Neue Nachricht vom Tippspiel Kommentator", "", html_body=html)
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Fehler bei {email}: {e}")
    return sent, failed
