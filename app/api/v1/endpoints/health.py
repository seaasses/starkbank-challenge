from fastapi import APIRouter, HTTPException
import redis
from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    """
    Health check endpoint that verifies Redis connection
    """
    try:
        # Test Redis connection
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()

        return {
            "status": "healthy",
            "services": {"redis": "connected", "api": "running"},
        }
    except redis.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "services": {"redis": "disconnected", "api": "running"},
            },
        )
