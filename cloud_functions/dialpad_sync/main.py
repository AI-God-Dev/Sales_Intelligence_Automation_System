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
    # Based on working curl -G command, /calls endpoint works
    # Try without user_id first (get all calls), then filter by user
    endpoints_to_try = [
        (f"/calls", "General calls endpoint (all calls)", False),  # Get all calls first
        (f"/calls", "General calls endpoint with user_id param", True),  # Then try with user_id
        (f"/users/{user_id}/calls", "User-specific calls endpoint", False),
        (f"/call_logs", "Call logs endpoint", False),
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
            
            # Handle different response structures
            # Response might be: array directly, or {"items": [...]}, or {"calls": [...]}
            if isinstance(data, list):
                calls = data
            else:
                calls = data.get("items", []) or data.get("calls", []) or data.get("data", [])
            
            # If we got calls but need to filter by user_id
            # Check target.id (user who received/made call) from the JSON structure we saw
            if calls and (not use_user_param or len(calls) > 0):
                # Filter calls that belong to this user
                # Check target.id (from the JSON: "target": {"id": "4966031882665984"})
                filtered_calls = [
                    call for call in calls 
                    if str(call.get("target", {}).get("id")) == str(user_id) or 
                       str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id) or
                       str(call.get("contact", {}).get("id")) == str(user_id)
                ]
                
                # If we got all calls and need to filter, use filtered list
                if not use_user_param and filtered_calls:
                    calls = filtered_calls
                    if isinstance(data, dict):
                        data["items"] = filtered_calls
                elif use_user_param and not filtered_calls:
                    logger.warning(f"No calls found for user {user_id} in response")
                    continue
            
            if calls or (isinstance(data, dict) and data):  # Accept if we got data structure even if empty
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
            
            # Handle different response structures
            # Response might be: array directly, or {"items": [...]}, or {"calls": [...]}
            if isinstance(data, list):
                calls = data
            else:
                # Handle different response structures
            if isinstance(data, list):
                calls = data
            else:
                calls = data.get("items", []) or data.get("calls", []) or data.get("data", [])
            
            # If we got all calls, filter by user_id
            # Check target.id (user who received/made call) from JSON structure
            if calls and needs_user_filter:
                calls = [
                    call for call in calls 
                    if str(call.get("target", {}).get("id")) == str(user_id) or 
                       str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id) or
                       str(call.get("contact", {}).get("id")) == str(user_id)
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
                    call_id = call.get("call_id") or call.get("id", "unknown")
                    logger.error(f"Error transforming call {call_id}: {e}")
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
    # Dialpad API returns: call_id, external_number, internal_number, date_started, duration (ms)
    call_id = call.get("call_id") or call.get("id")
    
    # Get phone numbers - Dialpad uses external_number and internal_number
    external_number = call.get("external_number", "")
    internal_number = call.get("internal_number", "")
    
    # Determine from/to based on direction
    direction = call.get("direction", "").lower()
    if direction == "outbound":
        from_number = normalize_phone(internal_number)
        to_number = normalize_phone(external_number)
    else:  # inbound
        from_number = normalize_phone(external_number)
        to_number = normalize_phone(internal_number)
    
    # Duration is in milliseconds, convert to seconds
    duration_ms = call.get("duration", 0)
    duration_seconds = int(duration_ms / 1000) if duration_ms else None
    
    # Parse timestamp - Dialpad returns milliseconds timestamp
    date_started = call.get("date_started")
    call_time = _parse_timestamp_ms(date_started) if date_started else None
    
    # Get transcript if available
    transcript_text = None
    if call.get("recording_details"):
        # Transcript might be in recording_details or separate endpoint
        transcript_text = None  # Will be fetched separately if needed
    
    # Get sentiment if available
    sentiment_score = call.get("mos_score")  # Dialpad uses MOS score, not sentiment
    
    # Get user_id from target if not provided
    target_user_id = call.get("target", {}).get("id") if call.get("target") else user_id
    
    return {
        "call_id": str(call_id) if call_id else None,
        "direction": direction,
        "from_number": from_number,
        "to_number": to_number,
        "duration_seconds": duration_seconds,
        "transcript_text": transcript_text,
        "sentiment_score": float(sentiment_score) if sentiment_score else None,
        "call_time": call_time,
        "user_id": str(target_user_id) if target_user_id else user_id,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }


def _parse_timestamp_ms(timestamp_ms: str) -> str:
    """Parse Dialpad timestamp (milliseconds) to ISO format."""
    if not timestamp_ms:
        return None
    
    try:
        # Dialpad returns timestamp in milliseconds as string
        timestamp_int = int(timestamp_ms)
        # Convert milliseconds to seconds
        dt = datetime.fromtimestamp(timestamp_int / 1000.0, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError, OSError) as e:
        logger.warning(f"Error parsing timestamp {timestamp_ms}: {e}")
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

