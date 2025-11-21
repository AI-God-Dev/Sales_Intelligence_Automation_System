"""
Gmail Sync Cloud Function
Ingests all messages from 3 Gmail mailboxes (full + incremental sync)
Uses domain-wide delegation (DWD) with service account for authentication
"""
import sys
import os
from pathlib import Path

# Add project root to Python path for imports
# This ensures utils, config, and entity_resolution modules are found
# Try multiple path resolution strategies for different deployment environments
_project_root = None
_possible_roots = [
    Path(__file__).parent.parent.parent,  # From cloud_functions/gmail_sync/main.py -> project root
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
    logger.info(f"Cloud functions directory exists: {(_project_root / 'cloud_functions').exists()}")
    if (_project_root / 'utils').exists():
        logger.info(f"Utils contents: {list((_project_root / 'utils').iterdir())}")
    if (_project_root / 'config').exists():
        logger.info(f"Config contents: {list((_project_root / 'config').iterdir())}")
else:
    logger.warning(f"Project root does not exist or is None: {_project_root}")

import functions_framework
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import time
import random
from google.cloud import bigquery
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    from utils.monitoring import publish_error_notification
    logger.info("Successfully imported publish_error_notification")
    
    logger.info("Attempting to import utils.validation...")
    from utils.validation import validate_email, validate_sync_type, ValidationError
    logger.info("Successfully imported validation functions")
    
    logger.info("Attempting to import config.config...")
    from config.config import settings
    logger.info("Successfully imported settings")
    
    logger.info("Attempting to import gmail_dwd...")
    from cloud_functions.gmail_sync.gmail_dwd import get_gmail_service_for_user
    logger.info("Successfully imported get_gmail_service_for_user")
    
    # Reinitialize logger with proper setup after imports succeed
    logger = setup_logger(__name__)
    logger.info("Successfully imported all required modules")
except ImportError as e:
    # Log import errors with full details
    logger.error(f"Import error during module load: {e}", exc_info=True)
    logger.error(f"Python path: {sys.path}")
    logger.error(f"Project root: {_project_root}")
    if _project_root and _project_root.exists():
        try:
            logger.error(f"Files in project root: {[f.name for f in _project_root.iterdir()]}")
        except Exception as list_error:
            logger.error(f"Could not list project root contents: {list_error}")
    
    # Try to provide helpful diagnostics
    import importlib.util
    failed_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
    logger.error(f"Failed to import module: {failed_module}")
    
    # Raise the error to fail fast - better than silent failures
    raise ImportError(
        f"Failed to import required modules during Cloud Function startup. "
        f"Error: {e}. "
        f"Python path: {sys.path}. "
        f"Project root: {_project_root}. "
        f"Please ensure all dependencies are installed and paths are correct. "
        f"Check Cloud Run logs for more details."
    ) from e


@functions_framework.http
def gmail_sync(request):
    """
    Cloud Function entry point for Gmail sync.
    Uses domain-wide delegation (DWD) - no access tokens needed.
    
    Expected request parameters:
    - mailbox_email: Email address of mailbox to sync (optional, defaults to configured mailboxes)
    - sync_type: 'full' or 'incremental' (default: 'incremental')
    """
    try:
        # Verify imports worked
        if BigQueryClient is None or settings is None:
            error_msg = f"Failed to import required modules. Project root: {_project_root}, Python path: {sys.path}"
            logger.error(error_msg)
            return {"error": "Internal server error - module import failed", "message": error_msg}, 500
        
        request_json = request.get_json(silent=True) or {}
        mailbox_email = request_json.get("mailbox_email")
        sync_type = request_json.get("sync_type", "incremental")
        
        # Validate inputs
        try:
            sync_type = validate_sync_type(sync_type)
            if mailbox_email:
                mailbox_email = validate_email(mailbox_email)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return {"error": str(e)}, 400
        
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # If no mailbox specified, sync all configured mailboxes
        mailboxes_to_sync = [mailbox_email] if mailbox_email else settings.gmail_mailboxes
        
        if not mailboxes_to_sync:
            return {
                "error": "No mailboxes configured or specified",
                "message": "Please configure mailboxes in settings or provide mailbox_email parameter"
            }, 400
        
        total_messages_synced = 0
        total_errors = 0
        
        # Sync each mailbox
        for mailbox in mailboxes_to_sync:
            try:
                logger.info(f"Starting Gmail sync for {mailbox} (type: {sync_type})")
                
                # Build Gmail API service using domain-wide delegation
                service = get_gmail_service_for_user(mailbox)
                
                # Get history ID for incremental sync
                history_id = None
                if sync_type == "incremental":
                    history_id = _get_last_history_id(bq_client, mailbox)
                
                # Sync messages
                messages_synced, errors = _sync_messages(
                    service,
                    bq_client,
                    mailbox,
                    history_id,
                    sync_type
                )
                
                total_messages_synced += messages_synced
                total_errors += errors
                
                # Update sync state
                _update_sync_state(bq_client, mailbox, history_id, sync_type)
                
                logger.info(f"Completed sync for {mailbox}: {messages_synced} messages, {errors} errors")
                
            except Exception as e:
                logger.error(f"Failed to sync mailbox {mailbox}: {str(e)}", exc_info=True)
                total_errors += 1
                # Publish error notification
                publish_error_notification(
                    source_system="gmail",
                    mailbox=mailbox,
                    error=str(e),
                    sync_type=sync_type
                )
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if total_errors == 0 else "partial" if total_messages_synced > 0 else "failed"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="gmail",
            job_type=sync_type,
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=total_messages_synced,
            rows_failed=total_errors,
            status=status
        )
        
        response_body = {
            "status": status,
            "messages_synced": total_messages_synced,
            "errors": total_errors,
            "mailboxes_synced": len(mailboxes_to_sync)
        }
        if status == "failed":
            response_body["error"] = "Gmail sync failed"
        http_status = 200 if status in ("success", "partial") else 500
        return response_body, http_status
        
    except ValidationError as e:
        logger.warning(f"Validation error in Gmail sync: {e}")
        return {
            "error": "Invalid request parameters",
            "message": str(e),
            "status_code": 400
        }, 400
    except Exception as e:
        logger.error(f"Gmail sync failed: {str(e)}", exc_info=True)
        try:
            publish_error_notification(
                source_system="gmail",
                error=str(e),
                sync_type=request_json.get("sync_type", "unknown")
            )
        except:
            pass  # Ignore notification errors
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred during Gmail sync. Please check logs for details.",
            "status_code": 500
        }, 500


