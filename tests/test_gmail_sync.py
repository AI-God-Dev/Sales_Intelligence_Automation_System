"""
Tests for Gmail sync functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from cloud_functions.gmail_sync.main import (
    gmail_sync,
    _transform_message,
    _parse_email_list,
    _extract_body,
    _parse_timestamp
)


@pytest.fixture
def mock_request():
    """Mock HTTP request object."""
    request = Mock()
    request.get_json.return_value = {
        "mailbox_email": "test@example.com",
        "sync_type": "incremental"
    }
    return request


@pytest.fixture
def mock_gmail_message():
    """Sample Gmail message structure."""
    return {
        "id": "msg123",
        "threadId": "thread123",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"}
            ],
            "body": {
                "data": "SGVsbG8gV29ybGQ="  # Base64 encoded "Hello World"
            },
            "mimeType": "text/plain"
        }
    }


@patch('cloud_functions.gmail_sync.main.get_gmail_service_for_user')
@patch('cloud_functions.gmail_sync.main.BigQueryClient')
def test_gmail_sync_success(mock_bq_client, mock_gmail_service, mock_request):
    """Test successful Gmail sync."""
    # Setup mocks
    mock_service = Mock()
    mock_gmail_service.return_value = mock_service
    
    mock_bq = Mock()
    mock_bq_client.return_value = mock_bq
    mock_bq.query.return_value = []  # No previous history
    
    # Mock Gmail API responses
    mock_service.users().getProfile().execute.return_value = {"historyId": "12345"}
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg123"}],
        "nextPageToken": None
    }
    mock_service.users().messages().get().execute.return_value = {
        "id": "msg123",
        "threadId": "thread123",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test"}
            ],
            "body": {"data": "SGVsbG8="}
        }
    }
    
    # Execute
    response, status_code = gmail_sync(mock_request)
    
    # Assert
    assert status_code == 200
    assert response["status"] in ["success", "partial"]
    assert "messages_synced" in response


def test_parse_email_list():
    """Test email list parsing."""
    # Single email
    assert _parse_email_list("test@example.com") == ["test@example.com"]
    
    # Multiple emails
    result = _parse_email_list("test1@example.com, test2@example.com")
    assert len(result) == 2
    assert "test1@example.com" in result
    assert "test2@example.com" in result
    
    # Email with name
    result = _parse_email_list("John Doe <john@example.com>")
    assert result == ["john@example.com"]
    
    # Empty string
    assert _parse_email_list("") == []


def test_extract_body():
    """Test body extraction."""
    # Plain text body
    payload = {
        "mimeType": "text/plain",
        "body": {"data": "SGVsbG8gV29ybGQ="}  # "Hello World"
    }
    text, html = _extract_body(payload)
    assert text == "Hello World"
    assert html == ""
    
    # HTML body
    payload = {
        "mimeType": "text/html",
        "body": {"data": "SGVsbG8gV29ybGQ="}
    }
    text, html = _extract_body(payload)
    assert text == ""
    assert html == "Hello World"


def test_parse_timestamp():
    """Test timestamp parsing."""
    # Valid timestamp
    result = _parse_timestamp("Mon, 1 Jan 2024 12:00:00 +0000")
    assert result is not None
    assert "2024" in result
    
    # Invalid timestamp
    result = _parse_timestamp("invalid")
    assert result is not None  # Should return current time


def test_transform_message(mock_gmail_message):
    """Test message transformation."""
    message_row, participants = _transform_message(mock_gmail_message, "test@example.com")
    
    assert message_row["message_id"] == "msg123"
    assert message_row["thread_id"] == "thread123"
    assert message_row["mailbox_email"] == "test@example.com"
    assert message_row["from_email"] == "sender@example.com"
    assert len(participants) > 0
    assert participants[0]["email_address"] == "sender@example.com"
    assert participants[0]["role"] == "from"


@patch('cloud_functions.gmail_sync.main.get_gmail_service_for_user')
@patch('cloud_functions.gmail_sync.main.BigQueryClient')
def test_gmail_sync_error_handling(mock_bq_client, mock_gmail_service, mock_request):
    """Test error handling in Gmail sync."""
    # Setup mocks to raise exception
    mock_gmail_service.side_effect = Exception("API Error")
    
    # Execute
    response, status_code = gmail_sync(mock_request)
    
    # Assert
    assert status_code == 500
    assert "error" in response

