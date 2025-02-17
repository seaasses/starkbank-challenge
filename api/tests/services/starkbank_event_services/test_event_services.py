import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.starkbank_event_services.implementation import (
    StarkBankEventFetcher,
    StarkBankEventStatusChanger,
)
from app.models.types import StarkBankEvent


@pytest.fixture
def mock_starkbank_project():
    return Mock(environment="sandbox", id="123", private_key="test-key")


class MockLog:
    def __init__(self):
        self.id = "log-123"
        self.created = datetime(2024, 1, 1, 12, 0)
        self.type = "credited"
        self.errors = []


class MockInvoice:
    def __init__(self):
        self.amount = 1000
        self.fee = 100


class MockEvent:
    def __init__(self):
        self.created = datetime(2024, 1, 1, 12, 0)
        self.id = "1234567890"
        self.subscription = "invoice"
        self.workspace_id = "workspace-1"
        self.log = MockLog()
        self.log.invoice = MockInvoice()


@pytest.fixture
def mock_starkbank_event():
    return MockEvent()


class MockCustomer:
    def __init__(self):
        self.name = "John Doe"
        self.id = "cust-123"


class MockComplexInvoice(MockInvoice):
    def __init__(self):
        super().__init__()
        self.tags = ["tag1", "tag2"]
        self.name = "John Doe"  # Flattened from customer
        self.customer_id = "cust-123"  # Flattened from customer


def test_event_fetcher_fetches_undelivered_events(mock_starkbank_project, mock_starkbank_event):
    with patch("starkbank.event.query") as mock_query:
        # Setup mock to return our test event
        mock_query.return_value = [mock_starkbank_event]
        
        # Create fetcher and get events
        fetcher = StarkBankEventFetcher(mock_starkbank_project)
        events = list(fetcher.fetch_undelivered_events())
        
        # Verify query was called with correct parameters
        mock_query.assert_called_once_with(
            is_delivered=False,
            user=mock_starkbank_project
        )
        
        # Verify event was converted correctly
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, StarkBankEvent)
        assert event.id == "1234567890"
        assert event.subscription == "invoice"
        assert event.workspaceId == "workspace-1"
        assert event.created == datetime(2024, 1, 1, 12, 0)
        
        # Verify log was converted correctly
        assert event.log["id"] == "log-123"
        assert event.log["type"] == "credited"
        assert event.log["errors"] == []
        assert event.log["invoice"]["amount"] == 1000
        assert event.log["invoice"]["fee"] == 100


def test_event_fetcher_handles_empty_result(mock_starkbank_project):
    with patch("starkbank.event.query") as mock_query:
        # Setup mock to return empty list
        mock_query.return_value = []
        
        # Create fetcher and get events
        fetcher = StarkBankEventFetcher(mock_starkbank_project)
        events = list(fetcher.fetch_undelivered_events())
        
        # Verify query was called
        mock_query.assert_called_once()
        
        # Verify no events were returned
        assert len(events) == 0


def test_event_fetcher_handles_complex_log_attributes(mock_starkbank_project):
    with patch("starkbank.event.query") as mock_query:
        # Create a mock event with nested attributes
        event = MockEvent()
        invoice = MockComplexInvoice()
        # Set attributes directly to match implementation's behavior
        invoice.amount = 1000
        invoice.fee = 100
        invoice.tags = ["tag1", "tag2"]
        invoice.name = "John Doe"  # Flattened customer attributes
        invoice.customer_id = "cust-123"  # Flattened customer attributes
        event.log.invoice = invoice
        mock_query.return_value = [event]
        
        # Create fetcher and get events
        fetcher = StarkBankEventFetcher(mock_starkbank_project)
        events = list(fetcher.fetch_undelivered_events())
        
        # Verify complex attributes were converted correctly
        event = events[0]
        assert event.log["invoice"]["amount"] == 1000
        assert event.log["invoice"]["fee"] == 100
        assert event.log["invoice"]["tags"] == ["tag1", "tag2"]
        assert event.log["invoice"]["name"] == "John Doe"
        assert event.log["invoice"]["customer_id"] == "cust-123"


def test_event_fetcher_handles_query_error(mock_starkbank_project):
    with patch("starkbank.event.query") as mock_query:
        # Setup mock to raise an exception
        mock_query.side_effect = Exception("API Error")
        
        # Create fetcher and try to get events
        fetcher = StarkBankEventFetcher(mock_starkbank_project)
        with pytest.raises(Exception) as exc_info:
            list(fetcher.fetch_undelivered_events())
        
        assert "API Error" in str(exc_info.value)


def test_event_status_changer_marks_event_as_delivered(mock_starkbank_project):
    with patch("starkbank.event.update") as mock_update:
        # Create status changer and mark event
        status_changer = StarkBankEventStatusChanger(mock_starkbank_project)
        status_changer.mark_as_delivered("event-123")
        
        # Verify update was called with correct parameters
        mock_update.assert_called_once_with(
            "event-123",
            is_delivered=True,
            user=mock_starkbank_project
        )


def test_event_status_changer_handles_update_error(mock_starkbank_project):
    with patch("starkbank.event.update") as mock_update:
        # Setup mock to raise an exception
        mock_update.side_effect = Exception("Update failed")
        
        # Create status changer and try to mark event
        status_changer = StarkBankEventStatusChanger(mock_starkbank_project)
        with pytest.raises(Exception) as exc_info:
            status_changer.mark_as_delivered("event-123")
        
        assert "Update failed" in str(exc_info.value) 