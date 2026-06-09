from datetime import datetime, timedelta, timezone
import logging
logging.basicConfig(level=logging.INFO)

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

    rows.sort(key=lambda x: x[2], reverse=True)

    # HTML-Tabelle bauen mit Platzierung
    table_html = f"<table border='1' cellpadding='4' cellspacing='0'><tr><th>Platz</th><th>User</th><th>Punkte Spieltag {nummer}</th><th>Gesamtpunkte</th></tr>"
    for idx, (username, punkte_spieltag, gesamt_punkte) in enumerate(rows, start=1):
        table_html += f"<tr><td>{idx}</td><td>{username}</td><td>{punkte_spieltag}</td><td>{gesamt_punkte}</td></tr>"
    table_html += "</table>"
    return table_html


import traceback


def auto_bereite_sonderpunkte_vor(saison: str) -> bool:
    """
    Stellt sicher, dass Sonderpunkt-Schema und Finale-Ergebnisse für die Saison vorliegen.
    Holt fehlende Daten automatisch von OpenLigaDB und berechnet anschließend die Punkte.
    Gibt True zurück wenn Punkte erfolgreich vorliegen, False bei Fehler.
    """
    try:
        import sqlite3
        from app.backend.models.finale import (
            get_sonder_punkte_schema, set_sonder_punkte_schema,
            get_alle_finale_ergebnisse, set_alle_finale_ergebnisse,
        )
        from app.backend.models.sondertipps import berechne_sondertipp_punkte
        from app.backend.services.external_game_data.game_data_provider import spiel_service
        from app.openligadb.services.importer import fetch_endtabelle
        from app.openligadb.db.database_openligadb import get_oldb

        # 1. Punkteschema – falls leer, Standard-Schema setzen
        schema = get_sonder_punkte_schema()
        if not schema:
            alle_teams = spiel_service.get_alle_teams() if spiel_service else []
            n = len(alle_teams)
            if n >= 5:
                default_schema = {}
                for k in range(1, n + 1):
                    if k == 1:
                        default_schema[k] = 10
                    elif k == 2:
                        default_schema[k] = 7
                    elif k == 3:
                        default_schema[k] = 5
                    elif k in (n - 1, n):
                        default_schema[k] = 5
                    else:
                        default_schema[k] = 0
                set_sonder_punkte_schema(default_schema)
                logging.info(f"[Sieger-Mail] Standard-Punkteschema für {n} Teams gesetzt.")
            else:
                logging.warning("[Sieger-Mail] Zu wenige Teams für Punkteschema – überspringe Schema-Setup.")

        # 2. Finale-Ergebnisse – falls leer, von OpenLigaDB laden und speichern
        ergebnisse = get_alle_finale_ergebnisse(saison)
        if not ergebnisse:
            logging.info(f"[Sieger-Mail] Keine Finale-Ergebnisse für Saison {saison} – lade von OpenLigaDB ...")
            conn = get_oldb()
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT shortcut, season FROM leagues ORDER BY season DESC LIMIT 1"
            ).fetchone()
            shortcut = row["shortcut"] if row else "bl1"

            tabelle = fetch_endtabelle(shortcut=shortcut, season=saison)
            neue_ergebnisse = {
                entry["platz"]: entry["team_id"]
                for entry in tabelle
                if entry["matched"] and entry["team_id"] is not None
            }

            if not neue_ergebnisse:
                logging.error(
                    f"[Sieger-Mail] OpenLigaDB lieferte keine gematchten Teams für Saison {saison} – Abbruch."
                )
                return False

            set_alle_finale_ergebnisse(saison, neue_ergebnisse)
            logging.info(f"[Sieger-Mail] {len(neue_ergebnisse)} Finale-Ergebnisse von OpenLigaDB gespeichert.")

        # 3. Sondertipp-Punkte berechnen (idempotent – kann mehrfach aufgerufen werden)
        treffer = berechne_sondertipp_punkte(saison)
        logging.info(f"[Sieger-Mail] Sondertipp-Punkte berechnet: {treffer} Treffer.")
        return True

    except Exception as e:
        logging.error(f"[Sieger-Mail] Fehler beim Vorbereiten der Sonderpunkte: {e}")
        traceback.print_exc()
        return False


