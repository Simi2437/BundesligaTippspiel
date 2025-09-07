import os

from app.backend.services.external_game_data.openligadb_gamedata_service import OpenLigaGameDataService


DATA_PROVIDER = os.getenv("GAME_DATA_PROVIDER", "openligadb").lower()

import logging
logging.basicConfig(level=logging.INFO)

if DATA_PROVIDER == "dummy":
    logging.info("➡️ Verwende DummyGameDataService")
    spiel_service = None
elif DATA_PROVIDER == "openligadb":
    logging.info("➡️ Verwende OpenLigaDbGameDataService")
    spiel_service = OpenLigaGameDataService()
else:
    raise ValueError(f"Unbekannter GAME_DATA_PROVIDER: {DATA_PROVIDER}")