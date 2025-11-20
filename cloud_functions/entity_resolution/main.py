"""
Entity Resolution Cloud Function
Batch processes entity resolution for emails and calls
"""
import sys
import os
from pathlib import Path

# Add project root to Python path for imports
# This ensures utils, config, and entity_resolution modules are found
# Try multiple path resolution strategies for different deployment environments
_project_root = None
_possible_roots = [
    Path(__file__).parent.parent.parent,  # From cloud_functions/entity_resolution/main.py -> project root
    Path.cwd(),  # Current working directory
    Path('/workspace'),  # Cloud Functions Gen2 default workspace
    Path('/var/task'),  # Alternative Cloud Functions path
]

for root in _possible_roots:
    if root.exists() and (root / 'utils').exists() and (root / 'config').exists():
        _project_root = root
        break

if _project_root and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
elif not _project_root:
    # Fallback: add current file's parent's parent's parent to path
    _project_root = Path(__file__).parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

# Initialize basic logging first (before any other imports that might fail)
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log path information for debugging
logger.info(f"Python path: {sys.path}")
logger.info(f"Project root: {_project_root}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"__file__ location: {__file__}")

# Verify directory structure exists
if _project_root and _project_root.exists():
    logger.info(f"Project root exists: {_project_root}")
    logger.info(f"Utils directory exists: {(_project_root / 'utils').exists()}")
    logger.info(f"Config directory exists: {(_project_root / 'config').exists()}")
    logger.info(f"Entity resolution directory exists: {(_project_root / 'entity_resolution').exists()}")
    if (_project_root / 'utils').exists():
        logger.info(f"Utils contents: {list((_project_root / 'utils').iterdir())}")
    if (_project_root / 'config').exists():
        logger.info(f"Config contents: {list((_project_root / 'config').iterdir())}")
    if (_project_root / 'entity_resolution').exists():
        logger.info(f"Entity resolution contents: {list((_project_root / 'entity_resolution').iterdir())}")
else:
    logger.warning(f"Project root does not exist or is None: {_project_root}")

import functions_framework
from typing import Dict, Any

# Now import project modules (after path is set)
# These imports are critical - if they fail, we can't proceed
try:
    logger.info("Attempting to import utils.bigquery_client...")
    from utils.bigquery_client import BigQueryClient
    logger.info("Successfully imported BigQueryClient")
    
    logger.info("Attempting to import utils.logger...")
    from utils.logger import setup_logger
    logger.info("Successfully imported setup_logger")
    
    logger.info("Attempting to import utils.monitoring...")
    from utils.monitoring import publish_error_notification, PerformanceMonitor
    logger.info("Successfully imported monitoring functions")
    
    logger.info("Attempting to import entity_resolution.matcher...")
    from entity_resolution.matcher import EntityMatcher
    logger.info("Successfully imported EntityMatcher")
    
    logger.info("Attempting to import config.config...")
    from config.config import settings
    logger.info("Successfully imported settings")
    
    # Reinitialize logger with proper setup after imports succeed
    logger = setup_logger(__name__)
    logger.info("Successfully imported all required modules")
except ImportError as e:
    # Log import errors with full details
    logger.error(f"Import error during module load: {e}", exc_info=True)
    logger.error(f"Python path: {sys.path}")
    logger.error(f"Project root: {_project_root}")
    logger.error(f"Current working directory: {os.getcwd()}")
    if _project_root and _project_root.exists():
        logger.error(f"Project root contents: {list(_project_root.iterdir())}")
    raise ImportError(
        f"Failed to import required modules for entity resolution. "
        f"Error: {e}. Python path: {sys.path}. "
        f"Project root: {_project_root}. "
        f"Current working directory: {os.getcwd()}. "
        f"Check that all required modules (utils, config, entity_resolution) are available."
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

