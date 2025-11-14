"""
Integration tests for data ingestion pipelines.
These tests verify end-to-end data flow.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
class TestGmailIngestionFlow:
    """Integration tests for Gmail ingestion."""
    
    @patch('cloud_functions.gmail_sync.main.get_gmail_service_for_user')
    @patch('cloud_functions.gmail_sync.main.BigQueryClient')
    def test_full_gmail_sync_flow(self, mock_bq, mock_gmail_service):
        """Test complete Gmail sync flow from API to BigQuery."""
        # Setup
        mock_service = Mock()
        mock_gmail_service.return_value = mock_service
        
        mock_bq_instance = Mock()
        mock_bq.return_value = mock_bq_instance
        
        # Mock Gmail API
        mock_service.users().getProfile().execute.return_value = {"historyId": "12345"}
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}],
            "nextPageToken": None
        }
        mock_service.users().messages().get().execute.side_effect = [
            {
                "id": "msg1",
                "threadId": "thread1",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "sender@example.com"},
                        {"name": "Subject", "value": "Test 1"}
                    ],
                    "body": {"data": "SGVsbG8="}
                }
            },
            {
                "id": "msg2",
                "threadId": "thread2",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "sender2@example.com"},
                        {"name": "Subject", "value": "Test 2"}
                    ],
                    "body": {"data": "SGVsbG8gV29ybGQ="}
                }
            }
        ]
        
        # Execute
        from cloud_functions.gmail_sync.main import gmail_sync
        request = Mock()
        request.get_json.return_value = {
            "mailbox_email": "test@example.com",
            "sync_type": "full"
        }
        
        response, status = gmail_sync(request)
        
        # Verify
        assert status == 200
        assert mock_bq_instance.insert_rows.called
        assert mock_bq_instance.log_etl_run.called


@pytest.mark.integration
class TestSalesforceIngestionFlow:
    """Integration tests for Salesforce ingestion."""
    
    @patch('cloud_functions.salesforce_sync.main.Salesforce')
    @patch('cloud_functions.salesforce_sync.main.BigQueryClient')
    @patch('cloud_functions.salesforce_sync.main.settings')
    def test_full_salesforce_sync_flow(self, mock_settings, mock_bq, mock_sf):
        """Test complete Salesforce sync flow."""
        # Setup
        mock_sf_instance = Mock()
        mock_sf.return_value = mock_sf_instance
        mock_sf_instance.query_all.return_value = {
            "records": [
                {
                    "Id": "0011234567890ABC",
                    "Name": "Test Account",
                    "Website": "https://test.com"
                }
            ],
            "totalSize": 1
        }
        
        mock_bq_instance = Mock()
        mock_bq.return_value = mock_bq_instance
        mock_bq_instance.query.return_value = []
        
        # Execute
        from cloud_functions.salesforce_sync.main import salesforce_sync
        request = Mock()
        request.get_json.return_value = {
            "object_type": "Account",
            "sync_type": "incremental"
        }
        
        response, status = salesforce_sync(request)
        
        # Verify
        assert status == 200
        assert mock_bq_instance.insert_rows.called
        assert mock_bq_instance.log_etl_run.called


@pytest.mark.integration
class TestEntityResolutionFlow:
    """Integration tests for entity resolution."""
    
    @patch('entity_resolution.matcher.BigQueryClient')
    def test_email_to_contact_resolution(self, mock_bq):
        """Test email to contact resolution flow."""
        from entity_resolution.matcher import EntityMatcher
        
        mock_bq_instance = Mock()
        mock_bq.return_value = mock_bq_instance
        mock_bq_instance.project_id = "test-project"
        mock_bq_instance.dataset_id = "test_dataset"
        
        # Mock: Unmatched participants query
        mock_bq_instance.query.side_effect = [
            [{"participant_id": "p1", "email_address": "test@example.com"}],
            [{"contact_id": "0031234567890ABC", "account_id": "0011234567890ABC", "email": "test@example.com"}]
        ]
        
        matcher = EntityMatcher(mock_bq_instance)
        stats = matcher.update_participant_matches(batch_size=100)
        
        assert stats["matched"] == 1
        assert stats["processed"] == 1


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""
    
    @patch('cloud_functions.gmail_sync.main.get_gmail_service_for_user')
    @patch('cloud_functions.gmail_sync.main.publish_error_notification')
    def test_gmail_sync_error_notification(self, mock_publish, mock_gmail_service):
        """Test that errors are properly published to Pub/Sub."""
        mock_gmail_service.side_effect = Exception("Gmail API Error")
        
        from cloud_functions.gmail_sync.main import gmail_sync
        request = Mock()
        request.get_json.return_value = {
            "mailbox_email": "test@example.com",
            "sync_type": "incremental"
        }
        
        response, status = gmail_sync(request)
        
        assert status == 500
        assert mock_publish.called

