"""
HubSpot Sync Cloud Function
Syncs available sequences metadata from HubSpot
"""
import functions_framework
import logging
from datetime import datetime, timezone
from hubspot import HubSpot
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

logger = setup_logger(__name__)


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
        # Fetch sequences from HubSpot API
        # Note: HubSpot API structure may vary - adjust based on actual API
        sequences_api = api_client.crm.sequences
        
        # Get all sequences
        all_sequences = sequences_api.get_all()
        
        rows = []
        for sequence in all_sequences.get("results", []):
            try:
                row = {
                    "sequence_id": sequence.get("id"),
                    "sequence_name": sequence.get("name"),
                    "is_active": sequence.get("enabled", False),
                    "enrollment_count": sequence.get("contactCount", 0),
                    "last_synced": datetime.now(timezone.utc).isoformat()
                }
                rows.append(row)
            except Exception as e:
                logger.error(f"Error transforming sequence {sequence.get('id')}: {e}")
                errors += 1
        
        if rows:
            try:
                bq_client.insert_rows("hubspot_sequences", rows)
                sequences_synced = len(rows)
            except Exception as e:
                logger.error(f"Error inserting sequences: {e}")
                errors += len(rows)
        
        return sequences_synced, errors
        
    except Exception as e:
        logger.error(f"Error fetching sequences from HubSpot: {e}", exc_info=True)
        return sequences_synced, errors + 1

