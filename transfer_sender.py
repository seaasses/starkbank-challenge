from transfer import Transfer
from abc import ABC, abstractmethod


class TransferSender(ABC):
    @abstractmethod
    def send(self, transfer: Transfer):
        pass
