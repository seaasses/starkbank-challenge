from abc import ABC, abstractmethod


class ThreadLock(ABC):
    @abstractmethod
    def lock(self, key: str, max_lock_time: int) -> bool:
        pass

    @abstractmethod
    def unlock(self, key: str) -> None:
        pass
