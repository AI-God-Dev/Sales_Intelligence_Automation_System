"""
Salesforce Sync Cloud Function
Syncs Account, Contact, Lead, Opportunity, Task, Event, EmailMessage objects
"""
import sys
import os
from pathlib import Path

# Add project root to Python path for imports
# This ensures utils, config, and entity_resolution modules are found
_project_root = None
_possible_roots = [
    Path(__file__).parent.parent.parent,  # From cloud_functions/salesforce_sync/main.py -> project root
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
from simple_salesforce import Salesforce
import requests

# Import project modules (after path is set)
try:
    from utils.bigquery_client import BigQueryClient
    from utils.logger import setup_logger
    from utils.validation import validate_sync_type, validate_object_type, ValidationError
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
def salesforce_sync(request):
    """
    Cloud Function entry point for Salesforce sync.
    
    Expected request parameters:
    - object_type: 'Account', 'Contact', 'Lead', 'Opportunity', 'Task', 'Event', 'EmailMessage'
    - sync_type: 'full' or 'incremental'
    """
    try:
        request_json = request.get_json(silent=True) or {}
        object_type = request_json.get("object_type", "Account")
        sync_type = request_json.get("sync_type", "incremental")
        
        # Validate inputs
        try:
            sync_type = validate_sync_type(sync_type)
            allowed_objects = ["Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage"]
            object_type = validate_object_type(object_type, allowed_objects)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return {"error": str(e)}, 400
        
        # Initialize Salesforce connection using OAuth 2.0 (preferred) or username/password (fallback)
        sf = _get_salesforce_client(settings)
        
        bq_client = BigQueryClient()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # Sync based on object type
        rows_synced, errors = _sync_salesforce_object(
            sf,
            bq_client,
            object_type,
            sync_type
        )
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if errors == 0 else "partial" if rows_synced > 0 else "failed"
        
        # Log ETL run
        bq_client.log_etl_run(
            source_system="salesforce",
            job_type=sync_type,
            started_at=started_at,
            completed_at=completed_at,
            rows_processed=rows_synced,
            rows_failed=errors,
            status=status,
            watermark=_get_last_modified_date(bq_client, object_type)
        )
        
        return {
            "status": "success",
            "object_type": object_type,
            "rows_synced": rows_synced,
            "errors": errors
        }, 200
        
    except ValidationError as e:
        logger.warning(f"Validation error in Salesforce sync: {e}")
        return {
            "error": "Invalid request parameters",
            "message": str(e),
            "status_code": 400
        }, 400
    except Exception as e:
        logger.error(f"Salesforce sync failed: {str(e)}", exc_info=True)
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred during Salesforce sync. Please check logs for details.",
            "status_code": 500
        }, 500


def _get_salesforce_client(settings) -> Salesforce:
    """
    Get Salesforce client using OAuth 2.0 (preferred) or username/password (fallback).
    
    OAuth 2.0 uses: Client ID, Client Secret, Refresh Token
    Username/password uses: Username, Password, Security Token
    """
    try:
        # Try OAuth 2.0 first (more secure)
        client_id = settings.salesforce_client_id
        client_secret = settings.salesforce_client_secret
        refresh_token = settings.salesforce_refresh_token
        domain = settings.salesforce_domain  # 'login' or 'test'
        
        if client_id and client_secret and refresh_token:
            logger.info("Using OAuth 2.0 authentication for Salesforce")
            return _authenticate_with_oauth(client_id, client_secret, refresh_token, domain)
        
        # Fallback to username/password if OAuth not available
        logger.info("Using username/password authentication for Salesforce (OAuth not configured)")
        username = settings.salesforce_username or ""
        password = settings.salesforce_password or ""
        security_token = settings.salesforce_security_token or ""
        
        if not username or not password:
            raise Exception("Neither OAuth credentials (client_id, client_secret, refresh_token) nor username/password are configured. Please set secrets in Secret Manager.")
        
        return Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
        
    except Exception as e:
        logger.error(f"Failed to authenticate with Salesforce: {e}", exc_info=True)
        raise


