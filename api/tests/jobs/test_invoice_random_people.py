import pytest
from unittest.mock import Mock, patch
from app.models.types import Person, Invoice
from app.services.invoice_service.implementation import QueueInvoiceSender
from app.services.queue_service.implementation import RabbitMQService


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="803.778.410-05")


def test_invoice_random_people(mock_person):
    with patch(
        "app.jobs.invoice_random_people.QueueInvoiceSender"
    ) as mock_sender_class, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.RabbitMQService"
    ) as mock_queue_service:
        # Setup mocks
        mock_getter.return_value.get_random_person.return_value = mock_person
        mock_sender_instance = Mock()
        mock_sender_class.return_value = mock_sender_instance

        # Run function
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(1, 1)

        # Verify RabbitMQ service was created correctly
        mock_queue_service.assert_called_once()
        assert mock_queue_service.call_args[1]["queue_name"] == "task_queue"

        # Verify sender was created with queue service
        mock_sender_class.assert_called_once()
        assert mock_sender_class.call_args[0][0] == mock_queue_service.return_value

        # Verify person was created
        mock_getter.return_value.get_random_person.assert_called_once()

        # Verify invoices were sent
        mock_sender_instance.send_batch.assert_called_once()
        sent_invoices = mock_sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 1
        assert sent_invoices[0].person == mock_person


def test_invoice_random_people_range(mock_person):
    with patch(
        "app.jobs.invoice_random_people.QueueInvoiceSender"
    ) as mock_sender_class, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.RabbitMQService"
    ) as mock_queue_service, patch(
        "app.jobs.invoice_random_people.random.randint"
    ) as mock_randint:
        # Setup mocks
        mock_getter.return_value.get_random_person.return_value = mock_person
        mock_sender_instance = Mock()
        mock_sender_class.return_value = mock_sender_instance
        mock_randint.side_effect = [3, 1000, 2000, 3000]  # First call for n, then for each invoice amount

        # Run function
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(1, 5)

        # Verify random range for n
        assert mock_randint.call_args_list[0] == ((1, 5),)
        
        # Verify random range for amounts
        for i in range(1, 4):
            assert mock_randint.call_args_list[i] == ((100, 10000000000 - 1),)

        # Verify correct number of people were created
        assert mock_getter.return_value.get_random_person.call_count == 3

        # Verify invoices were sent
        mock_sender_instance.send_batch.assert_called_once()
        sent_invoices = mock_sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 3
        assert all(invoice.person == mock_person for invoice in sent_invoices)
        assert [invoice.amount for invoice in sent_invoices] == [1000, 2000, 3000]


def test_invoice_random_people_invalid_range():
    with pytest.raises(ValueError) as exc_info:
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(5, 1)
    assert "n_min cannot be greater than n_max" in str(exc_info.value)


def test_invoice_random_people_zero_min(mock_person):
    with patch(
        "app.jobs.invoice_random_people.QueueInvoiceSender"
    ) as mock_sender_class, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.random.randint"
    ) as mock_randint, patch(
        "app.jobs.invoice_random_people.RabbitMQService"
    ) as mock_queue_service:
        # Setup mocks
        mock_getter.return_value.get_random_person.return_value = mock_person
        mock_sender_instance = Mock()
        mock_sender_class.return_value = mock_sender_instance
        mock_randint.return_value = 0

        # Run function
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(0, 5)

        # Verify random range
        mock_randint.assert_called_once_with(0, 5)

        # Verify no people were created
        mock_getter.return_value.get_random_person.assert_not_called()

        # Verify no invoices were sent
        mock_sender_instance.send_batch.assert_not_called()


def test_invoice_random_people_negative_numbers():
    with pytest.raises(ValueError) as exc_info:
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(-1, 5)
    assert "n_min and n_max must be non-negative" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(0, -5)
    assert "n_min and n_max must be non-negative" in str(exc_info.value)


def test_invoice_random_people_zero_min_with_invoices(mock_person):
    with patch(
        "app.jobs.invoice_random_people.QueueInvoiceSender"
    ) as mock_sender_class, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.random.randint"
    ) as mock_randint, patch(
        "app.jobs.invoice_random_people.RabbitMQService"
    ) as mock_queue_service:
        # Setup mocks
        mock_getter.return_value.get_random_person.return_value = mock_person
        mock_sender_instance = Mock()
        mock_sender_class.return_value = mock_sender_instance
        mock_randint.side_effect = [2, 1000, 2000]  # First call for n, then for each invoice amount

        # Run function
        from app.jobs.invoice_random_people import invoice_random_people
        invoice_random_people(0, 5)

        # Verify random range for n
        assert mock_randint.call_args_list[0] == ((0, 5),)
        
        # Verify random range for amounts
        for i in range(1, 3):
            assert mock_randint.call_args_list[i] == ((100, 10000000000 - 1),)

        # Verify correct number of people were created
        assert mock_getter.return_value.get_random_person.call_count == 2

        # Verify invoices were sent
        mock_sender_instance.send_batch.assert_called_once()
        sent_invoices = mock_sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 2
        assert all(invoice.person == mock_person for invoice in sent_invoices)
        assert [invoice.amount for invoice in sent_invoices] == [1000, 2000]
