from abc import ABC, abstractmethod
from app.models.types import StarkBankEvent


class EventFetcher(ABC):
    @abstractmethod
    def fetch_undelivered_events(self) -> list[StarkBankEvent]:
        pass