def _get_last_history_id(bq_client: BigQueryClient, mailbox_email: str) -> Optional[str]:
    """Get last processed history ID for incremental sync."""
    query = f"""
    SELECT last_history_id
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.gmail_sync_state`
    WHERE mailbox_email = @mailbox_email
    ORDER BY last_sync_at DESC
    LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("mailbox_email", "STRING", mailbox_email)
        ]
    )
    
    try:
        results = bq_client.query(query, job_config)
        if results and results[0].get("last_history_id"):
            return results[0]["last_history_id"]
    except Exception as e:
        logger.warning(f"Could not get last history ID for {mailbox_email}: {e}")
    
    return None


def _update_sync_state(
    bq_client: BigQueryClient,
    mailbox_email: str,
    history_id: Optional[str],
    sync_type: str
):
    """Update sync state table with latest history ID."""
    query = f"""
    MERGE `{bq_client.project_id}.{bq_client.dataset_id}.gmail_sync_state` AS target
    USING (
        SELECT 
            @mailbox_email AS mailbox_email,
            @history_id AS last_history_id,
            CURRENT_TIMESTAMP() AS last_sync_at,
            @sync_type AS sync_type,
            CURRENT_TIMESTAMP() AS updated_at
    ) AS source
    ON target.mailbox_email = source.mailbox_email
    WHEN MATCHED THEN
        UPDATE SET
            last_history_id = source.last_history_id,
            last_sync_at = source.last_sync_at,
            sync_type = source.sync_type,
            updated_at = source.updated_at
    WHEN NOT MATCHED THEN
        INSERT (mailbox_email, last_history_id, last_sync_at, sync_type, updated_at)
        VALUES (source.mailbox_email, source.last_history_id, source.last_sync_at, source.sync_type, source.updated_at)
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("mailbox_email", "STRING", mailbox_email),
            bigquery.ScalarQueryParameter("history_id", "STRING", history_id or ""),
            bigquery.ScalarQueryParameter("sync_type", "STRING", sync_type)
        ]
    )
    
    try:
        bq_client.query(query, job_config)
    except Exception as e:
        logger.error(f"Failed to update sync state for {mailbox_email}: {e}")


