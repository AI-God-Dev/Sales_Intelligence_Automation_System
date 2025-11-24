"""
BigQuery Vector Search for semantic queries.
Enables finding accounts/emails by intent using cosine similarity.
"""
import logging
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from google.cloud import aiplatform
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

# Conditional imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = setup_logger(__name__)


class SemanticSearch:
    """Semantic search using BigQuery Vector Search with cosine similarity."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        self.embedding_provider = getattr(settings, 'embedding_provider', 'vertex_ai')
        self.embedding_model = settings.embedding_model
        
        # Initialize embedding generator
        if self.embedding_provider == "vertex_ai":
            try:
                aiplatform.init(project=settings.gcp_project_id, location=settings.gcp_region)
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise
    
    def generate_query_embedding(self, query_text: str) -> List[float]:
        """Generate embedding for search query."""
        try:
            if self.embedding_provider == "openai":
                import openai
                client = openai.OpenAI(api_key=settings.openai_api_key)
                response = client.embeddings.create(
                    model=self.embedding_model,
                    input=query_text[:8000]
                )
                return response.data[0].embedding
            else:
                # Vertex AI
                from vertexai.language_models import TextEmbeddingModel
                model = TextEmbeddingModel.from_pretrained(self.embedding_model)
                embeddings = model.get_embeddings([query_text[:8000]])
                if embeddings and len(embeddings) > 0:
                    emb = embeddings[0]
                    if hasattr(emb, 'values'):
                        return emb.values
                    elif isinstance(emb, list):
                        return emb
                    else:
                        return list(emb)
                return []
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}", exc_info=True)
            return []
    
    def search_emails_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search emails by semantic intent using vector similarity.
        
        Args:
            query_text: Natural language query (e.g., "budget discussions for 2026")
            limit: Maximum number of results
            days_back: How many days back to search
            min_similarity: Minimum cosine similarity threshold (0-1)
        
        Returns:
            List of matching emails with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.generate_query_embedding(query_text)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Build BigQuery SQL with cosine similarity
        # BigQuery Vector Search uses COSINE_DISTANCE function
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
            -- Calculate cosine similarity (1 - cosine distance)
            (1 - COSINE_DISTANCE(m.embedding, query_embedding.embedding)) AS similarity
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages` m
        CROSS JOIN query_embedding
        LEFT JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants` p
            ON m.message_id = p.message_id AND p.role = 'from'
        LEFT JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts` a
            ON p.sf_account_id = a.account_id
        WHERE m.embedding IS NOT NULL
            AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
            AND (1 - COSINE_DISTANCE(m.embedding, query_embedding.embedding)) >= @min_similarity
        ORDER BY similarity DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
                bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
                bigquery.ScalarQueryParameter("min_similarity", "FLOAT64", min_similarity),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config)
            logger.info(f"Found {len(results)} emails matching query: {query_text}")
            return results
        except Exception as e:
            logger.error(f"Error searching emails: {e}", exc_info=True)
            return []
    
    def search_calls_by_intent(
        self,
        query_text: str,
        limit: int = 50,
        days_back: int = 60,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search call transcripts by semantic intent.
        
        Args:
            query_text: Natural language query
            limit: Maximum number of results
            days_back: How many days back to search
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            List of matching calls with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.generate_query_embedding(query_text)
        if not query_embedding:
            return []
        
        query = f"""
        WITH query_embedding AS (
            SELECT @query_embedding AS embedding
        )
        SELECT 
            c.call_id,
            c.direction,
            c.from_number,
            c.to_number,
            c.transcript_text,
            c.call_time,
            c.sentiment_score,
            c.matched_account_id,
            a.account_name,
            (1 - COSINE_DISTANCE(c.embedding, query_embedding.embedding)) AS similarity
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls` c
        CROSS JOIN query_embedding
        LEFT JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts` a
            ON c.matched_account_id = a.account_id
        WHERE c.embedding IS NOT NULL
            AND c.call_time >= DATE_SUB(CURRENT_DATE(), INTERVAL @days_back DAY)
            AND (1 - COSINE_DISTANCE(c.embedding, query_embedding.embedding)) >= @min_similarity
        ORDER BY similarity DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
                bigquery.ScalarQueryParameter("days_back", "INT64", days_back),
                bigquery.ScalarQueryParameter("min_similarity", "FLOAT64", min_similarity),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config)
            logger.info(f"Found {len(results)} calls matching query: {query_text}")
            return results
        except Exception as e:
            logger.error(f"Error searching calls: {e}", exc_info=True)
            return []
    
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
        # Search both emails and calls
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

