"""
Cloud Function for embedding generation.
Runs incrementally to generate embeddings for new emails and calls.
"""
import functions_framework
import logging
from datetime import datetime, timezone
from intelligence.embeddings.generator import EmbeddingGenerator
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

logger = setup_logger(__name__)


@functions_framework.http
def generate_embeddings(request):
    """
    HTTP Cloud Function for embedding generation.
    
    Expected request body (optional):
    {
        "type": "emails" | "calls" | "both" (default: "both"),
        "limit": 1000 (optional, default: None = all)
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        embedding_type = request_json.get("type", "both")
        limit = request_json.get("limit")
        
        started_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"Starting embedding generation (type: {embedding_type}, limit: {limit})")
        
        bq_client = BigQueryClient()
        generator = EmbeddingGenerator(bq_client)
        
        total_updated = 0
        
        if embedding_type in ["emails", "both"]:
            email_count = generator.update_email_embeddings(limit=limit)
            total_updated += email_count
            logger.info(f"Updated {email_count} email embeddings")
        
        if embedding_type in ["calls", "both"]:
            call_count = generator.update_call_embeddings(limit=limit)
            total_updated += call_count
            logger.info(f"Updated {call_count} call embeddings")
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if total_updated > 0 else "no_updates"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="embeddings",
            job_type="incremental",
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=total_updated,
            rows_failed=0,
            status=status
        )
        
        return {
            "status": "success",
            "embeddings_updated": total_updated,
            "email_count": email_count if embedding_type in ["emails", "both"] else 0,
            "call_count": call_count if embedding_type in ["calls", "both"] else 0,
            "completed_at": completed_at
        }, 200
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

