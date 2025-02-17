from abc import ABC, abstractmethod
from app.models.types import Invoice


class InvoiceSender(ABC):
    @abstractmethod
    def send_batch(self, invoices: list[Invoice]) -> None:
        pass

    @abstractmethod
    def send(self, invoice: Invoice) -> None:
        pass
