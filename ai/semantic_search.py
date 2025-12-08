"""
Unified Semantic Search Provider
Provides semantic search capabilities using embeddings and vector similarity.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from ai.embeddings import get_embedding_provider, EmbeddingProvider
from utils.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SemanticSearchProvider(ABC):
    """Abstract base class for semantic search providers."""
    
    @abstractmethod
    def search_emails_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search emails by semantic intent."""
        pass
    
    @abstractmethod
    def search_calls_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search calls by semantic intent."""
        pass


class BigQuerySemanticSearchProvider(SemanticSearchProvider):
    """BigQuery-based semantic search using vector similarity."""
    
    def __init__(
        self,
        bq_client: Optional[BigQueryClient] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.bq_client = bq_client or BigQueryClient()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        # Store project_id and dataset_id for convenience
        self.project_id = self.bq_client.project_id
        self.dataset_id = self.bq_client.dataset_id
    
    def search_emails_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search emails using BigQuery vector search."""
        # Generate query embedding
        query_embedding = self.embedding_provider.generate_embedding(query_text)
        
        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []
        
        # Build BigQuery vector search query using COSINE_DISTANCE
        query = f"""
        WITH query_embedding AS (
          SELECT @query_embedding AS embedding
        )
        SELECT 
          m.message_id,
          m.thread_id,
          m.subject,
          m.body_text,
          m.from_email,
          m.sent_at,
          m.mailbox_email,
          p.sf_account_id,
          a.account_name,
          (1 - COSINE_DISTANCE(m.embedding, query_embedding.embedding)) AS similarity
        FROM `{self.project_id}.{self.dataset_id}.gmail_messages` m
        CROSS JOIN query_embedding
        LEFT JOIN `{self.project_id}.{self.dataset_id}.gmail_participants` p
            ON m.message_id = p.message_id AND p.role = 'from'
        LEFT JOIN `{self.project_id}.{self.dataset_id}.sf_accounts` a
            ON p.sf_account_id = a.account_id
        WHERE m.embedding IS NOT NULL
          AND ARRAY_LENGTH(m.embedding) > 0
          AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
          AND (1 - COSINE_DISTANCE(m.embedding, query_embedding.embedding)) >= @min_similarity
        ORDER BY similarity DESC
        LIMIT @limit
        """
        
        try:
            from google.cloud import bigquery
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
                    bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
                    bigquery.ScalarQueryParameter("min_similarity", "FLOAT64", min_similarity),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            results = self.bq_client.query(query, job_config=job_config)
            return list(results) if results else []
        except Exception as e:
            logger.error(f"Error in semantic search: {e}", exc_info=True)
            return []
    
    def search_calls_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search calls using BigQuery vector search."""
        # Generate query embedding
        query_embedding = self.embedding_provider.generate_embedding(query_text)
        
        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []
        
        # Build BigQuery vector search query using COSINE_DISTANCE
        query = f"""
        WITH query_embedding AS (
          SELECT @query_embedding AS embedding
        )
        SELECT 
          c.call_id,
          c.transcript_text,
          c.from_number,
          c.to_number,
          c.call_time,
          c.direction,
          c.sentiment_score,
          c.matched_account_id,
          a.account_name,
          (1 - COSINE_DISTANCE(c.embedding, query_embedding.embedding)) AS similarity
        FROM `{self.project_id}.{self.dataset_id}.dialpad_calls` c
        CROSS JOIN query_embedding
        LEFT JOIN `{self.project_id}.{self.dataset_id}.sf_accounts` a
            ON c.matched_account_id = a.account_id
        WHERE c.embedding IS NOT NULL
          AND ARRAY_LENGTH(c.embedding) > 0
          AND c.call_time >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
          AND (1 - COSINE_DISTANCE(c.embedding, query_embedding.embedding)) >= @min_similarity
        ORDER BY similarity DESC
        LIMIT @limit
        """
        
        try:
            from google.cloud import bigquery
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
                    bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
                    bigquery.ScalarQueryParameter("min_similarity", "FLOAT64", min_similarity),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            results = self.bq_client.query(query, job_config=job_config)
            return list(results) if results else []
        except Exception as e:
            logger.error(f"Error in semantic search: {e}", exc_info=True)
            return []


def get_semantic_search_provider(
    bq_client: Optional[BigQueryClient] = None,
    embedding_provider: Optional[EmbeddingProvider] = None
) -> SemanticSearchProvider:
    """Factory function to get semantic search provider."""
    return BigQuerySemanticSearchProvider(bq_client, embedding_provider)
