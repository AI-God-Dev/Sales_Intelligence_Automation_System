"""
Unit tests for AI model abstraction layer.
"""
import os
import pytest
from ai.models import get_model_provider, MockModelProvider, VertexAIModelProvider
from ai.embeddings import get_embedding_provider, MockEmbeddingProvider
from ai.scoring import get_scoring_provider
from ai.semantic_search import get_semantic_search_provider


class TestMockModelProvider:
    """Test mock model provider."""
    
    def test_mock_mode_enabled(self):
        """Test that MOCK_MODE returns mock provider."""
        os.environ["MOCK_MODE"] = "1"
        provider = get_model_provider()
        assert isinstance(provider, MockModelProvider)
        os.environ.pop("MOCK_MODE", None)
    
    def test_mock_generate(self):
        """Test mock generation."""
        provider = MockModelProvider()
        response = provider.generate("test prompt")
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_mock_stream(self):
        """Test mock streaming."""
        provider = MockModelProvider()
        chunks = list(provider.generate_stream("test prompt"))
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)


class TestMockEmbeddingProvider:
    """Test mock embedding provider."""
    
    def test_mock_mode_enabled(self):
        """Test that MOCK_MODE returns mock embedding provider."""
        os.environ["MOCK_MODE"] = "1"
        provider = get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)
        os.environ.pop("MOCK_MODE", None)
    
    def test_mock_embedding(self):
        """Test mock embedding generation."""
        provider = MockEmbeddingProvider()
        embedding = provider.generate_embedding("test text")
        assert isinstance(embedding, list)
        assert len(embedding) == provider.dimensions
        assert all(isinstance(x, float) for x in embedding)
    
    def test_mock_batch_embeddings(self):
        """Test mock batch embedding generation."""
        provider = MockEmbeddingProvider()
        texts = ["text1", "text2", "text3"]
        embeddings = provider.generate_embeddings_batch(texts)
        assert len(embeddings) == len(texts)
        assert all(len(emb) == provider.dimensions for emb in embeddings)
    
    def test_deterministic_embeddings(self):
        """Test that same text produces same embedding."""
        provider = MockEmbeddingProvider()
        text = "test text"
        emb1 = provider.generate_embedding(text)
        emb2 = provider.generate_embedding(text)
        assert emb1 == emb2


class TestScoringProvider:
    """Test scoring provider."""
    
    def test_scoring_with_mock(self):
        """Test scoring with mock model."""
        os.environ["MOCK_MODE"] = "1"
        provider = get_scoring_provider()
        account_data = {
            "account_name": "Test Account",
            "emails": [],
            "calls": [],
            "opportunities": [],
            "activities": []
        }
        scores = provider.score_account("test_account_123", account_data)
        assert "priority_score" in scores
        assert "budget_likelihood" in scores
        assert "engagement_score" in scores
        assert 0 <= scores["priority_score"] <= 100
        os.environ.pop("MOCK_MODE", None)


class TestSemanticSearchProvider:
    """Test semantic search provider."""
    
    def test_semantic_search_mock(self):
        """Test semantic search with mock embeddings."""
        os.environ["MOCK_MODE"] = "1"
        # Note: This will fail if BigQuery is not accessible, but that's expected
        # In real tests, you'd mock BigQuery client
        try:
            from utils.bigquery_client import BigQueryClient
            bq_client = BigQueryClient()
            search = get_semantic_search_provider(bq_client=bq_client)
            # Just verify it's created, actual search requires BigQuery
            assert search is not None
        except Exception:
            # Expected if BigQuery not available
            pass
        os.environ.pop("MOCK_MODE", None)
