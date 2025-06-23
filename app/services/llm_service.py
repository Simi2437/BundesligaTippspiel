import os

import requests

from app.models.user import get_all_users

# OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
# MODEL_NAME = "llama3:8b"
groq_api_key = os.environ.get("GROQ_API_KEY", None)


def kommentator_admin_commando(admin_input: str, teilnehmer_kontext: str):
    if not groq_api_key:
        return "KEIN APIKEY"

    full_prompt = f"""
    Du bist 'Der Kommentator' für ein Bundesliga-Tippspiel. 
    Dein Stil: ironisch, witzig, gerne etwas frech – aber nicht beleidigend oder komplett ausfallend. 
    Dein Ziel: Teilnehmer charmant und mit Humor an etwas erinnern oder auf etwas hinweisen, dass dir der Admin vorgibt.

    Admin-Anweisung:
    \"\"\"{admin_input}\"\"\"

    Teilnehmer-Kontext:
    \"\"\"{teilnehmer_kontext}\"\"\"

    Gib eine unterhaltsame, maximal 3-4 Sätze lange Nachricht zurück:
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
    return response.json()["choices"][0]["message"]["content"].strip()

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
