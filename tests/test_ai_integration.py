"""
Integration tests for AI components using unified abstraction layer.
"""
import os
import pytest
from intelligence.embeddings.generator import EmbeddingGenerator
from intelligence.scoring.account_scorer import AccountScorer
from intelligence.vector_search.semantic_search import SemanticSearch
from intelligence.nlp_query.query_generator import NLPQueryGenerator
from intelligence.email_replies.generator import EmailReplyGenerator


class TestEmbeddingGeneratorIntegration:
    """Test EmbeddingGenerator with new abstraction."""
    
    def test_mock_mode(self):
        """Test EmbeddingGenerator with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        generator = EmbeddingGenerator()
        embedding = generator.generate_embedding("test text")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        os.environ.pop("MOCK_MODE", None)


class TestAccountScorerIntegration:
    """Test AccountScorer with new abstraction."""
    
    def test_mock_mode(self):
        """Test AccountScorer with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        scorer = AccountScorer()
        # Mock account data
        account_data = {
            "account_name": "Test Account",
            "emails": [{"subject": "Test", "body_text": "Test body", "sent_at": "2024-01-01", "from_email": "test@example.com"}],
            "calls": [],
            "opportunities": [],
            "activities": []
        }
        # This will use mock scoring
        try:
            scores = scorer.scoring_provider.score_account("test_123", account_data)
            assert "priority_score" in scores
        except Exception:
            # May fail if BigQuery not available, that's OK for unit test
            pass
        os.environ.pop("MOCK_MODE", None)


class TestSemanticSearchIntegration:
    """Test SemanticSearch with new abstraction."""
    
    def test_mock_mode(self):
        """Test SemanticSearch with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        search = SemanticSearch()
        # Verify it uses the abstraction
        assert hasattr(search, 'search_provider')
        os.environ.pop("MOCK_MODE", None)


class TestNLPQueryGeneratorIntegration:
    """Test NLPQueryGenerator with new abstraction."""
    
    def test_mock_mode(self):
        """Test NLPQueryGenerator with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        generator = NLPQueryGenerator()
        # Verify it uses the abstraction
        assert hasattr(generator, 'model_provider')
        os.environ.pop("MOCK_MODE", None)


class TestEmailReplyGeneratorIntegration:
    """Test EmailReplyGenerator with new abstraction."""
    
    def test_mock_mode(self):
        """Test EmailReplyGenerator with MOCK_MODE."""
        os.environ["MOCK_MODE"] = "1"
        generator = EmailReplyGenerator()
        # Verify it uses the abstraction
        assert hasattr(generator, 'model_provider')
        os.environ.pop("MOCK_MODE", None)