def _authenticate_with_oauth(client_id: str, client_secret: str, refresh_token: str, domain: str) -> Salesforce:
    """
    Authenticate with Salesforce using OAuth 2.0 refresh token flow.
    
    Args:
        client_id: Salesforce Connected App Consumer Key
        client_secret: Salesforce Connected App Consumer Secret
        refresh_token: OAuth 2.0 refresh token
        domain: 'login' for production, 'test' for sandbox
    
    Returns:
        Authenticated Salesforce client instance
    """
    # Determine token URL based on domain
    if domain == "test":
        token_url = "https://test.salesforce.com/services/oauth2/token"
    else:
        token_url = "https://login.salesforce.com/services/oauth2/token"
    
    # Exchange refresh token for access token
    token_data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    
    response = requests.post(token_url, data=token_data, timeout=30)
    response.raise_for_status()
    
    token_response = response.json()
    access_token = token_response["access_token"]
    instance_url = token_response["instance_url"]
    
    logger.info(f"Successfully authenticated with Salesforce OAuth. Instance: {instance_url}")
    
    # Create Salesforce client with access token and instance URL
    # simple_salesforce supports session_id (access token) and instance_url
    sf = Salesforce(
        instance_url=instance_url,
        session_id=access_token
    )
    
    return sf


def _get_available_fields(sf: Salesforce, object_type: str, desired_fields: list[str]) -> str:
    """
    Get available fields from Salesforce object, filtering out fields that don't exist.
    
    Args:
        sf: Salesforce client
        object_type: Salesforce object type (e.g., "Account")
        desired_fields: List of field names to check
        
    Returns:
        Comma-separated string of available fields
    """
    try:
        # Describe the object to get all available fields
        describe_result = sf.restful(f"sobjects/{object_type}/describe/")
        available_field_names = {field["name"] for field in describe_result["fields"]}
        
        # Filter desired fields to only those that exist
        valid_fields = [f for f in desired_fields if f in available_field_names]
        
        if not valid_fields:
            logger.warning(f"No valid fields found for {object_type}. Available fields: {list(available_field_names)[:10]}...")
            # Fall back to just Id if nothing else is available
            return "Id"
        
        logger.info(f"Found {len(valid_fields)}/{len(desired_fields)} valid fields for {object_type}")
        missing_fields = set(desired_fields) - set(valid_fields)
        if missing_fields:
            logger.info(f"Missing fields (will be skipped): {missing_fields}")
        
        return ", ".join(valid_fields)
    except Exception as e:
        logger.warning(f"Error describing {object_type} fields, using all desired fields: {e}")
        # Fallback: return all desired fields (will fail if any don't exist)
        return ", ".join(desired_fields)


def _sync_salesforce_object(
    sf: Salesforce,
    bq_client: BigQueryClient,
    object_type: str,
    sync_type: str
) -> tuple[int, int]:
    """Sync a Salesforce object to BigQuery."""
    rows_synced = 0
    errors = 0
    
    # Map object types to table names and field mappings
    object_mappings = {
        "Account": {
            "table": "sf_accounts",
            "fields_list": ["Id", "Name", "Website", "Industry", "AnnualRevenue", "OwnerId", "CreatedDate", "LastModifiedDate"]
        },
        "Contact": {
            "table": "sf_contacts",
            "fields_list": ["Id", "AccountId", "FirstName", "LastName", "Email", "Phone", "MobilePhone", "Title", "CreatedDate", "LastModifiedDate"]
        },
        "Lead": {
            "table": "sf_leads",
            "fields_list": ["Id", "FirstName", "LastName", "Email", "Company", "Phone", "Title", "LeadSource", "Status", "OwnerId", "CreatedDate", "LastModifiedDate"]
        },
        "Opportunity": {
            "table": "sf_opportunities",
            "fields_list": ["Id", "AccountId", "Name", "StageName", "Amount", "CloseDate", "Probability", "OwnerId", "IsClosed", "IsWon", "CreatedDate", "LastModifiedDate"]
        },
        "Task": {
            "table": "sf_activities",
            "fields_list": ["Id", "WhatId", "WhoId", "Subject", "Description", "ActivityDate", "OwnerId", "CreatedDate", "LastModifiedDate"],
            "activity_type": "Task"
        },
        "Event": {
            "table": "sf_activities",
            "fields_list": ["Id", "WhatId", "WhoId", "Subject", "Description", "ActivityDate", "OwnerId", "CreatedDate", "LastModifiedDate"],
            "activity_type": "Event"
        }
    }
    
    if object_type not in object_mappings:
        raise ValueError(f"Unsupported object type: {object_type}")
    
    mapping = object_mappings[object_type]
    
    # Get available fields dynamically (filters out non-existent fields)
    fields_str = _get_available_fields(sf, object_type, mapping["fields_list"])
    mapping["fields"] = fields_str  # Store for transform function
    
    # Build SOQL query
    query = f"SELECT {fields_str} FROM {object_type}"
    
    # Add WHERE clause for incremental sync
    if sync_type == "incremental":
        last_modified = _get_last_modified_date(bq_client, object_type)
        if last_modified:
            query += f" WHERE LastModifiedDate > {last_modified}"
    
    query += " ORDER BY LastModifiedDate"
    
    try:
        # Query Salesforce
        results = sf.query_all(query)
        
        # Transform and insert rows
        rows = []
        for record in results['records']:
            try:
                row = _transform_record(record, object_type, mapping)
                rows.append(row)
            except Exception as e:
                logger.error(f"Error transforming {object_type} record {record.get('Id')}: {e}")
                errors += 1
        
        # Batch insert to BigQuery
        if rows:
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                try:
                    bq_client.insert_rows(mapping["table"], batch)
                    rows_synced += len(batch)
                except Exception as e:
                    logger.error(f"Error inserting batch: {e}")
                    errors += len(batch)
        
        return rows_synced, errors
        
    except Exception as e:
        logger.error(f"Error querying Salesforce: {e}", exc_info=True)
        return rows_synced, errors + 1


