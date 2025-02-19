from app.core.config import settings
from app.models.types import Invoice
from app.services.invoice_service.implementation import StarkBankInvoiceSender
from app.services.random_person_getter.implementation import RandomPersonGetter
from app.services.thread_lock.interface import ThreadLock
import random


def invoice_random_people(n_min: int, n_max: int, thread_lock: ThreadLock):
    lock_key = "job:invoice_random_people"
    if thread_lock.lock(lock_key, 600):
        if n_min < 0 or n_max < 0:
            raise ValueError("n_min and n_max must be non-negative")
        if n_min > n_max:
            raise ValueError("n_min cannot be greater than n_max")

        n = random.randint(n_min, n_max)
        invoices = []
        invoice_sender = StarkBankInvoiceSender(settings.starkbank_project)
        person_getter = RandomPersonGetter()
        for _ in range(n):
            person = person_getter.get_random_person()
            amount = random.randint(100, 10000000000 - 1)
            invoice = Invoice(amount=amount, person=person)
            invoices.append(invoice)

        if len(invoices) > 0:
            invoice_sender.send_batch(invoices)

        thread_lock.unlock(lock_key)
