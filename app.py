from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from invoice import Invoice
from starkbank_invoice_sender import StarkBankInvoiceSender
from invoice_sender import InvoiceSender
from config import config

app = FastAPI(
    title="Stark Bank Challenge API",
    description="API for a client that uses Stark Bank (or any other implemented bank)",
    version="1.0.0",
)


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


@app.post("/invoices/")
async def create_invoice(
    schema: InvoiceRequest,
    invoice_sender: InvoiceSender = Depends(get_invoice_sender),
) -> dict:
    invoice_sender.send(schema.invoice)

    return {
        "message": "Invoice created successfully",
        "invoice": {
            "amount": schema.invoice.amount,
            "person": {
                "name": schema.invoice.person.name,
                "cpf": schema.invoice.person.cpf,
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
