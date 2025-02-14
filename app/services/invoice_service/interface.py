from abc import ABC, abstractmethod
from app.models.types import Invoice


class InvoiceSender(ABC):
    @abstractmethod
    def send(self, invoice: Invoice) -> None:
        pass 