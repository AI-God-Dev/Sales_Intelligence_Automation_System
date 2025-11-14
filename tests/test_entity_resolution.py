"""
Tests for entity resolution functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from entity_resolution.matcher import EntityMatcher


@pytest.fixture
def mock_bq_client():
    """Mock BigQuery client."""
    client = Mock()
    client.project_id = "test-project"
    client.dataset_id = "test_dataset"
    return client


@pytest.fixture
def entity_matcher(mock_bq_client):
    """Entity matcher instance with mocked BigQuery client."""
    return EntityMatcher(mock_bq_client)


def test_match_email_to_contact_exact_match(entity_matcher, mock_bq_client):
    """Test exact email match."""
    # Setup mock query result
    mock_bq_client.query.return_value = [{
        "contact_id": "0031234567890ABC",
        "account_id": "0011234567890ABC",
        "email": "test@example.com"
    }]
    
    result = entity_matcher.match_email_to_contact("test@example.com")
    
    assert result is not None
    assert result["contact_id"] == "0031234567890ABC"
    assert result["account_id"] == "0011234567890ABC"
    assert result["match_confidence"] == "exact"


def test_match_email_to_contact_no_match(entity_matcher, mock_bq_client):
    """Test email match with no results."""
    mock_bq_client.query.return_value = []
    
    result = entity_matcher.match_email_to_contact("nonexistent@example.com")
    
    assert result is None


def test_match_email_to_contact_manual_mapping(entity_matcher, mock_bq_client):
    """Test email match with manual mapping."""
    # Mock manual mapping check
    mock_bq_client.query.side_effect = [
        [{"sf_contact_id": "0031234567890ABC", "sf_account_id": "0011234567890ABC"}],  # Manual mapping
        []  # Regular query (shouldn't be called)
    ]
    
    result = entity_matcher.match_email_to_contact("mapped@example.com")
    
    assert result is not None
    assert result["match_confidence"] == "manual"


def test_match_phone_to_contact_exact_match(entity_matcher, mock_bq_client):
    """Test exact phone match."""
    mock_bq_client.query.return_value = [{
        "contact_id": "0031234567890ABC",
        "account_id": "0011234567890ABC",
        "phone": "+1234567890"
    }]
    
    result = entity_matcher.match_phone_to_contact("+1234567890")
    
    assert result is not None
    assert result["contact_id"] == "0031234567890ABC"
    assert result["match_confidence"] == "exact"


@patch('entity_resolution.matcher.normalize_phone')
def test_match_phone_to_contact_enhanced_fuzzy(mock_normalize, entity_matcher, mock_bq_client):
    """Test enhanced phone matching with fuzzy match."""
    from unittest.mock import MagicMock
    
    # Mock phone normalization
    mock_normalize.return_value = "+1234567890"
    
    # Mock exact match returning None, then fuzzy match returning result
    mock_bq_client.query.side_effect = [
        [],  # Exact match fails
        [{"contact_id": "0031234567890ABC", "account_id": "0011234567890ABC"}]  # Fuzzy match succeeds
    ]
    
    # Mock extract_last_10_digits
    with patch('entity_resolution.matcher.extract_last_10_digits') as mock_extract:
        mock_extract.return_value = "1234567890"
        
        result = entity_matcher.match_phone_to_contact_enhanced("1234567890")
        
        assert result is not None
        assert result["match_confidence"] == "fuzzy"


def test_update_participant_matches(entity_matcher, mock_bq_client):
    """Test batch participant matching."""
    # Mock query for unmatched participants
    mock_bq_client.query.side_effect = [
        [  # Unmatched participants
            {"participant_id": "p1", "email_address": "test@example.com"},
            {"participant_id": "p2", "email_address": "test2@example.com"}
        ],
        [  # Match result for first email
            {"contact_id": "0031234567890ABC", "account_id": "0011234567890ABC", "email": "test@example.com"}
        ],
        []  # No match for second email
    ]
    
    stats = entity_matcher.update_participant_matches(batch_size=100)
    
    assert stats["processed"] == 2
    assert stats["matched"] == 1
    assert stats["unmatched"] == 1


def test_update_call_matches(entity_matcher, mock_bq_client):
    """Test batch call matching."""
    # Mock query for unmatched calls
    mock_bq_client.query.side_effect = [
        [  # Unmatched calls
            {"call_id": "c1", "from_number": "+1234567890", "to_number": None}
        ],
        [  # Match result
            {"contact_id": "0031234567890ABC", "account_id": "0011234567890ABC", "phone": "+1234567890"}
        ]
    ]
    
    stats = entity_matcher.update_call_matches(batch_size=100)
    
    assert stats["processed"] == 1
    assert stats["matched"] == 1
