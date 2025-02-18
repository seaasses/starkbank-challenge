from app.core.config import settings
from app.models.types import Invoice
from app.services.invoice_service.implementation import QueueInvoiceSender
from app.services.random_person_getter.implementation import RandomPersonGetter
from app.services.queue_service.implementation import RabbitMQService
import random
import os


def invoice_random_people(n_min: int, n_max: int):
    if n_min < 0 or n_max < 0:
        raise ValueError("n_min and n_max must be non-negative")
    if n_min > n_max:
        raise ValueError("n_min cannot be greater than n_max")

    n = random.randint(n_min, n_max)
    invoices = []

    queue_service = RabbitMQService(
        queue_name="task_queue",
        rabbitmq_host=os.getenv("RABBITMQ_HOST"),
        rabbitmq_port=os.getenv("RABBITMQ_PORT"),
        rabbitmq_user=os.getenv("RABBITMQ_USER"),
        rabbitmq_pass=os.getenv("RABBITMQ_PASS"),
    )
    invoice_sender = QueueInvoiceSender(queue_service)
    person_getter = RandomPersonGetter()

    for _ in range(n):
        person = person_getter.get_random_person()
        amount = random.randint(100, 10000000000 - 1)
        invoice = Invoice(amount=amount, person=person)
        invoices.append(invoice)

    if len(invoices) > 0:
        invoice_sender.send_batch(invoices)
