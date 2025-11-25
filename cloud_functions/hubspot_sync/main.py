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
        import requests
        from config.config import settings
        
        # Try multiple endpoints - HubSpot has different APIs for different subscription levels
        endpoints_to_try = [
            ("/automation/v4/workflows", "Automation API v4"),
            ("/marketing/v3/sequences", "Marketing API v3"),
            ("/crm/v3/objects/sequences", "CRM API v3"),
        ]
        
        sequences_list = []
        last_error = None
        
        for endpoint, api_name in endpoints_to_try:
            try:
                url = f"https://api.hubapi.com{endpoint}"
                headers = {
                    "Authorization": f"Bearer {settings.hubspot_api_key}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Trying to fetch sequences from {api_name} ({endpoint})...")
                response = requests.get(url, headers=headers, timeout=30)
                
                # Check status code BEFORE calling raise_for_status()
                if response.status_code == 404:
                    logger.warning(f"{api_name} endpoint not available (404) - trying next endpoint")
                    last_error = f"404 Not Found: {endpoint}"
                    continue
                
                # Only raise for non-404 errors
                if not response.ok:
                    logger.warning(f"{api_name} returned status {response.status_code}: {response.text[:200]}")
                    last_error = f"{response.status_code} {response.reason}: {endpoint}"
                    continue
                
                sequences_data = response.json()
                
                # Parse sequences from response based on API format
                if isinstance(sequences_data, dict):
                    # Automation API v4: {"results": [...], "paging": {...}}
                    if 'results' in sequences_data:
                        sequences_list = sequences_data['results']
                    # Marketing API v3: {"objects": [...]}
                    elif 'objects' in sequences_data:
                        sequences_list = sequences_data['objects']
                    # Direct list (fallback)
                    elif isinstance(sequences_data.get('data'), list):
                        sequences_list = sequences_data['data']
                    # Single sequence (fallback)
                    elif sequences_data.get('id'):
                        sequences_list = [sequences_data]
                elif isinstance(sequences_data, list):
                    sequences_list = sequences_data
                
                if sequences_list:
                    logger.info(f"Successfully fetched {len(sequences_list)} sequences from {api_name}")
                    break
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"{api_name} endpoint not available - trying next endpoint")
                    last_error = str(e)
                    continue
                else:
                    logger.error(f"HTTP error from {api_name}: {e}")
                    last_error = str(e)
            except Exception as e:
                logger.warning(f"Error trying {api_name}: {e} - trying next endpoint")
                last_error = str(e)
        
        # If no sequences found via API, check if we can use the HubSpot SDK
        if not sequences_list:
            try:
                logger.info("Trying HubSpot Python SDK automation API...")
                # Try using the SDK's automation API
                if hasattr(api_client, 'automation') and hasattr(api_client.automation, 'workflows_api'):
                    workflows = api_client.automation.workflows_api.get_all()
                    if hasattr(workflows, 'results'):
                        sequences_list = workflows.results
                    elif isinstance(workflows, list):
                        sequences_list = workflows
                    elif hasattr(workflows, 'data'):
                        sequences_list = workflows.data if isinstance(workflows.data, list) else []
                    if sequences_list:
                        logger.info(f"Successfully fetched {len(sequences_list)} sequences via HubSpot SDK")
            except Exception as e:
                logger.warning(f"HubSpot SDK method also failed: {e}")
                # Don't set last_error here, we want to preserve the API error message
        
        # If still no sequences, log warning but don't fail completely
        if not sequences_list:
            logger.warning(
                f"Could not fetch sequences from HubSpot. "
                f"This may be because Marketing Automation is not enabled in your HubSpot account. "
                f"Last error: {last_error}. "
                f"Creating empty sync record."
            )
            # Insert a placeholder record to indicate sync ran but no sequences found
            placeholder_row = {
                "sequence_id": "NO_SEQUENCES_AVAILABLE",
                "sequence_name": "No sequences available - Marketing Automation may not be enabled",
                "is_active": False,
                "enrollment_count": 0,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
            try:
                bq_client.insert_rows("hubspot_sequences", [placeholder_row])
                logger.info("Inserted placeholder record indicating no sequences available")
            except Exception as e:
                logger.error(f"Error inserting placeholder: {e}")
            return 0, 0  # Return success with 0 sequences (not an error condition)
        
        logger.info(f"Processing {len(sequences_list)} sequences from HubSpot")
        
        rows = []
        for sequence in sequences_list:
            try:
                # Handle different API response formats
                sequence_id = str(sequence.get("id") or sequence.get("workflowId") or sequence.get("sequenceId") or "")
                sequence_name = sequence.get("name") or sequence.get("workflowName") or sequence.get("sequenceName") or "Unknown"
                
                # Filter for sequences only if type field exists
                workflow_type = sequence.get("type", "").upper()
                if workflow_type and workflow_type not in ["DRIP_DELAY", "SEQUENCE", "DRIP"]:
                    # Skip non-sequence workflows if type is specified
                    continue
                
                row = {
                    "sequence_id": sequence_id,
                    "sequence_name": sequence_name,
                    "is_active": sequence.get("enabled", sequence.get("active", sequence.get("isActive", True))),
                    "enrollment_count": sequence.get("contactCount", sequence.get("enrollmentCount", sequence.get("enrolledContacts", sequence.get("enrollments", 0)))),
                    "last_synced": datetime.now(timezone.utc).isoformat()
                }
                # Only add if we have at least an ID
                if row["sequence_id"] and row["sequence_id"] != "NO_SEQUENCES_AVAILABLE":
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
            logger.warning("No valid sequences to insert after processing")
        
        return sequences_synced, errors
        
    except Exception as e:
        logger.error(f"Error fetching sequences from HubSpot: {e}", exc_info=True)
        return sequences_synced, errors + 1

