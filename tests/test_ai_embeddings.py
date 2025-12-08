"""
Unit tests for AI embedding abstraction layer.
"""
import os
import pytest
from ai.embeddings import get_embedding_provider, MockEmbeddingProvider, LocalEmbeddingProvider


class TestEmbeddingProviders:
    """Test embedding providers."""
    
    def test_mock_provider(self):
        """Test mock embedding provider."""
        provider = MockEmbeddingProvider()
        embedding = provider.generate_embedding("test")
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
    
    def test_local_provider(self):
        """Test local embedding provider."""
        provider = LocalEmbeddingProvider()
        embedding = provider.generate_embedding("test")
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
    
    def test_batch_generation(self):
        """Test batch embedding generation."""
        provider = MockEmbeddingProvider()
        texts = ["text1", "text2", "text3"]
        embeddings = provider.generate_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
    
    def test_empty_text(self):
        """Test handling of empty text."""
        provider = MockEmbeddingProvider()
        embedding = provider.generate_embedding("")
        assert len(embedding) == 768
        assert all(x == 0.0 for x in embedding)
    
    def test_factory_mock_mode(self):
        """Test factory function with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        provider = get_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)
        os.environ.pop("MOCK_MODE", None)
    
    def test_factory_local_mode(self):
        """Test factory function with LOCAL_MODE."""
        os.environ["LOCAL_MODE"] = "1"
        provider = get_embedding_provider()
        assert isinstance(provider, LocalEmbeddingProvider)
        os.environ.pop("LOCAL_MODE", None)
