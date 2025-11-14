"""
Entity Resolution Cloud Function
Batch processes entity resolution for emails and calls
"""
import functions_framework
import logging
from typing import Dict, Any
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from utils.monitoring import publish_error_notification, PerformanceMonitor
from entity_resolution.matcher import EntityMatcher
from config.config import settings

logger = setup_logger(__name__)


@functions_framework.http
def entity_resolution(request):
    """
    Cloud Function entry point for entity resolution.
    
    Expected request parameters:
    - batch_size: Number of records to process (default: 1000)
    - entity_type: 'email' or 'phone' or 'all' (default: 'all')
    """
    try:
        request_json = request.get_json(silent=True) or {}
        batch_size = request_json.get("batch_size", 1000)
        entity_type = request_json.get("entity_type", "all")
        
        bq_client = BigQueryClient()
        matcher = EntityMatcher(bq_client)
        
        results = {}
        
        with PerformanceMonitor("entity_resolution"):
            if entity_type in ["email", "all"]:
                logger.info(f"Processing email entity resolution (batch_size: {batch_size})")
                email_stats = matcher.update_participant_matches(batch_size)
                results["email"] = email_stats
            
            if entity_type in ["phone", "all"]:
                logger.info(f"Processing phone entity resolution (batch_size: {batch_size})")
                phone_stats = matcher.update_call_matches(batch_size)
                results["phone"] = phone_stats
        
        return {
            "status": "success",
            "results": results
        }, 200
        
    except Exception as e:
        logger.error(f"Entity resolution failed: {str(e)}", exc_info=True)
        publish_error_notification(
            source_system="entity_resolution",
            error=str(e),
            entity_type=request_json.get("entity_type", "unknown")
        )
        return {"error": str(e)}, 500

