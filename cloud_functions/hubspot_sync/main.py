"""
HubSpot Sync Cloud Function
Syncs available sequences metadata from HubSpot
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
from datetime import datetime, timezone
from hubspot import HubSpot

# Import project modules (after path is set)
try:
    from utils.bigquery_client import BigQueryClient
    from utils.logger import setup_logger
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
def hubspot_sync(request):
    """
    Cloud Function entry point for HubSpot sequence sync.
    """
    try:
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # Initialize HubSpot client
        api_client = HubSpot(access_token=settings.hubspot_api_key)
        
        # Sync sequences
        sequences_synced, errors = _sync_sequences(api_client, bq_client)
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if errors == 0 else "partial" if sequences_synced > 0 else "failed"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="hubspot",
            job_type="full",
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=sequences_synced,
            rows_failed=errors,
            status=status
        )
        
        return {
            "status": "success",
            "sequences_synced": sequences_synced,
            "errors": errors
        }, 200
        
    except Exception as e:
        logger.error(f"HubSpot sync failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


def _sync_sequences(api_client: HubSpot, bq_client: BigQueryClient) -> tuple[int, int]:
    """Sync HubSpot sequences to BigQuery."""
    sequences_synced = 0
    errors = 0
    
    try:
        # HubSpot sequences are accessed via Automation API v4
        # Use /automation/v4/workflows endpoint (not /marketing/v3/sequences)
        import requests
        from config.config import settings
        
        url = "https://api.hubapi.com/automation/v4/workflows"
        headers = {
            "Authorization": f"Bearer {settings.hubspot_api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info("Fetching sequences from HubSpot Automation API...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        sequences_data = response.json()
        
        # Parse sequences from response
        # Automation API v4 returns: {"results": [...], "paging": {...}}
        sequences_list = []
        if isinstance(sequences_data, dict):
            # Automation API v4 paginated response format
            if 'results' in sequences_data:
                sequences_list = sequences_data['results']
            # Direct list (fallback)
            elif isinstance(sequences_data.get('data'), list):
                sequences_list = sequences_data['data']
            # Single sequence (fallback)
            elif sequences_data.get('id'):
                sequences_list = [sequences_data]
        elif isinstance(sequences_data, list):
            sequences_list = sequences_data
        
        logger.info(f"Found {len(sequences_list)} sequences in HubSpot")
        
        rows = []
        for sequence in sequences_list:
            try:
                # Automation API v4 workflow format
                # Filter for sequences only (workflow type = "DRIP_DELAY" or "SEQUENCE")
                workflow_type = sequence.get("type", "").upper()
                if workflow_type not in ["DRIP_DELAY", "SEQUENCE"]:
                    # Skip non-sequence workflows
                    continue
                
                row = {
                    "sequence_id": str(sequence.get("id") or sequence.get("workflowId", "")),
                    "sequence_name": sequence.get("name") or sequence.get("workflowName", ""),
                    "is_active": sequence.get("enabled", sequence.get("active", True)),
                    "enrollment_count": sequence.get("contactCount", sequence.get("enrollmentCount", sequence.get("enrolledContacts", 0))),
                    "last_synced": datetime.now(timezone.utc).isoformat()
                }
                # Only add if we have at least an ID
                if row["sequence_id"]:
                    rows.append(row)
            except Exception as e:
                logger.error(f"Error transforming sequence {sequence.get('id', 'unknown')}: {e}")
                errors += 1
        
        if rows:
            try:
                bq_client.insert_rows("hubspot_sequences", rows)
                sequences_synced = len(rows)
                logger.info(f"Successfully inserted {sequences_synced} sequences into BigQuery")
            except Exception as e:
                logger.error(f"Error inserting sequences: {e}")
                errors += len(rows)
        else:
            logger.warning("No sequences to insert (empty or invalid data)")
        
        return sequences_synced, errors
        
    except Exception as e:
        logger.error(f"Error fetching sequences from HubSpot: {e}", exc_info=True)
        return sequences_synced, errors + 1

