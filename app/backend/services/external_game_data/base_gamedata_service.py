from abc import ABC, abstractmethod
from typing import List, Dict


class BaseGameDataService(ABC):

    @abstractmethod
    def get_data_source_name(self):
        raise NotImplementedError

    @abstractmethod
    def get_spieltage(self) -> List[Dict]:
        """Gibt eine Liste von Spieltagen zurück"""
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
    def get_anzahl_spiele(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_erstes_match_datum(self) -> str:
        raise NotImplementedError