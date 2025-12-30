"""
Unit tests for model provider.
"""
import pytest
from unittest.mock import Mock, patch
from ai.models import VertexAIModelProvider, get_model_provider
import os


class TestVertexAIModelProvider:
    """Test VertexAIModelProvider."""
    
    def test_init_with_env_vars(self, monkeypatch):
        """Test initialization with environment variables."""
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("GCP_REGION", "us-central1")
        monkeypatch.setenv("LLM_MODEL", "gemini-2.5-pro")
        
        with patch('ai.models.vertexai') as mock_vertexai:
            provider = VertexAIModelProvider()
            
            assert provider.project_id == "test-project"
            assert provider.region == "us-central1"
            assert provider.model_name == "gemini-2.5-pro"
    
    def test_generate_with_json_output(self, mock_vertex_ai_provider):
        """Test generate with JSON output."""
        result = mock_vertex_ai_provider.generate(
            "Test prompt",
            want_json=True,
            temperature=0.2
        )
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_model_provider_default(self, monkeypatch):
        """Test get_model_provider returns default."""
        monkeypatch.setenv("LLM_PROVIDER", "vertex_ai")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        
        with patch('ai.models.VertexAIModelProvider') as mock_provider_class:
            mock_provider = Mock()
            mock_provider_class.return_value = mock_provider
            
            provider = get_model_provider()
            
            assert provider is not None

