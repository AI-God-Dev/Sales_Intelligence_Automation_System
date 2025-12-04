"""
Cloud Run service for daily account scoring.
Runs before 8 AM daily via Cloud Scheduler.
"""
import functions_framework
import logging
from datetime import datetime, timezone
from intelligence.scoring.account_scorer import AccountScorer
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

logger = setup_logger(__name__)


@functions_framework.http
def account_scoring_job(request):
    """
    HTTP Cloud Function/Cloud Run entry point for daily account scoring.
    """
    try:
        started_at = datetime.now(timezone.utc).isoformat()
        logger.info("Starting daily account scoring job")
        
        bq_client = BigQueryClient()
        scorer = AccountScorer(bq_client)
        
        scored_count = scorer.score_all_accounts()
        
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "success" if scored_count > 0 else "failed"
        
        # Log ETL run (try to get failed count from logs if available)
        try:
            bq_client.log_etl_run(
                source_system="account_scoring",
                job_type="daily",
                started_at=started_at,
                completed_at=completed_at,
                rows_processed=scored_count,
                rows_failed=0,  # Could be enhanced to track actual failures
                status=status
            )
        except Exception as log_error:
            logger.warning(f"Failed to log ETL run: {log_error}")
        
        return {
            "status": "success",
            "accounts_scored": scored_count,
            "completed_at": completed_at
        }, 200
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Account scoring job failed: {error_message}", exc_info=True)
        
        # Try to log failed ETL run
        try:
            bq_client = BigQueryClient()
            bq_client.log_etl_run(
                source_system="account_scoring",
                job_type="daily",
                started_at=started_at if 'started_at' in locals() else datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                rows_processed=0,
                rows_failed=0,
                status="failed",
                error_message=error_message[:1000]  # Limit error message length
            )
        except Exception as log_error:
            logger.error(f"Failed to log ETL run error: {log_error}")
        
        return {
            "error": error_message,
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }, 500


if __name__ == "__main__":
    # For local testing
    request = type('Request', (), {'get_json': lambda x: {}})()
    response, status = account_scoring_job(request)
    print(f"Status: {status}")
    print(f"Response: {response}")