def generate_saison_abschluss_table_html(saison: str) -> tuple:
    """
    Baut die finale Gesamtrangliste (Spieltag- + Sonderpunkte) als HTML-Tabelle.
    Gibt (table_html, user_points) zurück, wobei user_points eine absteigende Liste ist.
    """
    from app.backend.models.user import get_all_users
    from app.backend.db.database_backend import get_db

    db = get_db()
    users = get_all_users()
    user_points = []

    for user in users:
        user_id = user["id"]
        username = user["username"]
        spiel_punkte = db.execute(
            "SELECT SUM(punkte) FROM tipps WHERE user_id = ?", (user_id,)
        ).fetchone()[0] or 0
        sonder_punkte = db.execute(
            "SELECT SUM(punkte) FROM tipp_sonder WHERE user_id = ? AND punkte IS NOT NULL", (user_id,)
        ).fetchone()[0] or 0
        gesamt = spiel_punkte + sonder_punkte
        user_points.append({
            "username": username,
            "spiel_punkte": spiel_punkte,
            "sonder_punkte": sonder_punkte,
            "gesamt": gesamt,
        })

    user_points.sort(key=lambda x: x["gesamt"], reverse=True)
    total_users = len(user_points)

    table_html = (
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>"
        "<tr style='background:#f0f0f0;text-align:center'>"
        "<th>Platz</th><th>Teilnehmer</th><th>Spieltag-Punkte</th>"
        "<th>🏆 Sonder-Punkte</th><th>🎯 Gesamt</th></tr>"
    )
    for idx, user in enumerate(user_points, start=1):
        if idx == 1:
            emoji = "🥇"
        elif idx == 2:
            emoji = "🥈"
        elif idx == 3:
            emoji = "🥉"
        elif idx == total_users:
            emoji = "🫣"
        elif idx == total_users - 1 and total_users > 3:
            emoji = "🥲"
        else:
            emoji = "😎"
        table_html += (
            f"<tr style='text-align:center'>"
            f"<td>{emoji} {idx}</td>"
            f"<td><b>{user['username']}</b></td>"
            f"<td>{user['spiel_punkte']}</td>"
            f"<td>{user['sonder_punkte']}</td>"
            f"<td><b>{user['gesamt']}</b></td></tr>"
        )
    table_html += "</table>"
    return table_html, user_points


