import os

from app.backend.services.external_game_data.openligadb_gamedata_service import OpenLigaGameDataService


DATA_PROVIDER = os.getenv("GAME_DATA_PROVIDER", "openligadb").lower()

if DATA_PROVIDER == "dummy":
    print("➡️ Verwende DummyGameDataService")
    spiel_service = None
elif DATA_PROVIDER == "openligadb":
    print("➡️ Verwende OpenLigaDbGameDataService")
    spiel_service = OpenLigaGameDataService()
else:
    raise ValueError(f"Unbekannter GAME_DATA_PROVIDER: {DATA_PROVIDER}")