"""Logging utilities for Cloud Functions and ETL jobs."""
import logging
import json
from typing import Any, Dict
from google.cloud import logging as cloud_logging


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up structured logging for Cloud Functions."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Use Google Cloud Logging if available, otherwise use standard logging
    try:
        client = cloud_logging.Client()
        client.setup_logging()
    except Exception:
        # Fallback to standard logging if Cloud Logging not available
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    return logger


def log_etl_run(
    logger: logging.Logger,
    source_system: str,
    job_type: str,
    rows_processed: int,
    rows_failed: int,
    status: str,
    error_message: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Log ETL run details in structured format."""
    log_data = {
        "source_system": source_system,
        "job_type": job_type,
        "rows_processed": rows_processed,
        "rows_failed": rows_failed,
        "status": status,
        **kwargs
    }
    
    if error_message:
        log_data["error_message"] = error_message
    
    if status == "success":
        logger.info(f"ETL run completed: {json.dumps(log_data)}")
    elif status == "partial":
        logger.warning(f"ETL run completed with errors: {json.dumps(log_data)}")
    else:
        logger.error(f"ETL run failed: {json.dumps(log_data)}")
    
    return log_data

