import pytest
from datetime import date, datetime
from pydantic import ValidationError
from app.models.types import (
    Person,
    AccountType,
    Account,
    Transfer,
    Invoice,
    StarkBankEvent,
)


def test_person_valid():
    person = Person(name="John Doe", cpf="123.456.789-00")
    assert person.name == "John Doe"
    assert person.cpf == "123.456.789-00"


def test_person_invalid_name():
    with pytest.raises(ValidationError) as exc_info:
        Person(name="", cpf="123.456.789-00")
    assert "String should have at least 1 character" in str(exc_info.value)


def test_account_type_valid():
    assert AccountType.CHECKING == "checking"
    assert AccountType.PAYMENT == "payment"
    assert AccountType.SALARY == "salary"
    assert AccountType.SAVINGS == "savings"


def test_account_type_invalid():
    with pytest.raises(ValueError) as exc_info:
        AccountType("invalid")
    assert "is not a valid AccountType" in str(exc_info.value)


def test_account_valid():
    account = Account(
        bank_code="341",
        branch="0001",
        account="1234567",
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )
    assert account.bank_code == "341"
    assert account.branch == "0001"
    assert account.account == "1234567"
    assert account.name == "Test Account"
    assert account.tax_id == "123.456.789-00"
    assert account.account_type == AccountType.CHECKING


def test_account_valid_with_hyphen():
    account = Account(
        bank_code="341",
        branch="0001",
        account="123456-7",
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )
    assert account.account == "123456-7"


def test_account_invalid_account_number():
    with pytest.raises(ValidationError) as exc_info:
        Account(
            bank_code="341",
            branch="0001",
            account="invalid",  # Invalid format
            name="Test Account",
            tax_id="123.456.789-00",
            account_type=AccountType.CHECKING,
        )
    assert "Invalid account number" in str(exc_info.value)


def test_account_invalid_name():
    with pytest.raises(ValidationError) as exc_info:
        Account(
            bank_code="341",
            branch="0001",
            account="1234567",
            name="",  # Empty name
            tax_id="123.456.789-00",
            account_type=AccountType.CHECKING,
        )
    assert "String should have at least 1 character" in str(exc_info.value)


def test_transfer_valid():
    account = Account(
        bank_code="341",
        branch="0001",
        account="1234567",
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )
    transfer = Transfer(account=account, amount=1000)
    assert transfer.account == account
    assert transfer.amount == 1000


def test_transfer_invalid_amount():
    account = Account(
        bank_code="341",
        branch="0001",
        account="1234567",
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )
    
    # Test amount <= 0
    with pytest.raises(ValidationError) as exc_info:
        Transfer(account=account, amount=0)
    assert "Input should be greater than 0" in str(exc_info.value)

    # Test amount >= 10000000000
    with pytest.raises(ValidationError) as exc_info:
        Transfer(account=account, amount=10000000000)
    assert "Input should be less than 10000000000" in str(exc_info.value)


def test_invoice_valid():
    person = Person(name="John Doe", cpf="123.456.789-00")
    invoice = Invoice(amount=1000, person=person, due_date=date(2024, 12, 31))
    assert invoice.amount == 1000
    assert invoice.person == person
    assert invoice.due_date == date(2024, 12, 31)


def test_invoice_optional_due_date():
    person = Person(name="John Doe", cpf="123.456.789-00")
    invoice = Invoice(amount=1000, person=person)
    assert invoice.due_date is None


def test_invoice_invalid_amount():
    person = Person(name="John Doe", cpf="123.456.789-00")
    
    # Test amount <= 0
    with pytest.raises(ValidationError) as exc_info:
        Invoice(amount=0, person=person)
    assert "Input should be greater than 0" in str(exc_info.value)

    # Test amount >= 10000000000
    with pytest.raises(ValidationError) as exc_info:
        Invoice(amount=10000000000, person=person)
    assert "Input should be less than 10000000000" in str(exc_info.value)


def test_starkbank_event_valid():
    event = StarkBankEvent(
        created=datetime(2024, 1, 1, 12, 0),
        id="1234567890",
        log={"type": "credited", "invoice": {"amount": 1000, "fee": 100}},
        subscription="invoice",
        workspaceId="workspace-1",
    )
    assert event.created == datetime(2024, 1, 1, 12, 0)
    assert event.id == "1234567890"
    assert event.log["type"] == "credited"
    assert event.subscription == "invoice"
    assert event.workspaceId == "workspace-1" 