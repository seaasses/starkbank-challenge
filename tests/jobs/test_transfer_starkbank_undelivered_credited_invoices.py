import pytest
from unittest.mock import Mock, patch
from app.jobs.transfer_starkbank_undelivered_credited_invoices import (
    transfer_starkbank_undelivered_credited_invoices,
)
from app.models.types import StarkBankEvent, Transfer, Account, AccountType
from datetime import datetime


@pytest.fixture
def mock_thread_lock():
    mock = Mock()
    mock.lock.return_value = True
    mock.unlock.return_value = True
    return mock


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
def mock_credited_invoice_event():
    return StarkBankEvent(
        id="1234567890",
        subscription="invoice",
        log={
            "type": "credited",
            "invoice": {
                "amount": 1000,
                "fee": 100,
            },
        },
        created=datetime.now(),
        workspaceId="test-workspace",
    )


@pytest.fixture
def mock_non_credited_invoice_event():
    return StarkBankEvent(
        id="0987654321",
        subscription="invoice",
        log={
            "type": "created",
            "invoice": {
                "amount": 1000,
                "fee": 100,
            },
        },
        created=datetime.now(),
        workspaceId="test-workspace",
    )


@pytest.fixture
def mock_non_invoice_event():
    return StarkBankEvent(
        id="5555555555",
        subscription="transfer",
        log={
            "type": "credited",
            "transfer": {
                "amount": 1000,
            },
        },
        created=datetime.now(),
        workspaceId="test-workspace",
    )


def test_transfer_starkbank_undelivered_credited_invoices_basic(
    mock_credited_invoice_event, mock_account, mock_thread_lock
):
    with patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventFetcher"
    ) as mock_fetcher, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventStatusChanger"
    ) as mock_status_changer, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankTransferSender"
    ) as mock_transfer_sender, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.settings"
    ) as mock_settings:

        # Setup mocks
        fetcher_instance = Mock()
        fetcher_instance.fetch_undelivered_events.return_value = [mock_credited_invoice_event]
        mock_fetcher.return_value = fetcher_instance

        status_changer_instance = Mock()
        mock_status_changer.return_value = status_changer_instance

        transfer_sender_instance = Mock()
        mock_transfer_sender.return_value = transfer_sender_instance

        mock_settings.default_account = mock_account
        mock_settings.starkbank_project = "test-project"

        # Run function
        transfer_starkbank_undelivered_credited_invoices(mock_thread_lock)

        # Verify thread lock was used correctly
        mock_thread_lock.lock.assert_called_once_with(f"event:{mock_credited_invoice_event.id}")
        mock_thread_lock.unlock.assert_called_once_with(f"event:{mock_credited_invoice_event.id}")

        # Verify transfer was sent with correct amount
        transfer_sender_instance.send.assert_called_once()
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.account == mock_account
        assert sent_transfer.amount == 900  # 1000 - 100 fee

        # Verify event was marked as delivered
        status_changer_instance.mark_as_delivered.assert_called_once_with(
            mock_credited_invoice_event.id
        )


def test_transfer_starkbank_undelivered_credited_invoices_filtering(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_non_invoice_event,
    mock_account,
    mock_thread_lock,
):
    with patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventFetcher"
    ) as mock_fetcher, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventStatusChanger"
    ) as mock_status_changer, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankTransferSender"
    ) as mock_transfer_sender, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.settings"
    ) as mock_settings:

        # Setup mocks
        fetcher_instance = Mock()
        fetcher_instance.fetch_undelivered_events.return_value = [
            mock_credited_invoice_event,
            mock_non_credited_invoice_event,
            mock_non_invoice_event,
        ]
        mock_fetcher.return_value = fetcher_instance

        status_changer_instance = Mock()
        mock_status_changer.return_value = status_changer_instance

        transfer_sender_instance = Mock()
        mock_transfer_sender.return_value = transfer_sender_instance

        mock_settings.default_account = mock_account
        mock_settings.starkbank_project = "test-project"

        # Run function
        transfer_starkbank_undelivered_credited_invoices(mock_thread_lock)

        # Verify thread lock was used correctly for each event
        assert mock_thread_lock.lock.call_count == 3
        assert mock_thread_lock.unlock.call_count == 3

        # Verify transfer was sent only for credited invoice event
        transfer_sender_instance.send.assert_called_once()
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.account == mock_account
        assert sent_transfer.amount == 900  # 1000 - 100 fee

        # Verify all events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 3


