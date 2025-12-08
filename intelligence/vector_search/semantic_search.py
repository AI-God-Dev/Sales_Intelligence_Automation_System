"""
BigQuery Vector Search for semantic queries.
Enables finding accounts/emails by intent using cosine similarity.
Uses unified AI abstraction layer for provider-agnostic embedding generation.
"""
import logging
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings
from ai.semantic_search import get_semantic_search_provider, SemanticSearchProvider

logger = setup_logger(__name__)


class SemanticSearch:
    """Semantic search using BigQuery Vector Search with cosine similarity."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None, semantic_search_provider: Optional[SemanticSearchProvider] = None):
        self.bq_client = bq_client or BigQueryClient()
        # Use provided provider or get from factory (respects MOCK_MODE/LOCAL_MODE)
        self.search_provider = semantic_search_provider or get_semantic_search_provider(bq_client=self.bq_client)
        # Expose embedding_provider for backward compatibility
        self.embedding_provider = self.search_provider.embedding_provider
    
    def generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for search query using unified abstraction."""
        return self.search_provider.embedding_provider.generate_embedding(query_text)
    
    def search_emails_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search emails by semantic intent using unified abstraction."""
        return self.search_provider.search_emails_by_intent(query_text, limit, days_back, min_similarity)
    
    def search_calls_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search call transcripts by semantic intent using unified abstraction."""
        return self.search_provider.search_calls_by_intent(query_text, limit, days_back, min_similarity)
    
    def search_accounts_by_intent(
        self,
        query_text: str,
        limit: int = 20,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Find accounts based on semantic intent from their communications.
        
        Args:
            query_text: Natural language query (e.g., "accounts discussing budget")
            limit: Maximum number of accounts
            days_back: How many days back to search communications
        
        Returns:
            List of accounts with relevance scores
        """
        # Use search provider methods
        email_results = self.search_emails_by_intent(query_text, limit=100, days_back=days_back)
        call_results = self.search_calls_by_intent(query_text, limit=100, days_back=days_back)
        
        # Aggregate by account
        account_scores = {}
        
        for email in email_results:
            account_id = email.get('sf_account_id')
            if account_id:
                if account_id not in account_scores:
                    account_scores[account_id] = {
                        'account_id': account_id,
                        'account_name': email.get('account_name'),
                        'max_similarity': email.get('similarity', 0),
                        'email_count': 0,
                        'call_count': 0
                    }
                account_scores[account_id]['max_similarity'] = max(
                    account_scores[account_id]['max_similarity'],
                    email.get('similarity', 0)
                )
                account_scores[account_id]['email_count'] += 1
        
        for call in call_results:
            account_id = call.get('matched_account_id')
            if account_id:
                if account_id not in account_scores:
                    account_scores[account_id] = {
                        'account_id': account_id,
                        'account_name': call.get('account_name'),
                        'max_similarity': call.get('similarity', 0),
                        'email_count': 0,
                        'call_count': 0
                    }
                account_scores[account_id]['max_similarity'] = max(
                    account_scores[account_id]['max_similarity'],
                    call.get('similarity', 0)
                )
                account_scores[account_id]['call_count'] += 1
        
        # Sort by similarity and return top results
        sorted_accounts = sorted(
            account_scores.values(),
            key=lambda x: x['max_similarity'],
            reverse=True
        )
        
        return sorted_accounts[:limit]

