import pytest
from unittest.mock import Mock, patch
from app.jobs.invoice_random_people import invoice_random_people
from app.models.types import Person, Invoice


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="123.456.789-00")


def test_invoice_random_people(mock_person):
    with patch(
        "app.jobs.invoice_random_people.StarkBankInvoiceSender"
    ) as mock_sender, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter:

        sender_instance = Mock()
        mock_sender.return_value = sender_instance

        getter_instance = Mock()
        getter_instance.get_random_person.return_value = mock_person
        mock_getter.return_value = getter_instance

        n_min = 5
        n_max = 5
        invoice_random_people(n_min, n_max)

        assert getter_instance.get_random_person.call_count == 5

        assert sender_instance.send_batch.call_count == 1

        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 5

        for invoice in sent_invoices:
            assert isinstance(invoice, Invoice)
            assert invoice.person == mock_person
            assert 100 <= invoice.amount < 10000000000


def test_invoice_random_people_range(mock_person):
    with patch(
        "app.jobs.invoice_random_people.StarkBankInvoiceSender"
    ) as mock_sender, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter:

        sender_instance = Mock()
        mock_sender.return_value = sender_instance

        getter_instance = Mock()
        getter_instance.get_random_person.return_value = mock_person
        mock_getter.return_value = getter_instance

        n_min = 2
        n_max = 5
        invoice_random_people(n_min, n_max)

        # Verify that number of calls is within range
        call_count = getter_instance.get_random_person.call_count
        assert n_min <= call_count <= n_max

        # Verify batch was sent once
        assert sender_instance.send_batch.call_count == 1

        # Verify number of invoices matches number of persons
        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == call_count

        # Verify invoice properties
        for invoice in sent_invoices:
            assert isinstance(invoice, Invoice)
            assert invoice.person == mock_person
            assert 100 <= invoice.amount < 10000000000


def test_invoice_random_people_invalid_range():
    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(5, 2)
    assert str(exc_info.value) == "n_min cannot be greater than n_max"


def test_invoice_random_people_zero_min(mock_person):
    with patch(
        "app.jobs.invoice_random_people.StarkBankInvoiceSender"
    ) as mock_sender, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter:

        sender_instance = Mock()
        mock_sender.return_value = sender_instance

        getter_instance = Mock()
        getter_instance.get_random_person.return_value = mock_person
        mock_getter.return_value = getter_instance

        n_min = 0
        n_max = 2
        invoice_random_people(n_min, n_max)

        # Verify that number of calls is within range
        call_count = getter_instance.get_random_person.call_count
        assert n_min <= call_count <= n_max

        # Verify batch was sent once if there were any invoices
        if call_count > 0:
            assert sender_instance.send_batch.call_count == 1
            sent_invoices = sender_instance.send_batch.call_args[0][0]
            assert len(sent_invoices) == call_count
            
            # Verify invoice properties
            for invoice in sent_invoices:
                assert isinstance(invoice, Invoice)
                assert invoice.person == mock_person
                assert 100 <= invoice.amount < 10000000000
        else:
            assert sender_instance.send_batch.call_count == 0


def test_invoice_random_people_negative_numbers():
    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(-1, 5)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"

    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(1, -5)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"

    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(-2, -1)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"
