import pytest
from unittest.mock import Mock, patch
from app.jobs.invoice_random_people import invoice_random_people
from app.models.types import Person, Invoice


@pytest.fixture
def mock_thread_lock():
    mock = Mock()
    mock.lock.return_value = True
    mock.unlock.return_value = True
    return mock


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="803.778.410-05")


def test_invoice_random_people(mock_person, mock_thread_lock):
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
        invoice_random_people(n_min, n_max, mock_thread_lock)

        mock_thread_lock.lock.assert_called_once_with("job:invoice_random_people", 600)
        mock_thread_lock.unlock.assert_called_once_with("job:invoice_random_people")

        assert getter_instance.get_random_person.call_count == 5

        assert sender_instance.send_batch.call_count == 1

        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 5

        for invoice in sent_invoices:
            assert isinstance(invoice, Invoice)
            assert invoice.person == mock_person
            assert 100 <= invoice.amount < 10000000000


def test_invoice_random_people_range(mock_person, mock_thread_lock):
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
        invoice_random_people(n_min, n_max, mock_thread_lock)

        mock_thread_lock.lock.assert_called_once_with("job:invoice_random_people", 600)
        mock_thread_lock.unlock.assert_called_once_with("job:invoice_random_people")

        assert 2 <= getter_instance.get_random_person.call_count <= 5

        assert sender_instance.send_batch.call_count == 1

        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert 2 <= len(sent_invoices) <= 5

        for invoice in sent_invoices:
            assert isinstance(invoice, Invoice)
            assert invoice.person == mock_person
            assert 100 <= invoice.amount < 10000000000


def test_invoice_random_people_invalid_range(mock_thread_lock):
    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(5, 2, mock_thread_lock)
    assert str(exc_info.value) == "n_min cannot be greater than n_max"


def test_invoice_random_people_zero_min(mock_person, mock_thread_lock):
    with patch(
        "app.jobs.invoice_random_people.StarkBankInvoiceSender"
    ) as mock_sender, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.random.randint"
    ) as mock_randint:

        # Mock random to always return 0 for this test
        mock_randint.return_value = 0

        sender_instance = Mock()
        mock_sender.return_value = sender_instance

        getter_instance = Mock()
        getter_instance.get_random_person.return_value = mock_person
        mock_getter.return_value = getter_instance

        n_min = 0
        n_max = 2
        invoice_random_people(n_min, n_max, mock_thread_lock)

        mock_thread_lock.lock.assert_called_once_with("job:invoice_random_people", 600)
        mock_thread_lock.unlock.assert_called_once_with("job:invoice_random_people")

        assert getter_instance.get_random_person.call_count == 0
        assert sender_instance.send_batch.call_count == 0


def test_invoice_random_people_negative_numbers(mock_thread_lock):
    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(-1, 5, mock_thread_lock)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"

    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(1, -5, mock_thread_lock)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"

    with pytest.raises(ValueError) as exc_info:
        invoice_random_people(-2, -1, mock_thread_lock)
    assert str(exc_info.value) == "n_min and n_max must be non-negative"


def test_invoice_random_people_zero_min_with_invoices(mock_person, mock_thread_lock):
    with patch(
        "app.jobs.invoice_random_people.StarkBankInvoiceSender"
    ) as mock_sender, patch(
        "app.jobs.invoice_random_people.RandomPersonGetter"
    ) as mock_getter, patch(
        "app.jobs.invoice_random_people.random.randint"
    ) as mock_randint:

        mock_randint.side_effect = [2, 1000, 2000]

        sender_instance = Mock()
        mock_sender.return_value = sender_instance

        getter_instance = Mock()
        getter_instance.get_random_person.return_value = mock_person
        mock_getter.return_value = getter_instance

        n_min = 0
        n_max = 2
        invoice_random_people(n_min, n_max, mock_thread_lock)

        mock_thread_lock.lock.assert_called_once_with("job:invoice_random_people", 600)
        mock_thread_lock.unlock.assert_called_once_with("job:invoice_random_people")

        assert getter_instance.get_random_person.call_count == 2
        assert sender_instance.send_batch.call_count == 1

        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 2

        for invoice in sent_invoices:
            assert isinstance(invoice, Invoice)
            assert invoice.person == mock_person
            assert 100 <= invoice.amount < 10000000000
