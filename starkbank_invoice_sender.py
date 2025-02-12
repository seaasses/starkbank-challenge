import starkbank
from invoice_sender import InvoiceSender
from invoice import Invoice


class StarkBankInvoiceSender(InvoiceSender):
    def __init__(self, starkbank_project: starkbank.Project):
        self.starkbank_project = starkbank_project
        super().__init__()

    def send(self, invoice: Invoice):
        stark_invoice = self.__convert_to_starkbank_invoice(invoice)
        starkbank.invoice.create([stark_invoice], user=self.starkbank_project)

    def __convert_to_starkbank_invoice(self, invoice: Invoice) -> starkbank.Invoice:
        return starkbank.Invoice(
            amount=invoice.amount,
            name=invoice.person.name,
            tax_id=invoice.person.cpf,
            due=invoice.due_date,
        )
