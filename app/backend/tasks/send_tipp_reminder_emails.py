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


def generate_punkte_table_html(spieltag_id):
    from app.backend.models.user import get_all_users
    from app.backend.db.database_backend import get_db
    from app.openligadb.db.database_openligadb import get_oldb
    from app.backend.services.external_game_data.game_data_provider import spiel_service

    db = get_db()
    users = get_all_users()
    conn_ol = get_oldb()
    spiele = conn_ol.execute("SELECT id FROM matches WHERE group_id = ?", (spieltag_id,)).fetchall()
    spiel_ids = [row[0] for row in spiele]

    # Spieltag-Nummer holen
    nummer = spieltag_id
    nummer_row = conn_ol.execute('SELECT order_number FROM groups WHERE id = ?', (spieltag_id,)).fetchone()
    if nummer_row:
        nummer = nummer_row[0]

    rows = []
    from app.backend.models.tipps import DATA_SOURCE
    for user in users:
        user_id = user["id"]
        username = user["username"]
        # Punkte für diesen Spieltag
        if spiel_ids:
            placeholders = ",".join("?" for _ in spiel_ids)
            punkte_spieltag = (
                db.execute(
                    f"SELECT SUM(punkte) FROM tipps WHERE user_id = ? AND datenquelle = ? AND spiel_id IN ({placeholders})",
                    [user_id, DATA_SOURCE] + spiel_ids,
                ).fetchone()[0]
                or 0
            )
        else:
            punkte_spieltag = 0
        # Gesamtpunkte
        gesamt_punkte = db.execute("SELECT SUM(punkte) FROM tipps WHERE user_id = ?", (user_id,)).fetchone()[0] or 0
        rows.append((username, punkte_spieltag, gesamt_punkte))

    # HTML-Tabelle bauen
    table_html = f"<table border='1' cellpadding='4' cellspacing='0'><tr><th>User</th><th>Punkte Spieltag {nummer}</th><th>Gesamtpunkte</th></tr>"
    for username, punkte_spieltag, gesamt_punkte in rows:
        table_html += f"<tr><td>{username}</td><td>{punkte_spieltag}</td><td>{gesamt_punkte}</td></tr>"
    table_html += "</table>"
    return table_html


import traceback


def versende_kommentator_punkte_email(spieltag_id: int, recipient_user_ids: list = None):
    try:
        from app.backend.services.llm_service import kommentator_admin_commando
        from app.backend.services.mail_service import send_email_to_all_users_html
        from app.backend.models.tipps import create_punkte_user_context

        print(f"[Kommentator-Mail] Starte Versand für Spieltag {spieltag_id}")

        # 1. Tabelle generieren
        table_html = generate_punkte_table_html(spieltag_id)
        print(f"[Kommentator-Mail] Generierte Punktetabelle (gekürzt): {table_html[:300]} ...")

        # 2. Kontext für AI-Kommentar
        kontext = create_punkte_user_context(spieltag_id)
        print(f"[Kommentator-Mail] Kontext für AI-Kommentar: {str(kontext)[:300]} ...")
        prompt = (
            "Kommentiere die Leistungen und Punktestände der Teilnehmer nach diesem Spieltag. "
            "Sei ironisch, sarkastisch, aber nie beleidigend. Maximal 4 Sätze. "
            "Antworte ausschließlich auf Deutsch."
        )
        ai_comment = kommentator_admin_commando(prompt, kontext)
        print(f"[Kommentator-Mail] AI-Kommentar: {ai_comment}")

        # 3. HTML zusammenbauen
        html_body = f"""
        <html>
          <body>
            <h2>Punktetabelle</h2>
            {table_html}
            <hr>
            <h3>Kommentator sagt:</h3>
            <p>{ai_comment}</p>
          </body>
        </html>
        """

        # 4. E-Mail verschicken
        if recipient_user_ids is not None:
            from app.backend.services.mail_service import send_email_to_selected_users_html
            sent, failed = send_email_to_selected_users_html(html_body, recipient_user_ids)
        else:
            sent, failed = send_email_to_all_users_html(html_body)
        print(f"[Kommentator-Mail] Versand abgeschlossen: {sent} erfolgreich, {failed} fehlgeschlagen.")
        if sent == 0:
            print("[Kommentator-Mail] Fehler: Keine E-Mails wurden versendet!")
            return False
        if failed > 0:
            print(f"[Kommentator-Mail] Warnung: {failed} E-Mails konnten nicht versendet werden.")
        return True
    except Exception as e:
        print(f"[Kommentator-Mail] Fehler beim Versand der Kommentator-Punkte-Mail: {e}")
        traceback.print_exc()
        return False


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
            print(
                f"Letzter Reminder war am {last_sent or 'Nie'}, mehr als 3 Tage her. Reminder wird trotzdem gesendet."
            )
        else:
            return

    days_left = get_days_until_tippende()

    dringlichkeit = ""
    if days_left < 0:
        return
    elif days_left == 0:
        dringlichkeit = "Heute ist die letzte Chance zu tippen! "
    elif days_left == 1:
        dringlichkeit = "Nur noch 1 Tag bis Tippende! "
    elif days_left >= 2:
        dringlichkeit = f"Nur noch {days_left} Tage bis zum Tippende! "

    kontext = create_tipp_user_context()  # enthält Statistiken, z. B. Tippquote pro User
    print("Kontext für Kommentator erstellt:")
    print(kontext)
    print("---------------------")
    prompt = (
        f"Beginne mit den schlimmsten Faulpelzen – nenne sie beim Namen und stichle mit Humor. "
        f"Sei ironisch, sarkastisch und gnadenlos ehrlich – aber niemals beleidigend. "
        f"Je weniger getippt wurde, desto härter darf der Seitenhieb sein. "
        f"Teilnehmer mit 100 % Tippquote sollst du loben oder auslassen – sie brauchen keine Erinnerung. "
        f"Erinnere am Ende daran, dass nur noch {days_left} Tage zum Tippen bleiben. "
        f"Max. 4 Sätze. Kein Gelaber – direkt, pointiert, bissig."
    )
    text = kommentator_admin_commando(prompt, kontext)
    return_info = send_email_to_all_users(text)
    set_last_reminder_timestamp()
    return return_info