def _sync_messages(
    service,
    bq_client: BigQueryClient,
    mailbox_email: str,
    history_id: Optional[str] = None,
    sync_type: str = "incremental"
) -> tuple[int, int]:
    """
    Sync Gmail messages to BigQuery.
    
    Returns:
        Tuple of (messages_synced, errors)
    """
    messages_synced = 0
    errors = 0
    
    try:
        # Get message list
        message_ids = []
        if history_id and sync_type == "incremental":
            # Incremental sync using history
            try:
                history = service.users().history().list(
                    userId='me',
                    startHistoryId=history_id,
                    historyTypes=['messageAdded']
                ).execute()
                
                message_ids = [
                    change['message']['id']
                    for change in history.get('history', [])
                    if 'message' in change
                ]
                
                # Get the latest history ID for state update
                if history.get('historyId'):
                    history_id = history['historyId']
                    
            except Exception as e:
                logger.warning(f"History API failed, falling back to full sync: {e}")
                sync_type = "full"
        
        if not message_ids or sync_type == "full":
            # Full sync - get all messages (paginated)
            page_token = None
            while True:
                results = service.users().messages().list(
                    userId='me',
                    maxResults=500,
                    pageToken=page_token
                ).execute()
                
                message_ids.extend([msg['id'] for msg in results.get('messages', [])])
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                
                # Limit full sync to prevent timeout (can be adjusted)
                if len(message_ids) >= 10000:
                    logger.warning(f"Full sync limited to 10000 messages for {mailbox_email}")
                    break
        
        # Get current history ID for state tracking
        if not history_id:
            try:
                profile = service.users().getProfile(userId='me').execute()
                history_id = profile.get('historyId')
            except Exception as e:
                logger.warning(f"Could not get current history ID: {e}")
        
        # Batch process messages
        batch_size = 100
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            batch_messages = _fetch_message_batch(service, batch_ids)
            
            # Transform and insert to BigQuery
            rows = []
            participant_rows = []
            for msg in batch_messages:
                try:
                    row, participants = _transform_message(msg, mailbox_email)
                    rows.append(row)
                    participant_rows.extend(participants)
                except Exception as e:
                    logger.error(f"Error transforming message {msg.get('id')}: {e}")
                    errors += 1
            
            if rows:
                try:
                    bq_client.insert_rows("gmail_messages", rows)
                    messages_synced += len(rows)
                except Exception as e:
                    logger.error(f"Error inserting batch: {e}")
                    errors += len(rows)
            
            # Insert participants
            if participant_rows:
                try:
                    bq_client.insert_rows("gmail_participants", participant_rows)
                except Exception as e:
                    logger.error(f"Error inserting participants: {e}")
        
        # Update sync state with latest history ID
        if history_id:
            _update_sync_state(bq_client, mailbox_email, history_id, sync_type)
        
        return messages_synced, errors
        
    except Exception as e:
        logger.error(f"Error syncing messages: {e}", exc_info=True)
        return messages_synced, errors + 1


