from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from functools import lru_cache

from app.models.types import Transfer, StarkBankInvoiceEvent, Transfer, Account
from app.core.config import settings
from app.services.starkbank_signature_verifier.implementation import (
    StarkBankSignatureVerifier,
)
from app.services.transfer_service.interface import TransferSender
from app.services.transfer_service.implementation import StarkBankTransferSender

router = APIRouter()


class TransferRequest(BaseModel):
    transfer: Transfer
    bank: str


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


async def valid_signature(
    request: Request,
    schema: StarkBankInvoiceEvent,
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
    "/starkbank/invoices",
    dependencies=[Depends(valid_signature)],
)
async def starkbank_invoices_webhook(
    schema: StarkBankInvoiceEvent,
    transfer_sender: TransferSender = Depends(get_transfer_sender),
) -> None:
    transfer_amount = schema.event.log.invoice.amount - schema.event.log.invoice.fee

    transfer = Transfer(
        account=settings.default_account,
        amount=transfer_amount,
    )

    transfer_sender: TransferSender = get_transfer_sender()
    transfer_sender.send(transfer)
