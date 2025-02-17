import pytest
from unittest.mock import Mock, patch
from datetime import date
from app.models.types import Invoice, Person
from app.services.invoice_service.implementation import StarkBankInvoiceSender


@pytest.fixture
def mock_person():
    return Person(name="John Doe", cpf="803.778.410-05")


@pytest.fixture
def mock_starkbank_project():
    return Mock(environment="sandbox", id="123", private_key="test-key")


@pytest.fixture
def invoice_sender(mock_starkbank_project):
    return StarkBankInvoiceSender(mock_starkbank_project)


def test_send_converts_to_starkbank_invoice(invoice_sender, mock_person):
    with patch("starkbank.invoice.create") as mock_create:
        # Create and send invoice
        invoice = Invoice(amount=1000, person=mock_person, due_date=date(2024, 12, 31))
        invoice_sender.send(invoice)

        # Verify conversion to StarkBank format
        mock_create.assert_called_once()
        created_invoices = mock_create.call_args[0][0]
        assert len(created_invoices) == 1
        
        starkbank_invoice = created_invoices[0]
        assert starkbank_invoice.amount == 1000
        assert starkbank_invoice.name == mock_person.name
        assert starkbank_invoice.tax_id == mock_person.cpf
        assert starkbank_invoice.due == date(2024, 12, 31)


def test_send_batch_converts_all_invoices(invoice_sender, mock_person):
    with patch("starkbank.invoice.create") as mock_create:
        # Create and send invoices
        invoices = [
            Invoice(amount=1000, person=mock_person),
            Invoice(amount=2000, person=mock_person),
        ]
        invoice_sender.send_batch(invoices)

        # Verify conversion of all invoices
        mock_create.assert_called_once()
        created_invoices = mock_create.call_args[0][0]
        assert len(created_invoices) == 2
        
        # Verify each converted invoice
        assert created_invoices[0].amount == 1000
        assert created_invoices[0].name == mock_person.name
        assert created_invoices[0].tax_id == mock_person.cpf
        
        assert created_invoices[1].amount == 2000
        assert created_invoices[1].name == mock_person.name
        assert created_invoices[1].tax_id == mock_person.cpf


def test_send_uses_correct_project(invoice_sender, mock_person, mock_starkbank_project):
    with patch("starkbank.invoice.create") as mock_create:
        invoice = Invoice(amount=1000, person=mock_person)
        invoice_sender.send(invoice)

        # Verify project was passed correctly
        mock_create.assert_called_once()
        assert mock_create.call_args[1]["user"] == mock_starkbank_project


def test_send_empty_batch(invoice_sender):
    with patch("starkbank.invoice.create") as mock_create:
        invoice_sender.send_batch([])
        
        # Verify empty list is handled correctly
        mock_create.assert_called_once()
        created_invoices = mock_create.call_args[0][0]
        assert len(created_invoices) == 0 