def test_transfer_starkbank_undelivered_credited_invoices_no_events(mock_thread_lock):
    with patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventFetcher"
    ) as mock_fetcher, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventStatusChanger"
    ) as mock_status_changer, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankTransferSender"
    ) as mock_transfer_sender:

        # Setup mocks
        fetcher_instance = Mock()
        fetcher_instance.fetch_undelivered_events.return_value = []
        mock_fetcher.return_value = fetcher_instance

        status_changer_instance = Mock()
        mock_status_changer.return_value = status_changer_instance

        transfer_sender_instance = Mock()
        mock_transfer_sender.return_value = transfer_sender_instance

        # Run function
        transfer_starkbank_undelivered_credited_invoices(mock_thread_lock)

        # Verify no thread locks were used
        assert mock_thread_lock.lock.call_count == 0
        assert mock_thread_lock.unlock.call_count == 0

        # Verify no transfers were sent
        transfer_sender_instance.send.assert_not_called()

        # Verify no events were marked as delivered
        status_changer_instance.mark_as_delivered.assert_not_called()


def test_transfer_starkbank_undelivered_events_all_marked_delivered(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_non_invoice_event,
    mock_account,
    mock_thread_lock,
):
    with patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventFetcher"
    ) as mock_fetcher, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventStatusChanger"
    ) as mock_status_changer, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankTransferSender"
    ) as mock_transfer_sender, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.settings"
    ) as mock_settings:

        # Setup mocks
        fetcher_instance = Mock()
        fetcher_instance.fetch_undelivered_events.return_value = [
            mock_credited_invoice_event,
            mock_non_credited_invoice_event,
            mock_non_invoice_event,
        ]
        mock_fetcher.return_value = fetcher_instance

        status_changer_instance = Mock()
        mock_status_changer.return_value = status_changer_instance

        transfer_sender_instance = Mock()
        mock_transfer_sender.return_value = transfer_sender_instance

        mock_settings.default_account = mock_account
        mock_settings.starkbank_project = "test-project"

        # Run function
        transfer_starkbank_undelivered_credited_invoices(mock_thread_lock)

        # Verify thread lock was used correctly for each event
        assert mock_thread_lock.lock.call_count == 3
        assert mock_thread_lock.unlock.call_count == 3

        # Verify transfer was sent only for credited invoice event
        transfer_sender_instance.send.assert_called_once()
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.account == mock_account
        assert sent_transfer.amount == 900  # 1000 - 100 fee

        # Verify all events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 3


def test_transfer_starkbank_undelivered_credited_invoices_error_handling(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_account,
    mock_thread_lock,
):
    with patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventFetcher"
    ) as mock_fetcher, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankEventStatusChanger"
    ) as mock_status_changer, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.StarkBankTransferSender"
    ) as mock_transfer_sender, patch(
        "app.jobs.transfer_starkbank_undelivered_credited_invoices.settings"
    ) as mock_settings:

        # Setup mocks
        fetcher_instance = Mock()
        # Return two events - one will fail, one should succeed
        fetcher_instance.fetch_undelivered_events.return_value = [
            mock_credited_invoice_event,  # This one will fail
            mock_non_credited_invoice_event,  # This one should be marked as delivered
        ]
        mock_fetcher.return_value = fetcher_instance

        status_changer_instance = Mock()
        mock_status_changer.return_value = status_changer_instance

        transfer_sender_instance = Mock()
        # Make the first transfer fail
        transfer_sender_instance.send.side_effect = Exception("Transfer failed")
        mock_transfer_sender.return_value = transfer_sender_instance

        mock_settings.default_account = mock_account
        mock_settings.starkbank_project = "test-project"

        # Run function - should not raise exception
        transfer_starkbank_undelivered_credited_invoices(mock_thread_lock)

        # Verify thread lock was used correctly for each event
        assert mock_thread_lock.lock.call_count == 2
        assert mock_thread_lock.unlock.call_count == 2

        # Verify transfer was attempted for credited invoice event
        transfer_sender_instance.send.assert_called_once()

        # Verify both events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 2 