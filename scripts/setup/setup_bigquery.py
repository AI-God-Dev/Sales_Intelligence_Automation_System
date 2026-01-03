"""
BigQuery Schema Setup
Creates BigQuery tables for storing data from Gmail, Salesforce, Dialpad, and HubSpot.
Uses service account (sales-intel-poc-sa) for authentication.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
# from utils.secret_manager import get_secret_client  # Not needed for this script

logger = logging.getLogger(__name__)


class BigQuerySchemaManager:
    """
    Manager for creating and managing BigQuery tables and schemas.
    """
    
    def __init__(self, project_id: Optional[str] = None, dataset_id: str = "sales_intelligence"):
        """
        Initialize BigQuery schema manager.
        
        Args:
            project_id: GCP project ID. If not provided, uses environment or defaults.
            dataset_id: BigQuery dataset ID (default: sales_intelligence)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "maharani-sales-hub-11-2025")
        if not self.project_id:
            raise ValueError("GCP project ID is required. Set GCP_PROJECT_ID environment variable.")
        
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = self.client.dataset(self.dataset_id)
        
        logger.info(f"Initialized BigQuery manager for project: {self.project_id}, dataset: {self.dataset_id}")
    
    def create_dataset_if_not_exists(self) -> bigquery.Dataset:
        """
        Create BigQuery dataset if it doesn't exist.
        
        Returns:
            Dataset object
        """
        try:
            dataset = self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
            return dataset
        except NotFound:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"  # Set location
            dataset.description = "Sales Intelligence data warehouse"
            dataset = self.client.create_dataset(dataset, exists_ok=True)
            logger.info(f"Created dataset: {self.dataset_id}")
            return dataset
    
    def create_table(self, table_id: str, schema: List[bigquery.SchemaField], description: Optional[str] = None) -> bigquery.Table:
        """
        Create a BigQuery table with the specified schema.
        
        Args:
            table_id: Name of the table
            schema: List of SchemaField objects defining the table schema
            description: Optional table description
        
        Returns:
            Created table object
        """
        table_ref = self.dataset_ref.table(table_id)
        
        try:
            # Check if table exists
            try:
                table = self.client.get_table(table_ref)
                logger.info(f"Table {table_id} already exists")
                return table
            except NotFound:
                pass
            
            # Create table
            table = bigquery.Table(table_ref, schema=schema)
            if description:
                table.description = description
            
            table = self.client.create_table(table)
            logger.info(f"Successfully created table: {table_id}")
            return table
            
        except Exception as e:
            logger.error(f"Error creating table {table_id}: {e}")
            raise
    
    def get_gmail_messages_schema(self) -> List[bigquery.SchemaField]:
        """Get schema for Gmail messages table."""
        return [
            bigquery.SchemaField("message_id", "STRING", mode="REQUIRED", description="Gmail message ID"),
            bigquery.SchemaField("thread_id", "STRING", description="Gmail thread ID"),
            bigquery.SchemaField("mailbox_email", "STRING", mode="REQUIRED", description="Email address of mailbox"),
            bigquery.SchemaField("from_email", "STRING", description="Sender email address"),
            bigquery.SchemaField("to_emails", "STRING", mode="REPEATED", description="Recipient email addresses"),
            bigquery.SchemaField("cc_emails", "STRING", mode="REPEATED", description="CC email addresses"),
            bigquery.SchemaField("subject", "STRING", description="Email subject"),
            bigquery.SchemaField("body_text", "STRING", description="Plain text body"),
            bigquery.SchemaField("body_html", "STRING", description="HTML body"),
            bigquery.SchemaField("sent_at", "TIMESTAMP", description="Email sent timestamp"),
            bigquery.SchemaField("labels", "STRING", mode="REPEATED", description="Gmail labels"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED", description="Ingestion timestamp")
        ]
    
    def get_sf_accounts_schema(self) -> List[bigquery.SchemaField]:
        """Get schema for Salesforce accounts table."""
        return [
            bigquery.SchemaField("account_id", "STRING", mode="REQUIRED", description="Salesforce Account ID"),
            bigquery.SchemaField("account_name", "STRING", description="Account name"),
            bigquery.SchemaField("website", "STRING", description="Account website"),
            bigquery.SchemaField("industry", "STRING", description="Industry"),
            bigquery.SchemaField("annual_revenue", "FLOAT", description="Annual revenue"),
            bigquery.SchemaField("owner_id", "STRING", description="Owner ID"),
            bigquery.SchemaField("created_date", "TIMESTAMP", description="Created date"),
            bigquery.SchemaField("last_modified_date", "TIMESTAMP", description="Last modified date"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED", description="Ingestion timestamp")
        ]
    
    def get_dialpad_calls_schema(self) -> List[bigquery.SchemaField]:
        """Get schema for Dialpad calls table."""
        return [
            bigquery.SchemaField("call_id", "STRING", mode="REQUIRED", description="Dialpad call ID"),
            bigquery.SchemaField("direction", "STRING", description="Call direction (inbound/outbound)"),
            bigquery.SchemaField("from_number", "STRING", description="Caller phone number"),
            bigquery.SchemaField("to_number", "STRING", description="Recipient phone number"),
            bigquery.SchemaField("duration_seconds", "INTEGER", description="Call duration in seconds"),
            bigquery.SchemaField("transcript_text", "STRING", description="Call transcription"),
            bigquery.SchemaField("sentiment_score", "FLOAT", description="Sentiment score"),
            bigquery.SchemaField("call_time", "TIMESTAMP", description="Call timestamp"),
            bigquery.SchemaField("user_id", "STRING", description="Dialpad user ID"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED", description="Ingestion timestamp")
        ]
    
    def get_hubspot_sequences_schema(self) -> List[bigquery.SchemaField]:
        """Get schema for HubSpot sequences table."""
        return [
            bigquery.SchemaField("sequence_id", "STRING", mode="REQUIRED", description="HubSpot sequence ID"),
            bigquery.SchemaField("sequence_name", "STRING", description="Sequence name"),
            bigquery.SchemaField("is_active", "BOOLEAN", description="Whether sequence is active"),
            bigquery.SchemaField("enrollment_count", "INTEGER", description="Number of enrollments"),
            bigquery.SchemaField("last_synced", "TIMESTAMP", description="Last sync timestamp")
        ]


def setup_all_tables(project_id: Optional[str] = None, dataset_id: str = "sales_intelligence") -> Dict[str, Any]:
    """
    Set up all BigQuery tables for the sales intelligence system.
    
    Args:
        project_id: Optional GCP project ID override
        dataset_id: BigQuery dataset ID
    
    Returns:
        Dictionary with created tables information
    """
    manager = BigQuerySchemaManager(project_id, dataset_id)
    
    # Create dataset first
    manager.create_dataset_if_not_exists()
    
    # Define all tables
    tables_config = [
        {
            "table_id": "gmail_messages",
            "schema": manager.get_gmail_messages_schema(),
            "description": "Gmail messages from all mailboxes"
        },
        {
            "table_id": "sf_accounts",
            "schema": manager.get_sf_accounts_schema(),
            "description": "Salesforce accounts"
        },
        {
            "table_id": "sf_contacts",
            "schema": [
                bigquery.SchemaField("contact_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("account_id", "STRING"),
                bigquery.SchemaField("first_name", "STRING"),
                bigquery.SchemaField("last_name", "STRING"),
                bigquery.SchemaField("email", "STRING"),
                bigquery.SchemaField("phone", "STRING"),
                bigquery.SchemaField("mobile_phone", "STRING"),
                bigquery.SchemaField("title", "STRING"),
                bigquery.SchemaField("created_date", "TIMESTAMP"),
                bigquery.SchemaField("last_modified_date", "TIMESTAMP"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED")
            ],
            "description": "Salesforce contacts"
        },
        {
            "table_id": "sf_leads",
            "schema": [
                bigquery.SchemaField("lead_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("first_name", "STRING"),
                bigquery.SchemaField("last_name", "STRING"),
                bigquery.SchemaField("email", "STRING"),
                bigquery.SchemaField("company", "STRING"),
                bigquery.SchemaField("phone", "STRING"),
                bigquery.SchemaField("title", "STRING"),
                bigquery.SchemaField("lead_source", "STRING"),
                bigquery.SchemaField("status", "STRING"),
                bigquery.SchemaField("owner_id", "STRING"),
                bigquery.SchemaField("created_date", "TIMESTAMP"),
                bigquery.SchemaField("last_modified_date", "TIMESTAMP"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED")
            ],
            "description": "Salesforce leads"
        },
        {
            "table_id": "sf_opportunities",
            "schema": [
                bigquery.SchemaField("opportunity_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("account_id", "STRING"),
                bigquery.SchemaField("name", "STRING"),
                bigquery.SchemaField("stage", "STRING"),
                bigquery.SchemaField("amount", "FLOAT"),
                bigquery.SchemaField("close_date", "DATE"),
                bigquery.SchemaField("probability", "FLOAT"),
                bigquery.SchemaField("owner_id", "STRING"),
                bigquery.SchemaField("is_closed", "BOOLEAN"),
                bigquery.SchemaField("is_won", "BOOLEAN"),
                bigquery.SchemaField("created_date", "TIMESTAMP"),
                bigquery.SchemaField("last_modified_date", "TIMESTAMP"),
                bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED")
            ],
            "description": "Salesforce opportunities"
        },
        {
            "table_id": "dialpad_calls",
            "schema": manager.get_dialpad_calls_schema(),
            "description": "Dialpad call logs and transcriptions"
        },
        {
            "table_id": "hubspot_sequences",
            "schema": manager.get_hubspot_sequences_schema(),
            "description": "HubSpot sequences metadata"
        }
    ]
    
    created_tables = {}
    
    for table_config in tables_config:
        table_id = table_config["table_id"]
        try:
            table = manager.create_table(
                table_id,
                table_config["schema"],
                table_config.get("description")
            )
            created_tables[table_id] = {
                "name": table_id,
                "status": "created" if hasattr(table, 'table_id') else "exists",
                "num_rows": table.num_rows if hasattr(table, 'num_rows') else 0
            }
        except Exception as e:
            logger.error(f"Failed to create table {table_id}: {e}")
            created_tables[table_id] = {
                "name": table_id,
                "status": "error",
                "error": str(e)
            }
    
    return created_tables


def main():
    """
    Main function to set up all BigQuery tables.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Get project ID from environment or use default
    project_id = os.getenv("GCP_PROJECT_ID", "maharani-sales-hub-11-2025")
    dataset_id = os.getenv("BQ_DATASET_NAME") or os.getenv("BIGQUERY_DATASET", "sales_intelligence")
    
    print("=" * 60)
    print("Setting up BigQuery Tables for Sales Intelligence")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Dataset: {dataset_id}")
    
    # Set up all tables
    print("\nCreating tables...")
    tables = setup_all_tables(project_id=project_id, dataset_id=dataset_id)
    
    for table_name, info in tables.items():
        status = info.get("status", "unknown")
        print(f"  {table_name}: {status}")
        if status == "error":
            print(f"    Error: {info.get('error', 'Unknown error')}")
        elif status == "exists":
            print(f"    Rows: {info.get('num_rows', 0)}")
    
    print("\n" + "=" * 60)
    print("BigQuery setup completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

