from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.queue_service.implementation import RabbitMQService
from functools import lru_cache
import redis
import os

router = APIRouter()


@lru_cache(maxsize=1)
def get_rabbitmq_service():
    return RabbitMQService(
        queue_name="",
        rabbitmq_host=os.getenv("RABBITMQ_HOST"),
        rabbitmq_port=os.getenv("RABBITMQ_PORT"),
        rabbitmq_user=os.getenv("RABBITMQ_USER"),
        rabbitmq_pass=os.getenv("RABBITMQ_PASS"),
    )


@lru_cache(maxsize=1)
def get_redis_client():
    return redis.from_url(settings.REDIS_URL)


@router.get("")
async def health_check():
    """
    Health check endpoint that verifies Redis connection
    """
    redis_ok = False
    queue_ok = get_rabbitmq_service().test_connection()

    try:
        redis_client = get_redis_client()
        redis_client.ping()
        redis_ok = True
    except:
        pass

    if redis_ok and queue_ok:
        return {
            "status": "healthy",
            "services": {
                "redis": "connected",
                "rabbitmq": "connected",
                "api": "running",
            },
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "services": {
                    "redis": "connected" if redis_ok else "disconnected",
                    "rabbitmq": "connected" if queue_ok else "disconnected",
                    "api": "running",
                },
            },
        )
