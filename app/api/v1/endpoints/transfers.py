from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.types import Transfer
from app.services.transfer_service.implementation import StarkBankTransferSender
from app.services.transfer_service.interface import TransferSender
from app.core.config import settings

router = APIRouter()


class TransferRequest(BaseModel):
    transfer: Transfer
    bank: str


def get_transfer_sender(schema: TransferRequest) -> StarkBankTransferSender:
    if schema.bank != "starkbank":
        raise HTTPException(
            status_code=400,
            detail="Invalid bank. Only 'starkbank' is supported at the moment.",
        )
    return StarkBankTransferSender(settings.starkbank_project)


@router.post("/")
async def create_transfer(
    schema: TransferRequest,
    transfer_sender: TransferSender = Depends(get_transfer_sender),
) -> dict:
    transfer_sender.send(schema.transfer)

    return {"message": "Transfer created successfully", "transfer": schema.transfer}
