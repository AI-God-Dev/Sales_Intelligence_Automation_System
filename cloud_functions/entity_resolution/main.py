"""
Entity Resolution Cloud Function
Batch processes entity resolution for emails and calls
"""
import sys
import os
from pathlib import Path

# Add project root to Python path for imports
_project_root = None
_possible_roots = [
    Path(__file__).parent.parent.parent,
    Path.cwd(),
    Path('/workspace'),
    Path('/var/task'),
]

for root in _possible_roots:
    if root.exists() and (root / 'utils').exists() and (root / 'config').exists():
        _project_root = root
        break

if _project_root and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
elif not _project_root:
    _project_root = Path(__file__).parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

# Initialize basic logging first
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import functions_framework
from typing import Dict, Any

# Import project modules (after path is set)
try:
    from utils.bigquery_client import BigQueryClient
    from utils.logger import setup_logger
    from utils.monitoring import publish_error_notification, PerformanceMonitor
    from entity_resolution.matcher import EntityMatcher
    from config.config import settings
    logger = setup_logger(__name__)
    logger.info("Successfully imported all required modules")
except ImportError as e:
    logger.error(f"Import error: {e}", exc_info=True)
    raise ImportError(
        f"Failed to import required modules. Error: {e}. "
        f"Python path: {sys.path}. Project root: {_project_root}."
    ) from e


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

