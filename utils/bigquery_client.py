"""BigQuery client utilities for data operations."""
from google.cloud import bigquery
from typing import List, Dict, Any, Optional
import logging
from config.config import settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Wrapper for BigQuery operations."""
    
    def __init__(self, project_id: str = None, dataset_id: str = None):
        self.project_id = project_id or settings.gcp_project_id
        self.dataset_id = dataset_id or settings.bigquery_dataset
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = self.client.dataset(self.dataset_id)
    
    def insert_rows(self, table_id: str, rows: List[Dict[str, Any]]) -> int:
        """
        Insert rows into BigQuery table.
        
        Args:
            table_id: Table name (without dataset prefix)
            rows: List of dictionaries representing rows
        
        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0
        
        table_ref = self.dataset_ref.table(table_id)
        errors = self.client.insert_rows_json(table_ref, rows)
        
        if errors:
            logger.error(f"Errors inserting rows into {table_id}: {errors}")
            raise ValueError(f"Failed to insert rows: {errors}")
        
        return len(rows)
    
    def query(self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            job_config: Optional query job configuration
        
        Returns:
            List of result dictionaries
        """
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def get_table(self, table_id: str) -> bigquery.Table:
        """Get BigQuery table reference."""
        return self.client.get_table(self.dataset_ref.table(table_id))
    
    def table_exists(self, table_id: str) -> bool:
        """Check if table exists."""
        try:
            self.client.get_table(self.dataset_ref.table(table_id))
            return True
        except Exception:
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

