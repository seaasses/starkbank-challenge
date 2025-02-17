import pytest
from unittest.mock import Mock, patch
from app.jobs.invoice_random_people import invoice_random_people
from app.models.types import Person, Invoice


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="803.778.410-05")


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
        invoice_random_people(n_min, n_max)

        # Verify randint was called with correct args
        mock_randint.assert_called_once_with(n_min, n_max)

        # Verify that number of calls is within range
        call_count = getter_instance.get_random_person.call_count
        assert call_count == 0  # We know it's 0 because we mocked randint

        # Since we know n is 0, no invoices should be created or sent
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


def test_invoice_random_people_zero_min_with_invoices(mock_person):
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
        invoice_random_people(n_min, n_max)

        assert mock_randint.call_args_list[0] == ((n_min, n_max),)

        for i in range(1, 3):
            assert mock_randint.call_args_list[i] == ((100, 9999999999),)

        assert getter_instance.get_random_person.call_count == 2

        assert sender_instance.send_batch.call_count == 1
        sent_invoices = sender_instance.send_batch.call_args[0][0]
        assert len(sent_invoices) == 2

        assert sent_invoices[0].amount == 1000
        assert sent_invoices[1].amount == 2000
        for invoice in sent_invoices:
            assert invoice.person == mock_person
