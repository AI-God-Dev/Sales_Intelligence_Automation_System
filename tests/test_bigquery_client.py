"""Unit tests for BigQuery client."""
import pytest
from unittest.mock import Mock, patch
from utils.bigquery_client import BigQueryClient


class TestBigQueryClient:
    """Test BigQuery client operations."""
    
    @patch('utils.bigquery_client.bigquery.Client')
    def test_init(self, mock_client):
        client = BigQueryClient(project_id="test-project", dataset_id="test_dataset")
        assert client.project_id == "test-project"
        assert client.dataset_id == "test_dataset"
        mock_client.assert_called_once_with(project="test-project")
    
    @patch('utils.bigquery_client.bigquery.Client')
    def test_insert_rows_success(self, mock_client):
        client = BigQueryClient()
        mock_bq_client = mock_client.return_value
        mock_bq_client.insert_rows_json.return_value = []
        
        rows = [{"id": "1", "name": "Test"}]
        result = client.insert_rows("test_table", rows)
        
        assert result == 1
        mock_bq_client.insert_rows_json.assert_called_once()
    
    @patch('utils.bigquery_client.bigquery.Client')
    def test_insert_rows_error(self, mock_client):
        client = BigQueryClient()
        mock_bq_client = mock_client.return_value
        mock_bq_client.insert_rows_json.return_value = [{"error": "test error"}]
        
        rows = [{"id": "1", "name": "Test"}]
        
        with pytest.raises(ValueError):
            client.insert_rows("test_table", rows)

