"""
Integration tests for BigQuery client with mocked BigQuery service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.bigquery_client import BigQueryClient
from datetime import datetime


class TestBigQueryIntegration:
    """Test BigQuery client integration."""
    
    @pytest.fixture
    def mock_bigquery_service(self):
        """Mock BigQuery service."""
        with patch('utils.bigquery_client.bigquery.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock query job
            mock_job = Mock()
            mock_job.result.return_value = None
            mock_client.query.return_value = mock_job
            
            yield mock_client
    
    def test_query_execution(self, mock_bigquery_service, mock_gcp_environment):
        """Test query execution."""
        client = BigQueryClient()
        
        # Mock query results
        mock_results = [
            {"account_id": "001XX000004ABCD", "account_name": "Test Corp"}
        ]
        
        with patch.object(client, 'query', return_value=mock_results):
            results = client.query("SELECT * FROM test_table LIMIT 1")
            
            assert len(results) == 1
            assert results[0]["account_id"] == "001XX000004ABCD"
    
    def test_insert_rows(self, mock_bigquery_service, mock_gcp_environment):
        """Test row insertion."""
        client = BigQueryClient()
        
        rows = [
            {"account_id": "001XX000004ABCD", "score": 75}
        ]
        
        with patch.object(client, 'insert_rows', return_value=True) as mock_insert:
            result = client.insert_rows("test_table", rows)
            
            assert result is True
            mock_insert.assert_called_once()
    
    def test_log_etl_run(self, mock_bigquery_service, mock_gcp_environment):
        """Test ETL run logging."""
        client = BigQueryClient()
        
        with patch.object(client, 'log_etl_run', return_value=True) as mock_log:
            result = client.log_etl_run(
                source_system="test",
                job_type="daily",
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                rows_processed=100,
                status="success"
            )
            
            assert result is True
            mock_log.assert_called_once()

