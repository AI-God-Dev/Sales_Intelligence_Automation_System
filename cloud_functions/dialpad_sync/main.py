"""
Dialpad Sync Cloud Function
Extracts call logs and transcripts from Dialpad API
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
import requests

# Import project modules (after path is set)
try:
    from utils.bigquery_client import BigQueryClient
    from utils.logger import setup_logger
    from utils.phone_normalizer import normalize_phone
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
def dialpad_sync(request):
    """
    Cloud Function entry point for Dialpad sync.
    
    Expected request parameters:
    - user_id: Dialpad user ID to sync calls for
    - sync_type: 'full' or 'incremental'
    """
    try:
        request_json = request.get_json(silent=True) or {}
        user_id = request_json.get("user_id")
        sync_type = request_json.get("sync_type", "incremental")
        
        if not user_id:
            return {"error": "user_id required"}, 400
        
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # Sync calls
        calls_synced, errors = _sync_calls(
            bq_client,
            user_id,
            sync_type
        )
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if errors == 0 else "partial" if calls_synced > 0 else "failed"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="dialpad",
            job_type=sync_type,
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=calls_synced,
            rows_failed=errors,
            status=status
        )
        
        return {
            "status": "success",
            "calls_synced": calls_synced,
            "errors": errors
        }, 200
        
    except Exception as e:
        logger.error(f"Dialpad sync failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


def _sync_calls(
    bq_client: BigQueryClient,
    user_id: str,
    sync_type: str
) -> tuple[int, int]:
    """Sync Dialpad calls to BigQuery."""
    calls_synced = 0
    errors = 0
    
    api_key = settings.dialpad_api_key
    base_url = "https://dialpad.com/api/v2"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Get last sync timestamp for incremental
    last_sync_time = None
    if sync_type == "incremental":
        last_sync_time = _get_last_sync_time(bq_client, user_id)
    
    # Fetch calls from Dialpad API
    page = 1
    while True:
        params = {
            "user_id": user_id,
            "page": page,
            "per_page": 100
        }
        
        if last_sync_time:
            params["start_time"] = last_sync_time
        
        try:
            response = requests.get(
                f"{base_url}/calls",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            calls = data.get("items", [])
            if not calls:
                break
            
            # Transform and insert calls
            rows = []
            for call in calls:
                try:
                    row = _transform_call(call, user_id)
                    rows.append(row)
                except Exception as e:
                    logger.error(f"Error transforming call {call.get('id')}: {e}")
                    errors += 1
            
            if rows:
                try:
                    bq_client.insert_rows("dialpad_calls", rows)
                    calls_synced += len(rows)
                except Exception as e:
                    logger.error(f"Error inserting batch: {e}")
                    errors += len(rows)
            
            # Check if more pages
            if not data.get("has_more", False):
                break
            
            page += 1
            
        except requests.RequestException as e:
            logger.error(f"Error fetching calls from Dialpad: {e}")
            errors += 1
            break
    
    return calls_synced, errors


def _transform_call(call: dict, user_id: str) -> dict:
    """Transform Dialpad call record to BigQuery row format."""
    from_number = normalize_phone(call.get("from_number", ""))
    to_number = normalize_phone(call.get("to_number", ""))
    
    return {
        "call_id": call.get("id"),
        "direction": call.get("direction", "").lower(),
        "from_number": from_number,
        "to_number": to_number,
        "duration_seconds": call.get("duration_seconds"),
        "transcript_text": call.get("transcript", {}).get("text") if call.get("transcript") else None,
        "sentiment_score": call.get("sentiment_score"),
        "call_time": _parse_timestamp(call.get("start_time")),
        "user_id": user_id,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }


def _parse_timestamp(timestamp: str) -> str:
    """Parse Dialpad timestamp to ISO format."""
    if not timestamp:
        return None
    
    try:
        from dateutil import parser
        dt = parser.parse(timestamp)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _get_last_sync_time(bq_client: BigQueryClient, user_id: str) -> str:
    """Get last sync time for incremental sync."""
    query = f"""
    SELECT MAX(call_time) as last_call_time
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.dialpad_calls`
    WHERE user_id = @user_id
    """
    
    from google.cloud import bigquery
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
        ]
    )
    
    try:
        results = bq_client.query(query, job_config)
        if results and results[0].get("last_call_time"):
            return results[0]["last_call_time"]
    except Exception:
        pass
    
    return None

