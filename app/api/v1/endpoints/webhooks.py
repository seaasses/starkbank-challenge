from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from app.models.types import Transfer
from app.core.config import settings
from app.models.types import StarkBankInvoiceEvent
from app.services.starkbank_signature_verifier.implementation import (
    StarkBankSignatureVerifier,
)

router = APIRouter()


class TransferRequest(BaseModel):
    transfer: Transfer
    bank: str


async def valid_signature(request: Request, schema: StarkBankInvoiceEvent):
    signature = request.headers.get("Digital-Signature")
    if not signature:
        raise HTTPException(
            status_code=401, detail="Unauthorized: Missing Digital-Signature header"
        )

    request_body = await request.body()

    signature_verifier = StarkBankSignatureVerifier(settings.starkbank_project)
    if not signature_verifier.check_signature(
        request_body, signature, schema.event.created
    ):
        raise HTTPException(status_code=401, detail="Unauthorized:Invalid signature")


@router.post(
    "/starkbank/invoices",
    dependencies=[Depends(valid_signature)],
)
async def starkbank_invoices_webhook(
    request: Request,
    schema: StarkBankInvoiceEvent,
) -> None:
    # TODO: implement the logic to handle the event
    print(f"evento {schema} recebido e validado")
