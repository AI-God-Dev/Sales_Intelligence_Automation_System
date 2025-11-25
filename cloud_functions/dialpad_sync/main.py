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
    - user_id: (optional) Dialpad user ID to sync calls for. If not provided, syncs all users.
    - sync_type: 'full' or 'incremental' (default: 'incremental')
    """
    try:
        request_json = request.get_json(silent=True) or {}
        user_id = request_json.get("user_id")
        sync_type = request_json.get("sync_type", "incremental")
        
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # If user_id not provided, fetch all users and sync all
        if not user_id:
            logger.info("No user_id provided. Fetching all users and syncing all calls...")
            user_ids = _get_all_user_ids()
            
            if not user_ids:
                return {"error": "No users found in Dialpad account"}, 400
            
            logger.info(f"Found {len(user_ids)} users. Syncing calls for all users...")
            
            total_calls_synced = 0
            total_errors = 0
            
            for uid in user_ids:
                try:
                    calls_synced, errors = _sync_calls(bq_client, uid, sync_type)
                    total_calls_synced += calls_synced
                    total_errors += errors
                except requests.RequestException as e:
                    # Handle API errors gracefully - skip users that can't be accessed
                    if hasattr(e, 'response') and e.response is not None:
                        if e.response.status_code in [404, 403]:
                            logger.warning(f"Skipping user {uid}: {e.response.status_code} - {e}")
                            continue
                    logger.error(f"Error syncing calls for user {uid}: {e}")
                    total_errors += 1
                except Exception as e:
                    logger.error(f"Error syncing calls for user {uid}: {e}")
                    total_errors += 1
            
            calls_synced = total_calls_synced
            errors = total_errors
        else:
            # Sync for specific user
            calls_synced, errors = _sync_calls(bq_client, user_id, sync_type)
        
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


def _get_all_user_ids() -> list[str]:
    """Fetch all Dialpad user IDs from API."""
    api_key = settings.dialpad_api_key
    base_url = "https://dialpad.com/api/v2"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    user_ids = []
    page = 1
    
    try:
        while True:
            params = {
                "page": page,
                "per_page": 100
            }
            
            response = requests.get(
                f"{base_url}/users",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            users = data.get("items", [])
            if not users:
                break
            
            for user in users:
                user_id = user.get("id")
                if user_id:
                    user_ids.append(str(user_id))
            
            # Check if more pages
            if not data.get("has_more", False):
                break
            
            page += 1
        
        logger.info(f"Fetched {len(user_ids)} user IDs from Dialpad")
        return user_ids
    
    except requests.RequestException as e:
        logger.error(f"Error fetching users from Dialpad: {e}")
        raise Exception(f"Failed to fetch Dialpad users: {e}") from e


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
    
    # Try multiple endpoint patterns - Dialpad API structure may vary
    endpoints_to_try = [
        (f"/users/{user_id}/calls", "User-specific calls endpoint", False),
        (f"/calls", "General calls endpoint with user_id param", True),
        (f"/call_logs", "Call logs endpoint", True),
    ]
    
    calls_data = None
    working_endpoint = None
    needs_user_filter = False
    
    for endpoint, description, use_user_param in endpoints_to_try:
        try:
            params = {
                "page": 1,
                "per_page": 100
            }
            
            # For general endpoints, add user_id as param
            if use_user_param:
                params["user_id"] = user_id
            
            if last_sync_time:
                params["start_time"] = last_sync_time
            
            logger.info(f"Trying {description} ({endpoint}) for user {user_id}...")
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 404:
                logger.warning(f"{description} returned 404, trying next endpoint...")
                continue
            
            if not response.ok:
                logger.warning(f"{description} returned {response.status_code}, trying next endpoint...")
                continue
            
            data = response.json()
            calls = data.get("items", []) or data.get("calls", []) or data.get("data", [])
            
            # If using general endpoint, filter calls by user_id
            if use_user_param and calls:
                # Filter calls that belong to this user (check various user_id fields)
                filtered_calls = [
                    call for call in calls 
                    if str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id)
                ]
                if not filtered_calls:
                    logger.warning(f"No calls found for user {user_id} in general endpoint response")
                    continue
                data["items"] = filtered_calls
                calls = filtered_calls
            
            if calls or data:  # Accept if we got data structure even if empty
                calls_data = data
                working_endpoint = endpoint
                needs_user_filter = use_user_param
                logger.info(f"Successfully connected to {description} for user {user_id}")
                break
                
        except requests.RequestException as e:
            logger.warning(f"Error trying {description}: {e}, trying next endpoint...")
            continue
    
    if not calls_data:
        logger.warning(f"All endpoints failed for user {user_id}. User may not have calls or API structure differs.")
        return 0, 0
    
    # Fetch calls from Dialpad API using working endpoint
    page = 1
    while True:
        params = {
            "page": page,
            "per_page": 100
        }
        
        # For general endpoints, add user_id as param
        if needs_user_filter:
            params["user_id"] = user_id
        
        if last_sync_time:
            params["start_time"] = last_sync_time
        
        try:
            response = requests.get(
                f"{base_url}{working_endpoint}",
                headers=headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            calls = data.get("items", []) or data.get("calls", []) or data.get("data", [])
            
            # If using general endpoint, filter calls by user_id
            if needs_user_filter and calls:
                calls = [
                    call for call in calls 
                    if str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id)
                ]
            
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
            # Handle 404 errors gracefully - user might not have calls or endpoint not accessible
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    logger.warning(f"User {user_id} not found or has no calls endpoint (404). Skipping...")
                    # Don't count 404 as an error, just skip this user
                    break
                elif e.response.status_code == 403:
                    logger.warning(f"Access denied for user {user_id} (403). Skipping...")
                    break
            logger.error(f"Error fetching calls from Dialpad for user {user_id}: {e}")
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

