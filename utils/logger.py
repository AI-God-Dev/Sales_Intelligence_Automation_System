"""Logging utilities for Cloud Functions and ETL jobs."""
import logging
import json
import os
from typing import Any, Dict, Optional
from datetime import datetime
from google.cloud import logging as cloud_logging


class StructuredLogger:
    """Production-grade structured logger with Cloud Logging integration."""
    
    def __init__(self, name: str, project_id: Optional[str] = None):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            project_id: GCP project ID (optional, will try to detect)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        
        # Set up Cloud Logging if available
        if self.project_id:
            try:
                client = cloud_logging.Client(project=self.project_id)
                client.setup_logging()
            except Exception as e:
                # Fallback to standard logging
                if not self.logger.handlers:
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
        else:
            # Standard logging if no project ID
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
    
    def log_structured(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ):
        """
        Log with structured data.
        
        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            **kwargs: Additional structured fields
        """
        log_entry = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": level.upper(),
            **kwargs
        }
        
        getattr(self.logger, level.lower())(json.dumps(log_entry))
    
    def log_api_call(
        self,
        api_name: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Log API calls with standardized format.
        
        Args:
            api_name: Name of the API/service
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            error: Optional error message
            **kwargs: Additional context
        """
        log_data = {
            "api_name": api_name,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        }
        
        if error:
            log_data["error"] = error
        
        level = "info" if status_code < 400 else "error"
        self.log_structured(
            level,
            f"API call: {api_name}",
            **log_data
        )


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