def _fetch_message_batch(service, message_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch batch of messages from Gmail API with rate limiting and exponential backoff.
    
    Gmail API quota: 250 requests per minute per user
    """
    messages = []
    failed_ids = []
    
    for msg_id in message_ids:
        max_retries = 5
        retry_count = 0
        base_delay = 1  # Start with 1 second delay
        
        while retry_count < max_retries:
            try:
                # Rate limiting: Gmail allows 250 requests/minute = ~4 requests/second
                # Add small random delay to spread requests
                time.sleep(0.25 + random.uniform(0, 0.1))
                
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                messages.append(msg)
                break  # Success, move to next message
                
            except HttpError as e:
                error_code = e.resp.status if hasattr(e, 'resp') else None
                error_reason = None
                
                # Parse error details
                if hasattr(e, 'error_details') and e.error_details:
                    for detail in e.error_details:
                        if detail.get('reason') == 'rateLimitExceeded':
                            error_reason = 'rateLimitExceeded'
                            break
                
                if error_code == 403 and error_reason == 'rateLimitExceeded':
                    # Rate limit exceeded - exponential backoff with jitter
                    if retry_count < max_retries - 1:
                        delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
                        logger.warning(
                            f"Rate limit exceeded for message {msg_id}, "
                            f"retrying in {delay:.2f}s (attempt {retry_count + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        retry_count += 1
                    else:
                        logger.error(f"Rate limit exceeded for message {msg_id} after {max_retries} retries")
                        failed_ids.append(msg_id)
                        break
                elif error_code == 404:
                    # Message not found (might be deleted) - skip
                    logger.warning(f"Message {msg_id} not found (might be deleted)")
                    break
                elif error_code == 403:
                    # Other 403 errors (permission denied, etc.)
                    logger.error(f"403 Forbidden for message {msg_id}: {e}")
                    failed_ids.append(msg_id)
                    break
                else:
                    # Other HTTP errors - retry with exponential backoff
                    if retry_count < max_retries - 1:
                        delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
                        logger.warning(
                            f"Error {error_code} fetching message {msg_id}, "
                            f"retrying in {delay:.2f}s (attempt {retry_count + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        retry_count += 1
                    else:
                        logger.error(f"Error fetching message {msg_id} after {max_retries} retries: {e}")
                        failed_ids.append(msg_id)
                        break
                        
            except Exception as e:
                # Non-HTTP errors (network, timeout, etc.)
                if retry_count < max_retries - 1:
                    delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
                    logger.warning(
                        f"Error fetching message {msg_id}: {e}, "
                        f"retrying in {delay:.2f}s (attempt {retry_count + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    retry_count += 1
                else:
                    logger.error(f"Error fetching message {msg_id} after {max_retries} retries: {e}")
                    failed_ids.append(msg_id)
                    break
        
        # If we've been rate limited a lot, add extra delay to slow down
        if len(messages) > 0 and len(messages) % 100 == 0:
            logger.info(f"Fetched {len(messages)} messages so far, pausing briefly...")
            time.sleep(2)  # Pause every 100 messages to avoid hitting limits
    
    if failed_ids:
        logger.warning(f"Failed to fetch {len(failed_ids)} messages: {failed_ids[:10]}...")  # Log first 10
    
    return messages


def _transform_message(msg: Dict[str, Any], mailbox_email: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Transform Gmail message to BigQuery row format.
    
    Returns:
        Tuple of (message_row, participant_rows)
    """
    import uuid
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    
    # Extract email addresses
    from_email = headers.get('From', '').split('<')[-1].replace('>', '').strip()
    to_emails = _parse_email_list(headers.get('To', ''))
    cc_emails = _parse_email_list(headers.get('Cc', ''))
    bcc_emails = _parse_email_list(headers.get('Bcc', ''))
    
    # Extract body
    body_text, body_html = _extract_body(msg.get('payload', {}))
    
    message_row = {
        "message_id": msg['id'],
        "thread_id": msg.get('threadId'),
        "mailbox_email": mailbox_email,
        "from_email": from_email.lower() if from_email else None,
        "to_emails": to_emails,
        "cc_emails": cc_emails,
        "subject": headers.get('Subject', ''),
        "body_text": body_text,
        "body_html": body_html,
        "sent_at": _parse_timestamp(headers.get('Date')),
        "labels": msg.get('labelIds', []),
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create participant rows
    participant_rows = []
    if from_email:
        participant_rows.append({
            "participant_id": str(uuid.uuid4()),
            "message_id": msg['id'],
            "email_address": from_email.lower(),
            "role": "from",
            "sf_contact_id": None,
            "sf_account_id": None,
            "match_confidence": None
        })
    
    for email in to_emails:
        participant_rows.append({
            "participant_id": str(uuid.uuid4()),
            "message_id": msg['id'],
            "email_address": email.lower(),
            "role": "to",
            "sf_contact_id": None,
            "sf_account_id": None,
            "match_confidence": None
        })
    
    for email in cc_emails:
        participant_rows.append({
            "participant_id": str(uuid.uuid4()),
            "message_id": msg['id'],
            "email_address": email.lower(),
            "role": "cc",
            "sf_contact_id": None,
            "sf_account_id": None,
            "match_confidence": None
        })
    
    return message_row, participant_rows


def _parse_email_list(email_string: str) -> List[str]:
    """Parse comma-separated email list."""
    if not email_string:
        return []
    
    emails = []
    for part in email_string.split(','):
        email = part.split('<')[-1].replace('>', '').strip().lower()
        if email:
            emails.append(email)
    return emails


def _extract_body(payload: Dict[str, Any]) -> tuple[str, str]:
    """Extract plain text and HTML body from message payload."""
    body_text = ""
    body_html = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body_text = part['body'].get('data', '')
            elif part['mimeType'] == 'text/html':
                body_html = part['body'].get('data', '')
    elif payload.get('mimeType') == 'text/plain':
        body_text = payload['body'].get('data', '')
    elif payload.get('mimeType') == 'text/html':
        body_html = payload['body'].get('data', '')
    
    # Decode base64
    import base64
    if body_text:
        body_text = base64.urlsafe_b64decode(body_text).decode('utf-8', errors='ignore')
    if body_html:
        body_html = base64.urlsafe_b64decode(body_html).decode('utf-8', errors='ignore')
    
    return body_text, body_html


def _parse_timestamp(date_string: str) -> str:
    """Parse email date string to ISO timestamp."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(date_string)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
