from concurrent.futures import ThreadPoolExecutor

from nicegui import ui

from app.backend.services.auth_service import is_admin_user
from app.backend.services.llm_service import kommentator_admin_commando, create_user_context
from app.backend.services.mail_service import send_email_to_all_users
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
        print("Send Prompt button pressed")
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

    def send_mails():
        button_email.disable()
        text = response_output.text
        if not text.strip():
            ui.notify("❌ Kein Text vorhanden zum Versenden.")
            button_email.enable()
            return

        def run():
            try:
                sent, failed = send_email_to_all_users(text)
                ui.notify(f"✅ {sent} Mails verschickt, ❌ {failed} fehlgeschlagen.")
            except Exception as e:
                ui.notify(f"❌ Fehler: {e}")
            finally:
                button_email.enable()

        executor.submit(run)

    button = ui.button("💬 Kommentator anweisen", on_click=send_prompt).classes("mt-2")
    button_email = ui.button("📧 Mail an alle Teilnehmer", on_click=lambda: send_mails()).classes("mt-2")


