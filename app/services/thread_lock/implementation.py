from app.services.thread_lock.interface import ThreadLock
import redis


class RedisThreadLock(ThreadLock):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def lock(self, key: str, max_lock_time: int = 9999999999999) -> bool:
        return self.redis_client.set(key, "1", ex=max_lock_time, nx=True)

    def unlock(self, key: str) -> None:
        self.redis_client.delete(key)
    