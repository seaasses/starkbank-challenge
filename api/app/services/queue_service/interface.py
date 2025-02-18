from abc import ABC, abstractmethod


class QueueService(ABC):
    @abstractmethod
    def publish_message(self, message: dict[str, str]) -> bool:
        pass

    @abstractmethod
    def publish_messages(self, messages: list[dict[str, str]]) -> list[bool]:
        pass