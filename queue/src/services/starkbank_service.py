import starkbank
from ..models.schemas import Invoice
from ..config.settings import get_private_key, STARK_PROJECT_ID, STARK_ENVIRONMENT


def send_invoice(invoice: Invoice):
    starkbank.user = starkbank.Project(
        environment=STARK_ENVIRONMENT,
        id=STARK_PROJECT_ID,
        private_key=get_private_key(),
    )

    starkbank_invoice = starkbank.Invoice(
        amount=invoice.amount,
        due=invoice.due_date,
        name=invoice.person.name,
        tax_id=invoice.person.cpf,
    )

    starkbank.invoice.create([starkbank_invoice])
