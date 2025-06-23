import os
import smtplib
from email.message import EmailMessage

from app.models.user import get_all_users


def send_email(to_address, subject, body):
    if os.environ.get("MAIL_PASSWORD", None) is None:
        raise ValueError("MAIL_PASSWORD environment variable is not set.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "tippmaster@it-ketterl.de"
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.strato.de", 465) as smtp:
        smtp.login("tippmaster@it-ketterl.de", os.environ.get("MAIL_PASSWORD"))
        smtp.send_message(msg)

def send_email_to_all_users(text: str):
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        email = user.get("email")
        if not email:
            continue
        try:
            send_email(email, "📢 Neue Nachricht vom Tippspiel Kommentator", text)
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Fehler bei {email}: {e}")
    return sent, failed