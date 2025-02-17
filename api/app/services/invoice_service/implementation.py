import starkbank
from app.models.types import Invoice
from app.services.invoice_service.interface import InvoiceSender


class StarkBankInvoiceSender(InvoiceSender):
    def __init__(self, starkbank_project: starkbank.Project):
        self.starkbank_project = starkbank_project

    def send_batch(self, invoices: list[Invoice]):
        stark_invoices = [
            self.__convert_to_starkbank_invoice(invoice) for invoice in invoices
        ]
        starkbank.invoice.create(stark_invoices, user=self.starkbank_project)

    def send(self, invoice: Invoice):
        self.send_batch([invoice])

    def __convert_to_starkbank_invoice(self, invoice: Invoice) -> starkbank.Invoice:
        return starkbank.Invoice(
            amount=invoice.amount,
            name=invoice.person.name,
            tax_id=invoice.person.cpf,
            due=invoice.due_date,
        )
