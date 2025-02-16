from app.core.config import settings
from app.models.types import Invoice
from app.services.invoice_service.implementation import StarkBankInvoiceSender
from app.services.random_person_getter.implementation import RandomPersonGetter
import random


def invoice_random_people(n_min: int, n_max: int):
    n = random.randint(n_min, n_max)
    invoices = []
    invoice_sender = StarkBankInvoiceSender(settings.starkbank_project)
    person_getter = RandomPersonGetter()
    for _ in range(n):

        person = person_getter.get_random_person()
        amount = random.randint(100, 10000000000 - 1)
        invoice = Invoice(amount=amount, person=person)
        invoices.append(invoice)

    invoice_sender.send_batch(invoices)
