"""
Embedding generation pipeline for emails and call transcripts.
Supports OpenAI and Vertex AI embedding models.
"""
import logging
from typing import List, Optional
from google.cloud import bigquery
from google.cloud import aiplatform
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

# Conditional imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text content using OpenAI or Vertex AI."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        self.embedding_model = settings.embedding_model
        
        # Determine embedding provider (can be different from LLM provider)
        embedding_provider = getattr(settings, 'embedding_provider', 'vertex_ai')
        
        if embedding_provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Install with: pip install openai")
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured. Set 'openai-api-key' secret or use vertex_ai provider.")
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.embedding_provider = "openai"
        elif embedding_provider == "vertex_ai":
            try:
                aiplatform.init(project=settings.gcp_project_id, location=settings.gcp_region)
                self.client = None
                self.embedding_provider = "vertex_ai"
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise ValueError(f"Vertex AI initialization failed: {e}. Ensure Vertex AI API is enabled.")
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}. Use 'vertex_ai' or 'openai'.")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        if not text or not text.strip():
            return []
        
        try:
            if self.embedding_provider == "openai":
                # OpenAI embedding
                if not self.client:
                    raise ValueError("OpenAI client not initialized")
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text[:8000]  # Limit text length
                )
                return response.data[0].embedding
            else:
                # Vertex AI embedding
                from vertexai.language_models import TextEmbeddingModel
                model = TextEmbeddingModel.from_pretrained(self.embedding_model)
                embeddings = model.get_embeddings([text[:8000]])
                # Handle different response formats
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
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return []
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                if self.embedding_provider == "openai":
                    # OpenAI batch embedding
                    if not self.client:
                        raise ValueError("OpenAI client not initialized")
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=[t[:8000] for t in batch]
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                else:
                    # Vertex AI batch embedding
                    from vertexai.language_models import TextEmbeddingModel
                    model = TextEmbeddingModel.from_pretrained(self.embedding_model)
                    embeddings = model.get_embeddings([t[:8000] for t in batch])
                    # Handle different response formats
                    batch_embeddings = []
                    for emb in embeddings:
                        if hasattr(emb, 'values'):
                            batch_embeddings.append(emb.values)
                        elif isinstance(emb, list):
                            batch_embeddings.append(emb)
                        else:
                            batch_embeddings.append(list(emb))
                
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
                # Add empty embeddings for failed batch
                all_embeddings.extend([[]] * len(batch))
        
        return all_embeddings
    
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

