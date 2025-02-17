import pytest
from unittest.mock import Mock, patch
from app.jobs.transfer_starkbank_undelivered_credited_invoices import (
    transfer_starkbank_undelivered_credited_invoices,
)
from app.models.types import StarkBankEvent, Transfer, Account, AccountType
from datetime import datetime


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


def test_transfer_starkbank_undelivered_credited_invoices_basic(mock_credited_invoice_event, mock_account):
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
        transfer_starkbank_undelivered_credited_invoices()

        # Verify event fetching
        assert fetcher_instance.fetch_undelivered_events.call_count == 1

        # Verify transfer creation and sending
        assert transfer_sender_instance.send.call_count == 1
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.account == mock_account
        assert sent_transfer.amount == 900  # 1000 - 100

        # Verify event status update
        assert status_changer_instance.mark_as_delivered.call_count == 1
        assert status_changer_instance.mark_as_delivered.call_args[0][0] == "1234567890"


def test_transfer_starkbank_undelivered_credited_invoices_filtering(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_non_invoice_event,
    mock_account,
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
        transfer_starkbank_undelivered_credited_invoices()

        # Verify only one transfer was created (for the credited invoice event)
        assert transfer_sender_instance.send.call_count == 1
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.amount == 900

        # Verify all events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 3
        delivered_event_ids = [
            call_args[0][0]
            for call_args in status_changer_instance.mark_as_delivered.call_args_list
        ]
        assert "1234567890" in delivered_event_ids  # credited invoice event
        assert "0987654321" in delivered_event_ids  # non-credited invoice event
        assert "5555555555" in delivered_event_ids  # non-invoice event


def test_transfer_starkbank_undelivered_credited_invoices_no_events():
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
        transfer_starkbank_undelivered_credited_invoices()

        # Verify no transfers were created
        assert transfer_sender_instance.send.call_count == 0

        # Verify no events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 0


def test_transfer_starkbank_undelivered_events_all_marked_delivered(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_non_invoice_event,
    mock_account,
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
        transfer_starkbank_undelivered_credited_invoices()

        # Verify only one transfer was created (for the credited invoice event)
        assert transfer_sender_instance.send.call_count == 1
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.amount == 900

        # Verify all events were marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 3
        delivered_event_ids = [
            call_args[0][0]
            for call_args in status_changer_instance.mark_as_delivered.call_args_list
        ]
        assert "1234567890" in delivered_event_ids  # credited invoice event
        assert "0987654321" in delivered_event_ids  # non-credited invoice event
        assert "5555555555" in delivered_event_ids  # non-invoice event


def test_transfer_starkbank_undelivered_credited_invoices_error_handling(
    mock_credited_invoice_event,
    mock_non_credited_invoice_event,
    mock_account,
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
        transfer_starkbank_undelivered_credited_invoices()

        # Verify transfer was attempted for the credited event
        assert transfer_sender_instance.send.call_count == 1
        sent_transfer = transfer_sender_instance.send.call_args[0][0]
        assert isinstance(sent_transfer, Transfer)
        assert sent_transfer.amount == 900

        # Verify the failed event was not marked as delivered
        # but the non-credited event was marked as delivered
        assert status_changer_instance.mark_as_delivered.call_count == 1
        delivered_event_id = status_changer_instance.mark_as_delivered.call_args[0][0]
        assert delivered_event_id == "0987654321"  # ID of mock_non_credited_invoice_event 