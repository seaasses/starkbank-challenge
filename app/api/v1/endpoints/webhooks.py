from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from functools import lru_cache
from datetime import datetime, timezone
import redis

from app.models.types import Transfer, StarkBankEvent
from app.core.config import settings
from app.services.starkbank_signature_verifier.implementation import (
    StarkBankSignatureVerifier,
)
from app.services.transfer_service.implementation import StarkBankTransferSender

router = APIRouter()


@lru_cache(maxsize=1)
def get_signature_verifier():
    # use the same instance for all requests
    return StarkBankSignatureVerifier(settings.starkbank_project)


@lru_cache(maxsize=1)
def get_redis_client():
    return redis.from_url(settings.REDIS_URL)


class WebhookRequest(BaseModel):
    event: StarkBankEvent


async def validate_event_age(schema: WebhookRequest):
    now = datetime.now(timezone.utc)
    event_age = now - schema.event.created

    if event_age > settings.max_event_age:
        raise HTTPException(
            status_code=410,
            detail=f"Event is too old. Maximum age is {settings.max_event_age.total_seconds()/60} minutes",
        )


async def validate_not_already_processed(
    schema: WebhookRequest,
    redis_client=Depends(get_redis_client),
):
    key = f"webhook:event:{schema.event.id}"
    if redis_client.exists(key):
        raise HTTPException(
            status_code=409,
            detail="Event already processed",
        )


async def validate_signature(
    request: Request,
    schema: WebhookRequest,
    signature_verifier=Depends(get_signature_verifier),
):
    signature = request.headers.get("Digital-Signature")
    if not signature:
        raise HTTPException(
            status_code=401, detail="Unauthorized: Missing Digital-Signature header"
        )

    request_body = await request.body()

    if not signature_verifier.check_signature(
        request_body, signature, schema.event.created
    ):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid signature")


def valid_workspace(schema: WebhookRequest):
    return schema.event.workspaceId == settings.STARK_PROJECT_ID


@router.post(
    "/starkbank",
    dependencies=[
        Depends(validate_signature),
        Depends(validate_event_age),
        Depends(validate_not_already_processed),
        Depends(valid_workspace),
    ],
)
async def starkbank_webhook(
    schema: WebhookRequest,
    redis_client=Depends(get_redis_client),
):
    if schema.event.subscription != "invoice" or schema.event.log["type"] != "credited":
        return

    transfer_sender = StarkBankTransferSender(settings.starkbank_project)
    transfer_amount = (
        schema.event.log["invoice"]["amount"] - schema.event.log["invoice"]["fee"]
    )

    transfer = Transfer(
        account=settings.default_account,
        amount=transfer_amount,
    )

    transfer_sender.send(transfer)

    key = f"webhook:event:{schema.event.id}"
    redis_client.set(key, "1", ex=int(settings.max_event_age.total_seconds()))
