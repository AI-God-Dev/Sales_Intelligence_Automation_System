"""
Unit tests for scoring provider.
"""
import pytest
from unittest.mock import Mock, patch
from ai.scoring import VertexAIScoringProvider, get_scoring_provider
from datetime import date, datetime


class TestVertexAIScoringProvider:
    """Test VertexAIScoringProvider."""
    
    def test_score_account_basic(self, mock_vertex_ai_provider, sample_account_data):
        """Test basic account scoring."""
        provider = VertexAIScoringProvider(model_provider=mock_vertex_ai_provider)
        
        result = provider.score_account("test-123", sample_account_data)
        
        assert "priority_score" in result
        assert "account_id" in result
        assert result["account_id"] == "test-123"
        assert isinstance(result["priority_score"], int)
    
    def test_score_account_with_date_serialization(self, mock_vertex_ai_provider):
        """Test that date objects are properly serialized."""
        account_data = {
            "account_id": "test-123",
            "last_interaction": date(2025, 12, 20),
            "emails": [{
                "sent_at": datetime(2025, 12, 15, 10, 30, 0)
            }]
        }
        
        provider = VertexAIScoringProvider(model_provider=mock_vertex_ai_provider)
        
        # Should not raise TypeError
        result = provider.score_account("test-123", account_data)
        assert result is not None
    
    def test_build_prompt_includes_account_data(self, mock_vertex_ai_provider, sample_account_data):
        """Test that prompt includes account data."""
        provider = VertexAIScoringProvider(model_provider=mock_vertex_ai_provider)
        
        prompt = provider._build_prompt("test-123", sample_account_data)
        
        assert "test-123" in prompt
        assert "account_data" in prompt.lower()
    
    def test_get_scoring_provider_default(self):
        """Test get_scoring_provider returns default provider."""
        with patch('ai.scoring.get_model_provider') as mock_get_model:
            mock_model = Mock()
            mock_get_model.return_value = mock_model
            
            provider = get_scoring_provider()
            
            assert provider is not None
            assert hasattr(provider, 'score_account')

