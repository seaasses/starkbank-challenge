from fastapi import APIRouter, Depends
from functools import lru_cache

from app.models.types import Invoice
from app.services.invoice_service.implementation import QueueInvoiceSender
from app.services.invoice_service.interface import InvoiceSender
from app.services.queue_service.implementation import RabbitMQService
import os

router = APIRouter()


@lru_cache(maxsize=1)
def get_invoice_sender() -> InvoiceSender:
    queue_service = RabbitMQService(
        queue_name="task_queue",
        rabbitmq_host=os.getenv("RABBITMQ_HOST"),
        rabbitmq_port=os.getenv("RABBITMQ_PORT"),
        rabbitmq_user=os.getenv("RABBITMQ_USER"),
        rabbitmq_pass=os.getenv("RABBITMQ_PASS"),
    )

    return QueueInvoiceSender(queue_service)


@router.post("/")
async def create_invoice(
    schema: Invoice,
    invoice_sender: InvoiceSender = Depends(get_invoice_sender),
) -> dict:
    invoice_sender.send(schema)

    return {"message": "Invoice created successfully", "invoice": schema}
