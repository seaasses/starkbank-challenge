from app.models.types import Invoice
from app.services.invoice_service.interface import InvoiceSender
from app.services.queue_service.interface import QueueService


class QueueInvoiceSender(InvoiceSender):
    def __init__(self, queue_service: QueueService):
        self.queue_service = queue_service

    def send(self, invoice: Invoice) -> bool:
        invoice_message = self.__convert_to_message(invoice)
        return self.queue_service.publish_message(invoice_message)

    def send_batch(self, invoices: list[Invoice]) -> list[bool]:
        invoice_messages = [self.__convert_to_message(invoice) for invoice in invoices]
        return self.queue_service.publish_messages(invoice_messages)

    def __convert_to_message(self, invoice: Invoice):
        data = invoice.model_dump()
        if data.get("due_date"):
            data["due_date"] = data["due_date"].isoformat()
        return {
            "type": "invoice",
            "data": data,
        }
