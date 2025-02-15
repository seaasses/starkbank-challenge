from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from functools import lru_cache

from app.models.types import Transfer, StarkBankEvent
from app.core.config import settings
from app.services.starkbank_signature_verifier.implementation import (
    StarkBankSignatureVerifier,
)
from app.services.transfer_service.interface import TransferSender
from app.services.transfer_service.implementation import StarkBankTransferSender

router = APIRouter()


@lru_cache(maxsize=1)
def get_signature_verifier():
    # use the same instance for all requests
    return StarkBankSignatureVerifier(settings.starkbank_project)


def get_transfer_sender() -> TransferSender:
    default_account = settings.default_account
    if default_account.bank_code == "20018183":
        return StarkBankTransferSender(settings.starkbank_project)
    else:
        raise HTTPException(status_code=400, detail="Bank not supported")


class WebhookRequest(BaseModel):
    event: StarkBankEvent


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


@router.post(
    "/starkbank",
    dependencies=[Depends(validate_signature)],
)
async def starkbank_webhook(
    schema: WebhookRequest,
    transfer_sender: TransferSender = Depends(get_transfer_sender),
) -> None:
    if schema.event.subscription != "invoice":
        return

    transfer_amount = (
        schema.event.log["invoice"]["amount"] - schema.event.log["invoice"]["fee"]
    )

    transfer = Transfer(
        account=settings.default_account,
        amount=transfer_amount,
    )

    transfer_sender.send(transfer)
