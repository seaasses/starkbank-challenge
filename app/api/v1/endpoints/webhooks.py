from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.types import Transfer
from app.services.transfer_service.implementation import StarkBankTransferSender
from app.services.transfer_service.interface import TransferSender
from app.core.config import settings
from app.models.types import StarkBankInvoiceEvent

router = APIRouter()


class TransferRequest(BaseModel):
    transfer: Transfer
    bank: str


@router.post("/starkbank/invoices")
async def starkbank_invoices_webhook(
    schema: StarkBankInvoiceEvent,
) -> None:
    # TODO see if there is a way to validate the post is from Stark Bank
    if schema.event.log.type == "credited":
        print("CREDITED")
