from invoice import Invoice
from abc import ABC, abstractmethod


class InvoiceSender(ABC):

    @abstractmethod
    def send(self, invoice: Invoice):
        pass