def versende_saison_sieger_email(force: bool = False, recipient_user_ids: list = None) -> bool:
    """
    Versendet die Saison-Sieger-E-Mail.
    Wird automatisch ausgelöst wenn is_season_over() True ist.
    Pro Saison nur einmal versendet (settings-Flag), außer force=True.
    Bei force=True wird das Flag ignoriert aber NICHT neu gesetzt (für Admin-Tests).
    recipient_user_ids: wenn gesetzt, nur an diese User senden (Admin-Auswahl).
    """
    try:
        from app.backend.models.sondertipps import get_aktuelle_saison
        from app.backend.models.settings import get_setting, set_setting
        from app.backend.services.llm_service import kommentator_admin_commando
        from app.backend.services.mail_service import send_email_to_all_users_html, send_email_to_selected_users_html

        saison = get_aktuelle_saison()
        saison_name = get_setting("saison_name", f"Saison {saison}")
        logging.info(f"[Sieger-Mail] Starte für {saison_name} (Saison {saison}), force={force}")

        # 1. Bereits versendet?
        if not force and get_setting(f"sieger_mail_sent_{saison}") == "true":
            logging.info(f"[Sieger-Mail] Bereits versendet für Saison {saison} – Abbruch.")
            return False

        # 2. Sonderpunkte automatisch vorbereiten (API-Pull + Berechnung falls nötig)
        if not auto_bereite_sonderpunkte_vor(saison):
            logging.error("[Sieger-Mail] Sonderpunkte konnten nicht vorbereitet werden – Mail wird nicht versendet.")
            return False

        # 3. Finale Tabelle und KI-Kontext aufbauen
        table_html, user_points = generate_saison_abschluss_table_html(saison)

        kontext_lines = [f"{saison_name} ist beendet. Endstand:"]
        for idx, u in enumerate(user_points, start=1):
            kontext_lines.append(
                f"  Platz {idx}: {u['username']} – {u['gesamt']} Punkte "
                f"({u['spiel_punkte']} Spieltag + {u['sonder_punkte']} Sonder)"
            )
        kontext = "\n".join(kontext_lines)

        # 4. KI-Kommentar mit eigenem Saison-Abschluss-Prompt
        prompt = (
            f"Die {saison_name} ist offiziell beendet! "
            f"Kündige den Sieger dramatisch und feierlich an – nenne ihn unbedingt beim Namen. "
            f"Ziehe den Letzten sanft aber unübersehbar auf. "
            f"Blicke kurz auf die gesamte Saison zurück und mache Lust auf die nächste. "
            f"Sei mitreißend, ein bisschen überdramatisch und witzig. Maximal 5 Sätze. "
            f"Antworte ausschließlich auf Deutsch."
        )
        custom_system_prompt = (
            "Du bist der legendäre Kommentator des Bundesliga-Tippspiels. "
            "Die Saison ist vorbei – das ist die große Siegerehrung. "
            "Kommentiere packend und unterhaltsam wie ein Sportmoderator beim großen Finale."
        )
        ai_comment = kommentator_admin_commando(prompt, kontext, custom_system_prompt=custom_system_prompt)
        logging.info(f"[Sieger-Mail] KI-Kommentar generiert: {ai_comment[:200]} ...")

        # 5. HTML zusammenbauen
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; padding: 20px;">
            <h1 style="text-align:center; color: #c0a000;">🏆 {saison_name} – Saisonabschluss!</h1>
            <p style="font-size:1.1em; line-height:1.6; border-left: 4px solid #c0a000; padding-left: 12px;">
              {ai_comment}
            </p>
            <hr style="margin: 24px 0;">
            <h2 style="color: #333;">🎯 Finale Gesamtrangliste</h2>
            {table_html}
          </body>
        </html>
        """

        # 6. Versenden (an alle oder an ausgewählte User)
        betreff = f"🏆 {saison_name} – Das ist euer Champion!"
        if recipient_user_ids is not None:
            sent, failed = send_email_to_selected_users_html(html_body, recipient_user_ids, subject=betreff)
        else:
            sent, failed = send_email_to_all_users_html(html_body, subject=betreff)

        logging.info(f"[Sieger-Mail] Versand abgeschlossen: {sent} erfolgreich, {failed} fehlgeschlagen.")

        if sent == 0:
            logging.error("[Sieger-Mail] Keine Mails versendet – Flag wird nicht gesetzt.")
            return False

        # 7. Flag nur bei automatischem Versand setzen (force=True ist für Admin-Tests)
        if not force:
            set_setting(f"sieger_mail_sent_{saison}", "true")
            logging.info(f"[Sieger-Mail] Flag 'sieger_mail_sent_{saison}' gesetzt – kein erneuter Versand.")

        return True

    except Exception as e:
        logging.error(f"[Sieger-Mail] Fehler beim Versand: {e}")
        traceback.print_exc()
        return False


def versende_kommentator_punkte_email(spieltag_id: int, recipient_user_ids: list = None):
    try:
        from app.backend.services.llm_service import kommentator_admin_commando
        from app.backend.services.mail_service import send_email_to_all_users_html
        from app.backend.models.tipps import create_punkte_user_context

        logging.info(f"[Kommentator-Mail] Starte Versand für Spieltag {spieltag_id}")

        # 1. Tabelle generieren
        table_html = generate_punkte_table_html(spieltag_id)
        logging.info(f"[Kommentator-Mail] Generierte Punktetabelle (gekürzt): {table_html[:300]} ...")

        # 2. Kontext für AI-Kommentar
        kontext = create_punkte_user_context(spieltag_id)
        logging.info(f"[Kommentator-Mail] Kontext für AI-Kommentar: {str(kontext)[:300]} ...")
        prompt = (
            "Kommentiere die Leistungen und Punktestände der Teilnehmer nach diesem Spieltag. "
            "Sei ironisch, sarkastisch, aber nie beleidigend. Maximal 4 Sätze. "
            "Antworte ausschließlich auf Deutsch."
        )
        ai_comment = kommentator_admin_commando(prompt, kontext)
        logging.info(f"[Kommentator-Mail] AI-Kommentar: {ai_comment}")

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
        logging.info(f"[Kommentator-Mail] Versand abgeschlossen: {sent} erfolgreich, {failed} fehlgeschlagen.")
        if sent == 0:
            logging.info("[Kommentator-Mail] Fehler: Keine E-Mails wurden versendet!")
            return False
        if failed > 0:
            logging.info(f"[Kommentator-Mail] Warnung: {failed} E-Mails konnten nicht versendet werden.")
        return True
    except Exception as e:
        logging.error(f"[Kommentator-Mail] Fehler beim Versand der Kommentator-Punkte-Mail: {e}")
        traceback.print_exc()
        return False


def versende_kommentator_tipp_reminder():

    now = datetime.now()
    last_sent = get_last_reminder_timestamp()
    if last_sent:
        adjusted_last_sent = last_sent - timedelta(hours=12)
        if (now - adjusted_last_sent).days < 3:
            logging.info(f"Letzter Reminder (adjusted) war am {adjusted_last_sent}, noch keine 3 Tage vergangen.")
            return

    if not ist_morgens():
        logging.info("Nicht im Morgen-Zeitfenster. Reminder wird nicht gesendet.")
        if not last_sent or abs(now - last_sent) > timedelta(days=4):
            logging.info(
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
    logging.info("Kontext für Kommentator erstellt:")
    logging.info(kontext)
    logging.info("---------------------")
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
