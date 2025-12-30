"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime, date
import os

# Set MOCK_MODE for all tests to avoid real API calls
os.environ["MOCK_MODE"] = "1"
os.environ["LOCAL_MODE"] = "1"


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client for testing."""
    from utils.bigquery_client import BigQueryClient
    
    client = Mock(spec=BigQueryClient)
    client.project_id = "test-project"
    client.dataset_id = "test_dataset"
    client.query = Mock(return_value=[])
    client.insert_rows = Mock(return_value=True)
    client.log_etl_run = Mock(return_value=True)
    return client


@pytest.fixture
def mock_vertex_ai_provider():
    """Mock Vertex AI model provider."""
    from ai.models import ModelProvider
    
    provider = Mock(spec=ModelProvider)
    provider.generate.return_value = '{"score": 75, "priority_score": 75, "budget_likelihood": 60, "engagement_score": 80, "recommendation": "Test recommendation", "reasons": ["Test reason"], "key_signals": ["Test signal"]}'
    provider.generate_stream.return_value = iter(["Test", " response"])
    return provider


@pytest.fixture
def mock_scoring_provider():
    """Mock scoring provider."""
    from ai.scoring import ScoringProvider
    
    provider = Mock(spec=ScoringProvider)
    provider.score_account.return_value = {
        "priority_score": 75,
        "budget_likelihood": 60,
        "engagement_score": 80,
        "reasoning": "Test reasoning",
        "recommended_action": "Test action",
        "key_signals": ["Signal 1", "Signal 2"]
    }
    return provider


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Sample account data for testing."""
    return {
        "account_id": "001XX000004ABCD",
        "account_name": "Test Corporation",
        "industry": "Technology",
        "annual_revenue": 1000000,
        "emails": [
            {
                "subject": "Budget Discussion",
                "body_text": "We are discussing our 2026 budget...",
                "sent_at": datetime(2025, 12, 15, 10, 30, 0),
                "from_email": "contact@testcorp.com"
            }
        ],
        "calls": [
            {
                "transcript_text": "We discussed pricing and timeline...",
                "sentiment_score": 0.75,
                "call_time": datetime(2025, 12, 20, 14, 0, 0),
                "direction": "inbound"
            }
        ],
        "opportunities": [
            {
                "name": "Q1 2026 Deal",
                "stage": "Negotiation",
                "amount": 50000,
                "close_date": date(2026, 3, 31),
                "probability": 75
            }
        ],
        "activities": [
            {
                "activity_type": "Email",
                "subject": "Follow up",
                "description": "Sent pricing information",
                "activity_date": datetime(2025, 12, 25, 9, 0, 0)
            }
        ]
    }


@pytest.fixture
def sample_email_data() -> List[Dict[str, Any]]:
    """Sample email data for testing."""
    return [
        {
            "message_id": "msg-123",
            "subject": "Budget Discussion",
            "body_text": "We are interested in discussing our 2026 budget...",
            "sent_at": datetime(2025, 12, 15, 10, 30, 0),
            "from_email": "contact@testcorp.com",
            "to_email": "sales@example.com"
        },
        {
            "message_id": "msg-124",
            "subject": "Re: Budget Discussion",
            "body_text": "Thank you for your interest...",
            "sent_at": datetime(2025, 12, 16, 11, 0, 0),
            "from_email": "sales@example.com",
            "to_email": "contact@testcorp.com"
        }
    ]


@pytest.fixture
def sample_salesforce_account() -> Dict[str, Any]:
    """Sample Salesforce account data."""
    return {
        "account_id": "001XX000004ABCD",
        "account_name": "Test Corporation",
        "industry": "Technology",
        "annual_revenue": 1000000,
        "billing_city": "San Francisco",
        "billing_state": "CA",
        "billing_country": "USA",
        "created_date": datetime(2024, 1, 15, 10, 0, 0),
        "last_modified_date": datetime(2025, 12, 20, 14, 0, 0)
    }


@pytest.fixture
def mock_secret_manager():
    """Mock Secret Manager client."""
    with patch('config.config.secretmanager.SecretManagerServiceClient') as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        
        # Mock secret responses
        mock_response = Mock()
        mock_response.payload.data.decode.return_value = "mock-secret-value"
        mock_client.access_secret_version.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def mock_gcp_environment(monkeypatch):
    """Set up mock GCP environment variables."""
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCP_REGION", "us-central1")
    monkeypatch.setenv("BQ_DATASET_NAME", "test_dataset")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")


@pytest.fixture
def sample_scoring_response() -> Dict[str, Any]:
    """Sample LLM scoring response."""
    return {
        "priority_score": 75,
        "budget_likelihood": 60,
        "engagement_score": 80,
        "reasoning": "Account shows moderate engagement with recent email activity.",
        "recommended_action": "Follow up with pricing discussion",
        "key_signals": [
            "Recent email exchange",
            "Budget discussion mentioned",
            "Positive sentiment in calls"
        ]
    }


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    yield
    # Cleanup after test if needed

