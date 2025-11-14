"""
Tests for Salesforce sync functionality.
"""
import pytest
from unittest.mock import Mock, patch
from cloud_functions.salesforce_sync.main import (
    salesforce_sync,
    _transform_record,
    _parse_sf_datetime
)


@pytest.fixture
def mock_request():
    """Mock HTTP request object."""
    request = Mock()
    request.get_json.return_value = {
        "object_type": "Account",
        "sync_type": "incremental"
    }
    return request


@pytest.fixture
def mock_sf_account():
    """Sample Salesforce Account record."""
    return {
        "Id": "0011234567890ABC",
        "Name": "Test Account",
        "Website": "https://test.com",
        "Industry": "Technology",
        "AnnualRevenue": 1000000.0,
        "OwnerId": "0051234567890ABC",
        "CreatedDate": "2024-01-01T12:00:00.000+0000",
        "LastModifiedDate": "2024-01-02T12:00:00.000+0000"
    }


@patch('cloud_functions.salesforce_sync.main.Salesforce')
@patch('cloud_functions.salesforce_sync.main.BigQueryClient')
@patch('cloud_functions.salesforce_sync.main.settings')
def test_salesforce_sync_success(mock_settings, mock_bq_client, mock_sf, mock_request):
    """Test successful Salesforce sync."""
    # Setup mocks
    mock_sf_instance = Mock()
    mock_sf.return_value = mock_sf_instance
    mock_sf_instance.query_all.return_value = {
        "records": [{
            "Id": "0011234567890ABC",
            "Name": "Test Account",
            "Website": "https://test.com"
        }],
        "totalSize": 1
    }
    
    mock_bq = Mock()
    mock_bq_client.return_value = mock_bq
    mock_bq.query.return_value = []
    
    # Execute
    response, status_code = salesforce_sync(mock_request)
    
    # Assert
    assert status_code == 200
    assert response["status"] == "success"
    assert "rows_synced" in response


def test_transform_record_account(mock_sf_account):
    """Test Account record transformation."""
    mapping = {
        "table": "sf_accounts",
        "fields": "Id, Name, Website"
    }
    
    row = _transform_record(mock_sf_account, "Account", mapping)
    
    assert row["account_id"] == "0011234567890ABC"
    assert row["account_name"] == "Test Account"
    assert row["website"] == "https://test.com"
    assert "ingested_at" in row


def test_transform_record_contact():
    """Test Contact record transformation."""
    contact = {
        "Id": "0031234567890ABC",
        "AccountId": "0011234567890ABC",
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "john.doe@example.com",
        "Phone": "+1234567890"
    }
    
    mapping = {
        "table": "sf_contacts",
        "fields": "Id, AccountId, FirstName, LastName, Email, Phone"
    }
    
    row = _transform_record(contact, "Contact", mapping)
    
    assert row["contact_id"] == "0031234567890ABC"
    assert row["account_id"] == "0011234567890ABC"
    assert row["email"] == "john.doe@example.com"
    assert row["first_name"] == "John"
    assert row["last_name"] == "Doe"


def test_parse_sf_datetime():
    """Test Salesforce datetime parsing."""
    # Valid datetime
    result = _parse_sf_datetime("2024-01-01T12:00:00.000+0000")
    assert result is not None
    assert "2024" in result
    
    # None input
    result = _parse_sf_datetime(None)
    assert result is None
    
    # Invalid datetime
    result = _parse_sf_datetime("invalid")
    assert result is None