def _transform_record(record: dict, object_type: str, mapping: dict) -> dict:
    """Transform Salesforce record to BigQuery row format."""
    row = {}
    
    # Common transformations
    if "Id" in record:
        row[f"{object_type.lower()}_id"] = record["Id"]
    
    # Object-specific transformations
    if object_type == "Account":
        row.update({
            "account_id": record["Id"],
            "account_name": record.get("Name"),
            "website": record.get("Website"),
            "industry": record.get("Industry"),
            "annual_revenue": record.get("AnnualRevenue"),
            "owner_id": record.get("OwnerId"),
            "created_date": _parse_sf_datetime(record.get("CreatedDate")),
            "last_modified_date": _parse_sf_datetime(record.get("LastModifiedDate")),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        })
    elif object_type == "Contact":
        row.update({
            "contact_id": record["Id"],
            "account_id": record.get("AccountId"),
            "first_name": record.get("FirstName"),
            "last_name": record.get("LastName"),
            "email": record.get("Email", "").lower() if record.get("Email") else None,
            "phone": record.get("Phone"),
            "mobile_phone": record.get("MobilePhone"),
            "title": record.get("Title"),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        })
    elif object_type == "Lead":
        row.update({
            "lead_id": record["Id"],
            "first_name": record.get("FirstName"),
            "last_name": record.get("LastName"),
            "email": record.get("Email", "").lower() if record.get("Email") else None,
            "company": record.get("Company"),
            "phone": record.get("Phone"),
            "title": record.get("Title"),
            "lead_source": record.get("LeadSource"),
            "status": record.get("Status"),
            "owner_id": record.get("OwnerId"),
            "created_date": _parse_sf_datetime(record.get("CreatedDate")),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        })
    elif object_type == "Opportunity":
        row.update({
            "opportunity_id": record["Id"],
            "account_id": record.get("AccountId"),
            "name": record.get("Name"),
            "stage": record.get("StageName"),
            "amount": record.get("Amount"),
            "close_date": record.get("CloseDate"),
            "probability": record.get("Probability"),
            "owner_id": record.get("OwnerId"),
            "is_closed": record.get("IsClosed"),
            "is_won": record.get("IsWon"),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        })
    elif object_type in ["Task", "Event"]:
        row.update({
            "activity_id": record["Id"],
            "activity_type": mapping.get("activity_type", object_type),
            "what_id": record.get("WhatId"),
            "who_id": record.get("WhoId"),
            "subject": record.get("Subject"),
            "description": record.get("Description"),
            "activity_date": _parse_sf_datetime(record.get("ActivityDate")),
            "owner_id": record.get("OwnerId"),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        })
    
    return row


def _parse_sf_datetime(dt_string: str) -> str:
    """Parse Salesforce datetime string to ISO format."""
    if not dt_string:
        return None
    
    try:
        # Salesforce returns ISO format, just ensure timezone
        from dateutil import parser
        dt = parser.parse(dt_string)
        return dt.isoformat()
    except Exception:
        return None


def _get_last_modified_date(bq_client: BigQueryClient, object_type: str) -> str:
    """Get last modified date from BigQuery for incremental sync."""
    table_map = {
        "Account": "sf_accounts",
        "Contact": "sf_contacts",
        "Lead": "sf_leads",
        "Opportunity": "sf_opportunities",
        "Task": "sf_activities",
        "Event": "sf_activities"
    }
    
    table = table_map.get(object_type)
    if not table:
        return None
    
    query = f"""
    SELECT MAX(last_modified_date) as last_modified
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.{table}`
    """
    
    try:
        results = bq_client.query(query)
        if results and results[0].get("last_modified"):
            return results[0]["last_modified"]
    except Exception:
        pass
    
    return None

