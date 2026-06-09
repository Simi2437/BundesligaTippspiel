from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseGameDataService(ABC):

    @abstractmethod
    def get_data_source_name(self):
        raise NotImplementedError

    @abstractmethod
    def get_available_saisons(self) -> List[str]:
        """Gibt alle verfügbaren Saisons zurück (neueste zuerst), z. B. ['2025', '2024']"""
        raise NotImplementedError

    @abstractmethod
    def get_spieltage(self, saison: Optional[str] = None) -> List[Dict]:
        """Gibt eine Liste von Spieltagen zurück. Optional gefiltert nach Saison."""
        raise NotImplementedError

    @abstractmethod
    def get_spiele_by_spieltag(self, spieltag_id: int) -> List[Dict]:
        """Gibt alle Spiele für einen Spieltag zurück"""
        raise NotImplementedError

    @abstractmethod
    def get_match_by_id(self, match_id: int) -> Dict:
        """Optional: Einzelnes Spiel abrufen"""
        raise NotImplementedError

    @abstractmethod
    def get_anzahl_spiele(self, saison: Optional[str] = None) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_erstes_match_datum(self, saison: Optional[str] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_alle_teams(self) -> list[dict]:
        raise NotImplementedError

