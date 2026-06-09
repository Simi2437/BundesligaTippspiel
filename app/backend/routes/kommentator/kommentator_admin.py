from concurrent.futures import ThreadPoolExecutor
import logging
logging.basicConfig(level=logging.INFO)

from nicegui import ui

from app.backend.services.auth_service import is_admin_user
from app.backend.services.llm_service import kommentator_admin_commando, create_user_context
from app.backend.services.mail_service import send_email_to_all_users, send_email_to_selected_users, send_email_to_selected_users_html
from app.backend.models.user import get_all_users
from app.backend.uielements.pagestructure import inner_page

executor = ThreadPoolExecutor(max_workers=2)

@inner_page("/admin/kommentator")
def kommentator_admin():
    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return
    ui.label("🎙️ Kommentator anweisen").classes("text-2xl mb-4")

    input_field = ui.textarea(label="Anweisung an den Kommentator").classes("w-full")
    kontext_input = ui.textarea(label="Teilnehmer-Kontext").classes('w-full')
    kontext_input.set_value(create_user_context())
    response_output = ui.label("").classes("text-lg mt-4")

    def send_prompt():
        logging.info("Send Prompt button pressed")
        button.disable()
        prompt = input_field.value.strip()
        if not prompt:
            ui.notify("Bitte eine Anweisung eingeben")
            button.enable()
            return
        response_output.set_text("⏳ Kommentator denkt nach...")
        def run():
            try:
                response_output.set_text(kommentator_admin_commando(prompt, kontext_input.value))
                #response_output.set_text("Test message")
            except:
                pass
            finally:
                button.enable()
        executor.submit(run)

    # Checkbox-Liste für User-Auswahl
    users = get_all_users()
    selected_user_ids = []
    user_checkboxes = {}
    ui.label("Empfänger auswählen:").classes("mt-4 mb-2")
    for user in users:
        user_checkboxes[user["id"]] = ui.checkbox(f'{user["username"]}', value=True)

    def update_selected_user_ids():
        selected_user_ids.clear()
        for user in users:
            if user_checkboxes[user["id"]].value:
                selected_user_ids.append(user["id"])

    def send_mails():
        button_email.disable()
        update_selected_user_ids()
        text = response_output.text
        if not text.strip():
            ui.notify("❌ Kein Text vorhanden zum Versenden.")
            button_email.enable()
            return

        def run():
            try:
                sent, failed = send_email_to_selected_users(text, selected_user_ids)
                ui.notify(f"✅ {sent} Mails verschickt, ❌ {failed} fehlgeschlagen.")
            except Exception as e:
                ui.notify(f"❌ Fehler: {e}")
            finally:
                button_email.enable()

        executor.submit(run)

    button = ui.button("💬 Kommentator anweisen", on_click=send_prompt).classes("mt-2")
    button_email = ui.button("📧 Mail an alle Teilnehmer", on_click=lambda: send_mails()).classes("mt-2")

    # Manueller Trigger für die Punkte-Mail zum letzten fertigen Spieltag
    from app.backend.tasks.send_tipp_reminder_emails import versende_kommentator_punkte_email
    from app.backend.models.spieltage import get_highest_finished_spieltag
    def send_punkte_mail():
        button_punkte_mail.disable()
        update_selected_user_ids()
        def run():
            try:
                highest = get_highest_finished_spieltag()
                if not highest:
                    ui.notify("❌ Kein fertiger Spieltag gefunden!")
                    return
                spieltag_id = highest['id']
                nummer = highest['nummer']
                from app.backend.tasks.send_tipp_reminder_emails import versende_kommentator_punkte_email
                success = versende_kommentator_punkte_email(spieltag_id, selected_user_ids)
                if success:
                    ui.notify(f"✅ Kommentator-Punkte-Mail für Spieltag {nummer} (ID {spieltag_id}) verschickt!")
                else:
                    ui.notify(f"❌ Fehler beim Versand der Kommentator-Punkte-Mail für Spieltag {nummer} (ID {spieltag_id}).")
            except Exception as e:
                ui.notify(f"❌ Fehler: {e}")
                logging.info(f"❌ Fehler: {e}")
            finally:
                button_punkte_mail.enable()
        executor.submit(run)
    button_punkte_mail = ui.button("📊 Kommentator-Punkte-Mail für letzten fertigen Spieltag senden", on_click=send_punkte_mail).classes("mt-2")

    # Manueller Trigger für die Saison-Sieger-Mail
    def send_sieger_mail():
        button_sieger_mail.disable()
        update_selected_user_ids()

        def run():
            try:
                from app.backend.tasks.send_tipp_reminder_emails import versende_saison_sieger_email
                success = versende_saison_sieger_email(force=True, recipient_user_ids=selected_user_ids if selected_user_ids else None)
                if success:
                    ui.notify("✅ Saison-Sieger-Mail erfolgreich verschickt!")
                else:
                    ui.notify("❌ Fehler beim Versand der Saison-Sieger-Mail. Logs prüfen.")
            except Exception as e:
                ui.notify(f"❌ Fehler: {e}")
                logging.error(f"[Sieger-Mail] Fehler im Admin-Button: {e}")
            finally:
                button_sieger_mail.enable()

        executor.submit(run)

    button_sieger_mail = ui.button("🏆 Saison-Sieger-Mail versenden (force)", on_click=send_sieger_mail).classes("mt-2")


