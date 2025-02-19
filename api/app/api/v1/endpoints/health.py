from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.queue_service.implementation import RabbitMQService
from app.services.transfer_service.implementation import QueueTransferSender
from functools import lru_cache
from app.services.queue_service.implementation import QueueService
from app.models.types import Transfer, Account

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
    print("TO AQUIIIIIIIIIIIIIIIIII", flush=True)
    queue_service = RabbitMQService(
        queue_name="task_queue",
        rabbitmq_host=os.getenv("RABBITMQ_HOST"),
        rabbitmq_port=os.getenv("RABBITMQ_PORT"),
        rabbitmq_user=os.getenv("RABBITMQ_USER"),
        rabbitmq_pass=os.getenv("RABBITMQ_PASS"),
    )

    transfer_service = QueueTransferSender(queue_service)
    account = settings.default_account

    transfer = Transfer(
        account=account,
        amount=1000,
    )

    transfer_service.send(transfer)
