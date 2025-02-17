import pytest
from unittest.mock import Mock, patch
from app.models.types import Transfer, Account, AccountType
from app.services.transfer_service.implementation import StarkBankTransferSender


@pytest.fixture
def mock_account():
    return Account(
        bank_code="341",
        branch="0001",
        account="1234567",
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )


@pytest.fixture
def mock_starkbank_project():
    return Mock(environment="sandbox", id="123", private_key="test-key")


def test_send_converts_to_starkbank_transfer(mock_account, mock_starkbank_project):
    with patch("starkbank.transfer.create") as mock_create:
        transfer = Transfer(account=mock_account, amount=1000)
        sender = StarkBankTransferSender(mock_starkbank_project)
        sender.send(transfer)

        mock_create.assert_called_once()
        created_transfers = mock_create.call_args[0][0]
        assert len(created_transfers) == 1
        
        starkbank_transfer = created_transfers[0]
        assert starkbank_transfer.bank_code == "341"
        assert starkbank_transfer.branch_code == "0001"
        assert starkbank_transfer.account_number == "1234567"
        assert starkbank_transfer.account_type == "checking"
        assert starkbank_transfer.name == "Test Account"
        assert starkbank_transfer.tax_id == "123.456.789-00"
        assert starkbank_transfer.amount == 1000


def test_send_uses_correct_project(mock_account, mock_starkbank_project):
    with patch("starkbank.transfer.create") as mock_create:
        transfer = Transfer(account=mock_account, amount=1000)
        sender = StarkBankTransferSender(mock_starkbank_project)
        sender.send(transfer)

        mock_create.assert_called_once()
        assert mock_create.call_args[1]["user"] == mock_starkbank_project


def test_send_handles_api_error(mock_account, mock_starkbank_project):
    with patch("starkbank.transfer.create") as mock_create:
        mock_create.side_effect = Exception("API Error")

        transfer = Transfer(account=mock_account, amount=1000)
        sender = StarkBankTransferSender(mock_starkbank_project)

        with pytest.raises(Exception) as exc_info:
            sender.send(transfer)
        assert "API Error" in str(exc_info.value)


def test_send_with_hyphenated_account(mock_starkbank_project):
    account = Account(
        bank_code="341",
        branch="0001",
        account="123456-7",  
        name="Test Account",
        tax_id="123.456.789-00",
        account_type=AccountType.CHECKING,
    )

    with patch("starkbank.transfer.create") as mock_create:
        transfer = Transfer(account=account, amount=1000)
        sender = StarkBankTransferSender(mock_starkbank_project)
        sender.send(transfer)

        mock_create.assert_called_once()
        created_transfers = mock_create.call_args[0][0]
        starkbank_transfer = created_transfers[0]
        assert starkbank_transfer.account_number == "123456-7" 