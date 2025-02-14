from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.types import Invoice
from app.services.invoice_service.implementation import StarkBankInvoiceSender
from app.services.invoice_service.interface import InvoiceSender
from app.core.config import config

router = APIRouter()


class InvoiceRequest(BaseModel):
    invoice: Invoice
    bank: str


def get_invoice_sender(schema: InvoiceRequest) -> StarkBankInvoiceSender:
    if schema.bank != "starkbank":
        raise HTTPException(
            status_code=400,
            detail="Invalid bank. Only 'starkbank' is supported at the moment.",
        )
    return StarkBankInvoiceSender(config.starkbank_project)


@router.post("/")
async def create_invoice(
    schema: InvoiceRequest,
    invoice_sender: InvoiceSender = Depends(get_invoice_sender),
) -> dict:
    invoice_sender.send(schema.invoice)

    return {"message": "Invoice created successfully", "invoice": schema.invoice}
