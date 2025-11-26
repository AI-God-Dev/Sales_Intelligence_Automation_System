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
from typing import Optional
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
        
        # Use workaround method: Fetch all calls, then filter locally
        # Dialpad API limitation: Cannot filter by BOTH time range AND user_id together
        # Solution: Fetch all recent calls (limit=1000), then filter locally by date and user
        logger.info("Using workaround method: Fetch all calls, filter locally by date/user...")
        calls_synced, errors = _sync_all_calls_workaround(bq_client, sync_type, user_id)
        
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


def _sync_all_calls_workaround(
    bq_client: BigQueryClient,
    sync_type: str,
    user_id: Optional[str] = None
) -> tuple[int, int]:
    """
    Sync Dialpad calls using workaround method.
    
    Dialpad API limitation: Cannot filter by BOTH time range AND user_id together.
    Workaround: Fetch all recent calls (limit=1000, no filters), then filter locally.
    
    Args:
        bq_client: BigQuery client
        sync_type: 'full' or 'incremental'
        user_id: Optional user ID to filter by (if None, syncs all users)
    
    Returns:
        Tuple of (calls_synced, errors)
    """
    calls_synced = 0
    errors = 0
    
    api_key = settings.dialpad_api_key
    base_url = "https://dialpad.com/api/v2"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Get last sync timestamp for incremental filtering (in milliseconds)
    last_sync_timestamp_ms = None
    if sync_type == "incremental":
        query = f"""
        SELECT MAX(call_time) as last_call_time
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.dialpad_calls`
        """
        try:
            results = bq_client.query(query)
            if results and results[0].get("last_call_time"):
                last_sync_time = results[0]["last_call_time"]
                # Convert to timestamp (milliseconds) for comparison with date_started
                if isinstance(last_sync_time, str):
                    dt = datetime.fromisoformat(last_sync_time.replace('Z', '+00:00'))
                    last_sync_timestamp_ms = int(dt.timestamp() * 1000)
                elif hasattr(last_sync_time, 'timestamp'):
                    last_sync_timestamp_ms = int(last_sync_time.timestamp() * 1000)
                logger.info(f"Last sync timestamp: {last_sync_timestamp_ms} (filtering calls after this)")
        except Exception as e:
            logger.warning(f"Could not get last sync time: {e}")
    
    # WORKAROUND: Fetch all recent calls with NO filters (this works!)
    # Use /call endpoint - limit=10 works, limit=100+ returns 400
    # Response structure: {"cursor": "...", "items": [...]}
    # Use cursor-based pagination to get all calls
    page_size = 10  # This limit works (100+ returns 400)
    all_calls_list = []
    cursor = None
    max_iterations = 1000  # Safety limit (10 calls per page = up to 10,000 calls)
    
    try:
        logger.info(f"Fetching all recent calls (workaround method with cursor pagination)...")
        logger.info(f"Using /call endpoint with limit={page_size}")
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            params = {"limit": page_size}
            if cursor:
                params["cursor"] = cursor
            
            logger.info(f"Iteration {iteration}: Fetching with limit={page_size}, cursor={'present' if cursor else 'none'}...")
            
            response = requests.get(
                f"{base_url}/call",
                headers=headers,
                params=params,
                timeout=60
            )
            
            logger.info(f"Iteration {iteration} - Status: {response.status_code}, URL: {response.url}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Response structure: {"cursor": "...", "items": [...]}
                    page_calls = []
                    if isinstance(data, list):
                        page_calls = data
                        cursor = None  # No cursor for list responses
                    else:
                        page_calls = data.get("items", []) or data.get("calls", []) or data.get("data", []) or []
                        cursor = data.get("cursor")  # Get cursor for next page
                    
                    if page_calls:
                        all_calls_list.extend(page_calls)
                        logger.info(f"Iteration {iteration}: Got {len(page_calls)} calls (total: {len(all_calls_list)})")
                        
                        # If no cursor or empty cursor, we're done
                        if not cursor:
                            logger.info(f"No cursor returned, pagination complete")
                            break
                    else:
                        logger.info(f"Iteration {iteration}: No calls found, stopping")
                        break
                    
                except Exception as e:
                    logger.error(f"Error parsing iteration {iteration} response: {e}", exc_info=True)
                    break
            else:
                logger.error(f"Failed iteration {iteration}: HTTP {response.status_code}")
                if response.status_code == 400:
                    logger.error("400 Bad Request - API may not support this request format")
                break
        
        all_calls = all_calls_list
        logger.info(f"✅ Fetched {len(all_calls)} total calls from Dialpad API (across {iteration} iterations)")
        
        if not all_calls:
            logger.warning(f"⚠️ No calls found in API response after pagination")
            logger.warning(f"Total iterations: {iteration}")
        else:
            logger.info(f"Processing {len(all_calls)} calls...")
        
        if all_calls:
            # Step 1: Filter by date locally (if incremental sync)
            if last_sync_timestamp_ms:
                filtered_calls = []
                for call in all_calls:
                    # Check date_started field (timestamp in milliseconds)
                    date_started = call.get("date_started")
                    if date_started:
                        # Handle both string and int timestamps
                        if isinstance(date_started, str):
                            try:
                                date_started = int(date_started)
                            except ValueError:
                                continue
                        if date_started >= last_sync_timestamp_ms:
                            filtered_calls.append(call)
                all_calls = filtered_calls
                logger.info(f"Filtered to {len(all_calls)} calls after timestamp {last_sync_timestamp_ms}")
            
            # Step 2: Filter by user locally (if specific user requested)
            if user_id:
                user_filtered_calls = []
                for call in all_calls:
                    # Check multiple possible fields for user identification
                    target = call.get("target", {})
                    call_user_id = None
                    
                    if target and target.get("type") == "user":
                        call_user_id = str(target.get("id"))
                    elif call.get("user_id"):
                        call_user_id = str(call.get("user_id"))
                    elif call.get("owner_id"):
                        call_user_id = str(call.get("owner_id"))
                    
                    if call_user_id == str(user_id):
                        user_filtered_calls.append(call)
                
                all_calls = user_filtered_calls
                logger.info(f"Filtered to {len(all_calls)} calls for user {user_id}")
            
            # Step 3: Transform and insert calls
            if all_calls:
                rows = []
                for call in all_calls:
                    try:
                        # Extract user_id from call data
                        call_user_id = None
                        target = call.get("target", {})
                        if target and target.get("type") == "user":
                            call_user_id = str(target.get("id"))
                        elif call.get("user_id"):
                            call_user_id = str(call.get("user_id"))
                        
                        row = _transform_call(call, call_user_id)
                        rows.append(row)
                    except Exception as e:
                        logger.error(f"Error transforming call {call.get('id')}: {e}")
                        errors += 1
                
                if rows:
                    try:
                        bq_client.insert_rows("dialpad_calls", rows)
                        calls_synced = len(rows)
                        logger.info(f"✅ Successfully inserted {calls_synced} calls using workaround method")
                    except Exception as e:
                        logger.error(f"Error inserting calls: {e}")
                        errors += len(rows)
            else:
                logger.info("No calls to sync after filtering")
            
    except Exception as e:
        logger.error(f"Error fetching all calls: {e}", exc_info=True)
        errors += 1
    
    return calls_synced, errors


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
    
    # First, test authentication by trying to get all calls (no user filter)
    # This helps us determine if the issue is with the endpoint or user-specific access
    logger.info(f"Testing Dialpad API authentication and endpoint access...")
    
    # Try multiple endpoint patterns - Dialpad API structure may vary
    # Strategy: Try to get ALL calls first, then filter by user if needed
    endpoints_to_try = [
        # Try getting all calls first (no user filter) - this tests if endpoint works at all
        (f"/calls", "All calls endpoint (no filter)", {}, False),
        # Try with limit parameter
        (f"/calls", "All calls with limit", {"limit": 100}, False),
        # Try with pagination
        (f"/calls", "All calls with pagination", {"page": 1, "per_page": 100}, False),
        # Try with user_id as query parameter
        (f"/calls", "Calls with user_id param", {"user_id": user_id, "limit": 100}, True),
        # Try user-specific endpoint
        (f"/users/{user_id}/calls", "User-specific calls endpoint", {"limit": 100}, True),
        # Try alternative endpoints
        (f"/call_logs", "Call logs endpoint", {"limit": 100}, False),
        (f"/v2/calls", "V2 calls endpoint", {"limit": 100}, False),
    ]
    
    calls_data = None
    working_endpoint = None
    working_params = None
    needs_user_filter = False
    
    for endpoint, description, params, is_user_specific in endpoints_to_try:
        try:
            # Add pagination if not already present
            if "page" not in params and "limit" not in params:
                params["page"] = 1
                params["per_page"] = 100
            
            if last_sync_time and "start_time" not in params:
                params["start_time"] = last_sync_time
            
            full_url = f"{base_url}{endpoint}"
            logger.info(f"Trying {description} ({endpoint}) with params {params}...")
            
            response = requests.get(
                full_url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}, URL: {response.url}")
            
            if response.status_code == 404:
                try:
                    error_body = response.text[:500]  # First 500 chars
                    logger.warning(f"{description} returned 404. Response: {error_body}")
                except:
                    pass
                continue
            
            if response.status_code == 401:
                logger.error(f"Authentication failed (401). Check API key permissions.")
                # Don't continue trying other endpoints if auth fails
                break
            
            if response.status_code == 403:
                logger.warning(f"Access denied (403) for {description}. API key may lack permissions.")
                continue
            
            if not response.ok:
                try:
                    error_body = response.text[:500]
                    logger.warning(f"{description} returned {response.status_code}. Response: {error_body}")
                except:
                    logger.warning(f"{description} returned {response.status_code}")
                continue
            
            # Try to parse JSON response
            try:
                data = response.json()
            except Exception as e:
                logger.warning(f"Failed to parse JSON response from {description}: {e}")
                logger.warning(f"Response text (first 500 chars): {response.text[:500]}")
                continue
            
            # Handle different response structures
            # Response might be: array directly, or {"items": [...]}, or {"calls": [...]}, or {"data": [...]}
            if isinstance(data, list):
                calls = data
            elif isinstance(data, dict):
                calls = data.get("items", []) or data.get("calls", []) or data.get("data", []) or data.get("results", [])
            else:
                calls = []
            
            logger.info(f"Retrieved {len(calls)} calls from {description}")
            
            # If we got calls, filter by user_id if needed
            if calls and not is_user_specific:
                # Filter calls that belong to this user
                # Check multiple possible fields for user identification
                filtered_calls = [
                    call for call in calls 
                    if str(call.get("target", {}).get("id")) == str(user_id) or 
                       str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id) or
                       str(call.get("contact", {}).get("id")) == str(user_id) or
                       str(call.get("user", {}).get("id")) == str(user_id)
                ]
                if filtered_calls:
                    calls = filtered_calls
                    logger.info(f"Filtered to {len(filtered_calls)} calls for user {user_id}")
                    if isinstance(data, dict):
                        data["items"] = filtered_calls
                else:
                    logger.warning(f"No calls found for user {user_id} in {len(calls)} total calls")
                    # Continue trying other endpoints even if this one has no user calls
            
            # Accept if we got a valid response structure (even if empty)
            # This means the endpoint works, just might not have data
            if isinstance(data, (dict, list)):
                calls_data = data
                working_endpoint = endpoint
                working_params = params.copy()
                needs_user_filter = not is_user_specific
                logger.info(f"Successfully connected to {description} - found {len(calls) if calls else 0} calls")
                # If we found calls, use this endpoint. Otherwise, continue trying.
                if calls:
                    break
                
        except requests.RequestException as e:
            logger.warning(f"Request error trying {description}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    logger.warning(f"Error response: {e.response.text[:500]}")
                except:
                    pass
            continue
        except Exception as e:
            logger.warning(f"Unexpected error trying {description}: {e}")
            continue
    
    if not calls_data:
        logger.warning(f"All endpoints failed for user {user_id}. Possible issues:")
        logger.warning("  1. API key may not have call logs permissions")
        logger.warning("  2. No calls exist in the account")
        logger.warning("  3. API endpoint structure may have changed")
        return 0, 0
    
    # If we found an endpoint but no calls, that's okay - just return 0
    if isinstance(calls_data, list):
        calls = calls_data
    else:
        calls = calls_data.get("items", []) or calls_data.get("calls", []) or calls_data.get("data", []) or []
    
    if not calls:
        logger.info(f"Endpoint {working_endpoint} works but no calls found for user {user_id}")
        return 0, 0
    
    # Fetch calls from Dialpad API using working endpoint
    page = 1
    has_more = True
    
    while has_more:
        # Start with working params and update pagination
        params = working_params.copy() if working_params else {}
        
        # Update pagination parameters
        if "page" in params:
            params["page"] = page
        elif "limit" in params:
            # If using limit, calculate offset
            limit = params.get("limit", 100)
            params["offset"] = (page - 1) * limit
        
        if last_sync_time and "start_time" not in params:
            params["start_time"] = last_sync_time
        
        try:
            logger.info(f"Fetching page {page} from {working_endpoint}...")
            response = requests.get(
                f"{base_url}{working_endpoint}",
                headers=headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Handle different response structures
            if isinstance(data, list):
                calls = data
            else:
                calls = data.get("items", []) or data.get("calls", []) or data.get("data", []) or data.get("results", [])
            
            # If we got all calls, filter by user_id
            if calls and needs_user_filter:
                original_count = len(calls)
                calls = [
                    call for call in calls 
                    if str(call.get("target", {}).get("id")) == str(user_id) or 
                       str(call.get("user_id")) == str(user_id) or 
                       str(call.get("owner_id")) == str(user_id) or
                       str(call.get("caller_id")) == str(user_id) or
                       str(call.get("contact", {}).get("id")) == str(user_id) or
                       str(call.get("user", {}).get("id")) == str(user_id)
                ]
                if original_count > len(calls):
                    logger.info(f"Filtered {original_count} calls to {len(calls)} for user {user_id}")
            
            if not calls:
                logger.info(f"No more calls found on page {page}")
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
                    logger.info(f"Inserted {len(rows)} calls (total: {calls_synced})")
                except Exception as e:
                    logger.error(f"Error inserting batch: {e}")
                    errors += len(rows)
            
            # Check if more pages
            # Different APIs use different pagination indicators
            if isinstance(data, dict):
                has_more = (
                    data.get("has_more", False) or 
                    data.get("next_page", None) is not None or
                    len(calls) >= params.get("per_page", params.get("limit", 100))
                )
            else:
                # If response is a list, check if we got a full page
                has_more = len(calls) >= params.get("per_page", params.get("limit", 100))
            
            if not has_more:
                logger.info(f"Reached end of pagination at page {page}")
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
    call_id_str = str(call_id) if call_id else None
    if call_id_str:
        # Try to get transcript from call data or fetch separately
        transcript_text = call.get("transcript") or call.get("transcription") or call.get("transcript_text")
        if not transcript_text and call.get("has_transcript") or call.get("recording_id"):
            # Fetch transcript from Dialpad API if available
            try:
                transcript_text = _fetch_call_transcript(call_id_str)
            except Exception as e:
                logger.debug(f"Could not fetch transcript for call {call_id_str}: {e}")
    
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


def _fetch_call_transcript(call_id: str) -> Optional[str]:
    """Fetch transcript for a specific call from Dialpad API."""
    api_key = settings.dialpad_api_key
    base_url = "https://dialpad.com/api/v2"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try multiple transcript endpoint patterns
    endpoints_to_try = [
        f"/calls/{call_id}/transcript",
        f"/calls/{call_id}/transcription",
        f"/call_logs/{call_id}/transcript",
        f"/recordings/{call_id}/transcript"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response structures
                transcript = (
                    data.get("transcript") or 
                    data.get("transcription") or 
                    data.get("text") or
                    data.get("content")
                )
                if transcript:
                    return transcript if isinstance(transcript, str) else str(transcript)
            elif response.status_code == 404:
                # Transcript not available for this call
                continue
        except requests.RequestException:
            continue
    
    return None


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

