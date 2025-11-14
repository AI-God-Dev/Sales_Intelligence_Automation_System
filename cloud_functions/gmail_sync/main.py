"""
Gmail Sync Cloud Function
Ingests all messages from 3 Gmail mailboxes (full + incremental sync)
Uses domain-wide delegation (DWD) with service account for authentication
"""
import functions_framework
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from googleapiclient.discovery import build
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from utils.monitoring import publish_error_notification
from utils.validation import validate_email, validate_sync_type, ValidationError
from config.config import settings
from gmail_dwd import get_gmail_service_for_user

logger = setup_logger(__name__)


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
        
        return {
            "status": status,
            "messages_synced": total_messages_synced,
            "errors": total_errors,
            "mailboxes_synced": len(mailboxes_to_sync)
        }, 200
        
    except ValidationError as e:
        logger.warning(f"Validation error in Gmail sync: {e}")
        return {
            "error": "Invalid request parameters",
            "message": str(e),
            "status_code": 400
        }, 400
    except Exception as e:
        logger.error(f"Gmail sync failed: {str(e)}", exc_info=True)
        publish_error_notification(
            source_system="gmail",
            error=str(e),
            sync_type=request_json.get("sync_type", "unknown")
        )
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
    """Fetch batch of messages from Gmail API."""
    messages = []
    for msg_id in message_ids:
        try:
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            messages.append(msg)
        except Exception as e:
            logger.error(f"Error fetching message {msg_id}: {e}")
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

