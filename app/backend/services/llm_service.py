import os

import requests

from app.backend.models.tipps import get_tipp_statistik
from app.backend.models.user import get_all_users

# OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
# MODEL_NAME = "llama3:8b"
groq_api_key = os.environ.get("GROQ_API_KEY", None)


def kommentator_admin_commando(admin_input: str, teilnehmer_kontext: str, custom_system_prompt: str | None = None):
    if not groq_api_key:
        return "KEIN APIKEY"
    print("Trying to reach the api.")
    full_prompt = custom_system_prompt or f"""
    Du bist 'Der Kommentator' für ein Bundesliga-Tippspiel. 
    Dein Stil: frech, ironisch, manchmal sarkastisch – aber immer charmant. 
    Du darfst sticheln, Seitenhiebe verteilen, überfällige Tipps anprangern und mit Augenzwinkern motivieren. 
    Keine Kuschelpädagogik. Du bist die Stimme der Wahrheit – aber mit Humor. 
    Wichtig: Du darfst provozieren, aber nicht beleidigen oder verletzen.

    Admin-Anweisung:
    \"\"\"{admin_input}\"\"\"

    Teilnehmer-Kontext:
    \"\"\"{teilnehmer_kontext}\"\"\"

    Gib einen knackigen Kommentar zurück, 2–6 Sätze lang. Der Text darf ruhig überspitzt, bissig oder spöttisch sein – aber nie ohne Stil.
    """
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_api_key}"},
        json={
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.9,
        },
        timeout=60
    )
    if response.ok:
        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print("⚠️ JSON-Parsing fehlgeschlagen trotz erfolgreichem Statuscode.")
            print(f"Status Code: {response.status_code}")
            print("Raw Response:")
            print(response.text)
            raise e
    else:
        print("❌ Fehlerhafte Antwort vom LLM:")
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)
        raise Exception(f"Groq API-Fehler: Status {response.status_code}")

def create_user_context():
    users = get_all_users()
    if not users:
        return "Es sind keine Teilnehmer im Tippspiel registriert"

    beschreibungen = []

    for user in users:
        if user.get('is_approved', False) == 0:
            continue
        name = user.get("username", "Unbekannt")
        beschreibungen.append(f"- {name}")

    return "Diese Teilnehmer sind aktuell im Tippspiel:\n" + "\n".join(beschreibungen)


def create_tipp_user_context():
    users = get_all_users()
    if not users:
        return "Es sind keine Teilnehmer im Tippspiel registriert."

    beschreibungen = []

    for user in users:
        getippt, offen = get_tipp_statistik(user["id"])
        gesamt = getippt + offen
        quote = (getippt / gesamt * 100) if gesamt else 0
        beschreibungen.append(f'{user["username"]} hat {getippt} von {gesamt} Spielen getippt ({quote:.1f}%){" -> fertig getippt" if offen == 0 else ""}')

    beschreibungen.sort(key=lambda s: float(s.split("(")[-1].replace("%)", "")))

    return "\n".join(beschreibungen)

    # r = requests.post(
    #     f"{OLLAMA_BASE_URL}/api/generate",
    #     json={"model": MODEL_NAME, "prompt": full_prompt, "stream": False},
    #     timeout=3600,
    # )
    # return r.json()["response"].strip()


# def ensure_model_available():
#     try:
#         print(f"⚙️ Lade Modell {MODEL_NAME} von Ollama …")
#         response = requests.post(f"{OLLAMA_BASE_URL}/api/pull", json={"name": MODEL_NAME}, timeout=120)
#         response.raise_for_status()
#         print("✅ Modell geladen oder bereits verfügbar.")
#     except Exception as e:
#         print(f"❌ Fehler beim Laden des Modells: {e}")
