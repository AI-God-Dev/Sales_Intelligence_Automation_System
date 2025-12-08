"""
Embedding generation pipeline for emails and call transcripts.
Uses unified AI abstraction layer for provider-agnostic embedding generation.
"""
import logging
from typing import List, Optional
from google.cloud import bigquery
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings
from ai.embeddings import get_embedding_provider, EmbeddingProvider

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text content using unified AI abstraction layer."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None, embedding_provider: Optional[EmbeddingProvider] = None):
        self.bq_client = bq_client or BigQueryClient()
        # Use provided provider or get from factory (respects MOCK_MODE/LOCAL_MODE)
        # Vertex AI uses Application Default Credentials - no API key needed
        self.embedding_provider = embedding_provider or get_embedding_provider(
            provider=settings.embedding_provider,
            project_id=settings.gcp_project_id,
            region=settings.gcp_region,
            model_name=settings.embedding_model
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        return self.embedding_provider.generate_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        return self.embedding_provider.generate_embeddings_batch(texts, batch_size=batch_size)
    
    def update_email_embeddings(self, limit: Optional[int] = None):
        """Generate embeddings for emails that don't have them yet."""
        query = f"""
        SELECT message_id, body_text, subject
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages`
        WHERE embedding IS NULL
          AND body_text IS NOT NULL
          AND body_text != ''
        ORDER BY sent_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        logger.info(f"Fetching emails without embeddings (limit: {limit})")
        rows = self.bq_client.query(query)
        
        if not rows:
            logger.info("No emails found without embeddings")
            return 0
        
        texts = []
        message_ids = []
        
        for row in rows:
            # Combine subject and body for better semantic meaning
            text = f"Subject: {row.get('subject', '')}\n\n{row.get('body_text', '')}"
            texts.append(text)
            message_ids.append(row['message_id'])
        
        logger.info(f"Generating embeddings for {len(texts)} emails")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Update BigQuery with embeddings
        updates = []
        for msg_id, embedding in zip(message_ids, embeddings):
            if embedding:
                updates.append({
                    "message_id": msg_id,
                    "embedding": embedding
                })
        
        if updates:
            # Batch update embeddings
            update_query = f"""
            UPDATE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages` m
            SET embedding = @embedding
            WHERE message_id = @message_id
            """
            
            for update in updates:
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("message_id", "STRING", update["message_id"]),
                        bigquery.ArrayQueryParameter("embedding", "FLOAT64", update["embedding"])
                    ]
                )
                self.bq_client.client.query(update_query, job_config=job_config).result()
        
        logger.info(f"Updated embeddings for {len(updates)} emails")
        return len(updates)
    
    def update_call_embeddings(self, limit: Optional[int] = None):
        """Generate embeddings for call transcripts that don't have them yet."""
        query = f"""
        SELECT call_id, transcript_text
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls`
        WHERE embedding IS NULL
          AND transcript_text IS NOT NULL
          AND transcript_text != ''
        ORDER BY call_time DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        logger.info(f"Fetching calls without embeddings (limit: {limit})")
        rows = self.bq_client.query(query)
        
        if not rows:
            logger.info("No calls found without embeddings")
            return 0
        
        texts = [row['transcript_text'] for row in rows]
        call_ids = [row['call_id'] for row in rows]
        
        logger.info(f"Generating embeddings for {len(texts)} calls")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Update BigQuery with embeddings
        updates = []
        for call_id, embedding in zip(call_ids, embeddings):
            if embedding:
                updates.append({
                    "call_id": call_id,
                    "embedding": embedding
                })
        
        if updates:
            # Batch update embeddings
            update_query = f"""
            UPDATE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls` c
            SET embedding = @embedding
            WHERE call_id = @call_id
            """
            
            for update in updates:
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("call_id", "STRING", update["call_id"]),
                        bigquery.ArrayQueryParameter("embedding", "FLOAT64", update["embedding"])
                    ]
                )
                self.bq_client.client.query(update_query, job_config=job_config).result()
        
        logger.info(f"Updated embeddings for {len(updates)} calls")
        return len(updates)
    
    def process_incremental_updates(self):
        """Process new emails and calls that need embeddings."""
        email_count = self.update_email_embeddings(limit=1000)
        call_count = self.update_call_embeddings(limit=500)
        return email_count + call_count

