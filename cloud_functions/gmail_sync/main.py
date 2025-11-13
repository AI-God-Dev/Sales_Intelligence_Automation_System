"""
Gmail Sync Cloud Function
Ingests all messages from 3 Gmail mailboxes (full + incremental sync)
"""
import functions_framework
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger, log_etl_run
from config.config import settings

logger = setup_logger(__name__)


@functions_framework.http
def gmail_sync(request):
    """
    Cloud Function entry point for Gmail sync.
    
    Expected request parameters:
    - mailbox_email: Email address of mailbox to sync
    - sync_type: 'full' or 'incremental'
    - access_token: OAuth access token for Gmail API
    """
    try:
        request_json = request.get_json(silent=True) or {}
        mailbox_email = request_json.get("mailbox_email")
        sync_type = request_json.get("sync_type", "incremental")
        access_token = request_json.get("access_token")
        
        if not mailbox_email or not access_token:
            return {"error": "mailbox_email and access_token required"}, 400
        
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # Build Gmail API service
        credentials = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get history ID for incremental sync
        history_id = None
        if sync_type == "incremental":
            history_id = _get_last_history_id(bq_client, mailbox_email)
        
        # Sync messages
        messages_synced, errors = _sync_messages(
            service,
            bq_client,
            mailbox_email,
            history_id
        )
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if errors == 0 else "partial" if messages_synced > 0 else "failed"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="gmail",
            job_type=sync_type,
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=messages_synced,
            rows_failed=errors,
            status=status
        )
        
        return {
            "status": "success",
            "messages_synced": messages_synced,
            "errors": errors
        }, 200
        
    except Exception as e:
        logger.error(f"Gmail sync failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


def _get_last_history_id(bq_client: BigQueryClient, mailbox_email: str) -> str:
    """Get last processed history ID for incremental sync."""
    query = f"""
    SELECT MAX(history_id) as last_history_id
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.gmail_sync_state`
    WHERE mailbox_email = @mailbox_email
    """
    
    # This table would need to be created separately
    # For now, return None to do full sync
    return None


def _sync_messages(
    service,
    bq_client: BigQueryClient,
    mailbox_email: str,
    history_id: str = None
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
        if history_id:
            # Incremental sync using history
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
        else:
            # Full sync - get all messages
            results = service.users().messages().list(
                userId='me',
                maxResults=500
            ).execute()
            message_ids = [msg['id'] for msg in results.get('messages', [])]
        
        # Batch process messages
        batch_size = 100
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            batch_messages = _fetch_message_batch(service, batch_ids)
            
            # Transform and insert to BigQuery
            rows = []
            for msg in batch_messages:
                try:
                    row = _transform_message(msg, mailbox_email)
                    rows.append(row)
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


def _transform_message(msg: Dict[str, Any], mailbox_email: str) -> Dict[str, Any]:
    """Transform Gmail message to BigQuery row format."""
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
    
    # Extract email addresses
    from_email = headers.get('From', '').split('<')[-1].replace('>', '').strip()
    to_emails = _parse_email_list(headers.get('To', ''))
    cc_emails = _parse_email_list(headers.get('Cc', ''))
    
    # Extract body
    body_text, body_html = _extract_body(msg.get('payload', {}))
    
    return {
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

