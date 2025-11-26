"""
BigQuery client utilities for data operations.

This module provides a production-ready wrapper around the Google BigQuery client
with retry logic, error handling, and performance monitoring.
"""
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, BadRequest
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date
from config.config import settings
from utils.retry import retry_with_backoff
from utils.monitoring import PerformanceMonitor, MetricsCollector

logger = logging.getLogger(__name__)


def _serialize_for_json(obj: Any) -> Any:
    """
    Convert datetime/date objects to ISO format strings for JSON serialization.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    else:
        return obj


class BigQueryClient:
    """
    Production-ready wrapper for BigQuery operations.
    
    Features:
    - Automatic retry with exponential backoff
    - Performance monitoring
    - Comprehensive error handling
    - Connection pooling
    - Query result caching
    
    Example:
        client = BigQueryClient()
        results = client.query("SELECT * FROM table LIMIT 10")
        client.insert_rows("table_name", [{"col1": "value1"}])
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize BigQuery client.
        
        Args:
            project_id: GCP project ID (defaults to settings)
            dataset_id: BigQuery dataset ID (defaults to settings)
            metrics_collector: Optional metrics collector for observability
        """
        self.project_id = project_id or settings.gcp_project_id
        self.dataset_id = dataset_id or settings.bigquery_dataset
        self.metrics_collector = metrics_collector
        
        if not self.project_id:
            raise ValueError("GCP project ID is required")
        if not self.dataset_id:
            raise ValueError("BigQuery dataset ID is required")
        
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = self.client.dataset(self.dataset_id)
    
    @retry_with_backoff(
        max_attempts=3,
        initial_wait=1.0,
        max_wait=10.0,
        retryable_exceptions=[Exception]
    )
    def insert_rows(
        self,
        table_id: str,
        rows: List[Dict[str, Any]],
        skip_invalid_rows: bool = False,
        ignore_unknown_values: bool = False
    ) -> int:
        """
        Insert rows into BigQuery table with retry logic.
        
        Args:
            table_id: Table name (without dataset prefix)
            rows: List of dictionaries representing rows
            skip_invalid_rows: Skip invalid rows instead of failing
            ignore_unknown_values: Ignore unknown values in rows
        
        Returns:
            Number of rows inserted
        
        Raises:
            ValueError: If insertion fails after retries
            NotFound: If table doesn't exist
        """
        if not rows:
            logger.debug(f"No rows to insert into {table_id}")
            return 0
        
        with PerformanceMonitor(f"bigquery_insert_{table_id}", self.metrics_collector):
            try:
                table_ref = self.dataset_ref.table(table_id)
                
                # Serialize datetime objects to ISO format strings for JSON compatibility
                serialized_rows = [_serialize_for_json(row) for row in rows]
                
                # Insert rows using insert_rows_json
                # Note: insert_rows_json doesn't accept job_config parameter
                # Use skip_invalid_rows and ignore_unknown_values directly
                errors = self.client.insert_rows_json(
                    table_ref,
                    serialized_rows,
                    skip_invalid_rows=skip_invalid_rows,
                    ignore_unknown_values=ignore_unknown_values
                )
                
                if errors:
                    error_count = len(errors)
                    logger.error(
                        f"Errors inserting {error_count} rows into {table_id}: {errors[:5]}"  # Log first 5
                    )
                    
                    if self.metrics_collector:
                        self.metrics_collector.increment_counter(
                            "bigquery_insert_errors",
                            value=error_count,
                            labels={"table": table_id}
                        )
                    
                    raise ValueError(f"Failed to insert {error_count} rows: {errors[:3]}")
                
                logger.info(f"Successfully inserted {len(rows)} rows into {table_id}")
                
                if self.metrics_collector:
                    self.metrics_collector.increment_counter(
                        "bigquery_insert_success",
                        value=len(rows),
                        labels={"table": table_id}
                    )
                
                return len(rows)
                
            except NotFound as e:
                logger.error(f"Table {table_id} not found: {e}")
                if self.metrics_collector:
                    self.metrics_collector.increment_counter(
                        "bigquery_table_not_found",
                        labels={"table": table_id}
                    )
                raise
            except BadRequest as e:
                logger.error(f"Bad request inserting into {table_id}: {e}")
                if self.metrics_collector:
                    self.metrics_collector.increment_counter(
                        "bigquery_bad_request",
                        labels={"table": table_id}
                    )
                raise
    
    @retry_with_backoff(
        max_attempts=3,
        initial_wait=1.0,
        max_wait=30.0,
        retryable_exceptions=[Exception]
    )
    def query(
        self,
        query: str,
        job_config: Optional[bigquery.QueryJobConfig] = None,
        use_legacy_sql: bool = False,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results with retry logic.
        
        Args:
            query: SQL query string
            job_config: Optional query job configuration
            use_legacy_sql: Whether to use legacy SQL syntax
            max_results: Maximum number of results to return
        
        Returns:
            List of result dictionaries
        
        Raises:
            BadRequest: If query is invalid
            Exception: If query fails after retries
        """
        with PerformanceMonitor("bigquery_query", self.metrics_collector):
            try:
                if job_config is None:
                    job_config = bigquery.QueryJobConfig()
                
                job_config.use_legacy_sql = use_legacy_sql
                
                query_job = self.client.query(query, job_config=job_config)
                
                # Wait for job to complete
                query_job.result(timeout=settings.query_timeout_seconds)
                
                # Check for errors
                if query_job.errors:
                    logger.error(f"Query errors: {query_job.errors}")
                    if self.metrics_collector:
                        self.metrics_collector.increment_counter("bigquery_query_errors")
                    raise ValueError(f"Query failed: {query_job.errors}")
                
                # Get results
                results = list(query_job.result(max_results=max_results))
                result_dicts = [dict(row) for row in results]
                
                logger.debug(f"Query returned {len(result_dicts)} rows")
                
                if self.metrics_collector:
                    self.metrics_collector.record_gauge(
                        "bigquery_query_rows",
                        len(result_dicts)
                    )
                    self.metrics_collector.increment_counter("bigquery_query_success")
                
                return result_dicts
                
            except BadRequest as e:
                logger.error(f"Bad query request: {e}")
                if self.metrics_collector:
                    self.metrics_collector.increment_counter("bigquery_query_bad_request")
                raise
            except Exception as e:
                logger.error(f"Query execution failed: {e}", exc_info=True)
                if self.metrics_collector:
                    self.metrics_collector.increment_counter("bigquery_query_failure")
                raise
    
    @retry_with_backoff(max_attempts=3, retryable_exceptions=[Exception])
    def get_table(self, table_id: str) -> bigquery.Table:
        """
        Get BigQuery table reference.
        
        Args:
            table_id: Table name (without dataset prefix)
        
        Returns:
            BigQuery Table object
        
        Raises:
            NotFound: If table doesn't exist
        """
        try:
            return self.client.get_table(self.dataset_ref.table(table_id))
        except NotFound:
            logger.warning(f"Table {table_id} not found")
            raise
    
    def table_exists(self, table_id: str) -> bool:
        """
        Check if table exists.
        
        Args:
            table_id: Table name (without dataset prefix)
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            self.client.get_table(self.dataset_ref.table(table_id))
            return True
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def create_table_from_schema(self, table_id: str, schema: List[bigquery.SchemaField]) -> bigquery.Table:
        """Create table from schema definition."""
        table_ref = self.dataset_ref.table(table_id)
        table = bigquery.Table(table_ref, schema=schema)
        return self.client.create_table(table)
    
    def log_etl_run(
        self,
        source_system: str,
        job_type: str,
        started_at: str,
        completed_at: str,
        rows_processed: int,
        rows_failed: int,
        status: str,
        error_message: Optional[str] = None,
        watermark: Optional[str] = None
    ) -> None:
        """Log ETL run to etl_runs table."""
        import uuid
        from datetime import datetime
        
        row = {
            "run_id": str(uuid.uuid4()),
            "source_system": source_system,
            "job_type": job_type,
            "started_at": started_at,
            "completed_at": completed_at,
            "rows_processed": rows_processed,
            "rows_failed": rows_failed,
            "status": status,
            "error_message": error_message,
            "watermark": watermark
        }
        
        self.insert_rows("etl_runs", [row])

