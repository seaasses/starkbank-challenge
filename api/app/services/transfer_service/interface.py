from abc import ABC, abstractmethod
from app.models.types import Transfer


class TransferSender(ABC):
    @abstractmethod
    def send(self, transfer: Transfer) -> None:
        pass 