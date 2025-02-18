import pytest
from unittest.mock import Mock
from datetime import date
from app.models.types import Invoice, Person
from app.services.invoice_service.implementation import QueueInvoiceSender
from app.services.queue_service.interface import QueueService


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="803.778.410-05")


@pytest.fixture
def mock_queue_service():
    return Mock(spec=QueueService)


@pytest.fixture
def invoice_sender(mock_queue_service):
    return QueueInvoiceSender(mock_queue_service)


def test_send_publishes_to_queue(invoice_sender, mock_person, mock_queue_service):
    # Create and send invoice
    invoice = Invoice(amount=1000, person=mock_person, due_date=date(2024, 12, 31))
    invoice_sender.send(invoice)

    # Verify message was published to queue
    mock_queue_service.publish_message.assert_called_once()
    published_message = mock_queue_service.publish_message.call_args[0][0]
    
    assert published_message["type"] == "invoice"
    assert published_message["data"]["amount"] == 1000
    assert published_message["data"]["person"]["name"] == mock_person.name
    assert published_message["data"]["person"]["cpf"] == mock_person.cpf
    assert published_message["data"]["due_date"] == "2024-12-31"


def test_send_batch_publishes_all_invoices(invoice_sender, mock_person, mock_queue_service):
    # Create and send invoices
    invoices = [
        Invoice(amount=1000, person=mock_person),
        Invoice(amount=2000, person=mock_person),
    ]
    invoice_sender.send_batch(invoices)

    # Verify all messages were published
    mock_queue_service.publish_messages.assert_called_once()
    published_messages = mock_queue_service.publish_messages.call_args[0][0]
    
    assert len(published_messages) == 2
    assert all(msg["type"] == "invoice" for msg in published_messages)
    assert published_messages[0]["data"]["amount"] == 1000
    assert published_messages[1]["data"]["amount"] == 2000


def test_send_empty_batch(invoice_sender, mock_queue_service):
    # Setup mock return value
    mock_queue_service.publish_messages.return_value = []
    
    # Send empty batch
    result = invoice_sender.send_batch([])
    
    # Verify no messages were published
    mock_queue_service.publish_messages.assert_called_once_with([])
    assert result == [] 