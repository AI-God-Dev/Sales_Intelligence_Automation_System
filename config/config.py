"""
Configuration management for Sales Intelligence System.
All sensitive values should be stored in Google Secret Manager.
"""
import os
from typing import Optional
from google.cloud import secretmanager
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and Secret Manager."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "maharani-sales-hub-11-2025")
    gcp_region: str = os.getenv("GCP_REGION", "us-central1")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "sales_intelligence")
    
    # Secret Manager client (instance variable)
    _secret_client: Optional[secretmanager.SecretManagerServiceClient] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._secret_client = None
    
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Retrieve secret from Google Secret Manager.
        
        Args:
            secret_id: Secret identifier
            version: Secret version (default: "latest")
            
        Returns:
            Secret value as string
            
        Raises:
            Exception: If secret retrieval fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if self._secret_client is None:
                self._secret_client = secretmanager.SecretManagerServiceClient()
            
            name = f"projects/{self.gcp_project_id}/secrets/{secret_id}/versions/{version}"
            response = self._secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            error_msg = f"Failed to retrieve secret '{secret_id}' from Secret Manager: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    # API Credentials (loaded from Secret Manager)
    @property
    def salesforce_username(self) -> str:
        try:
            return self.get_secret("salesforce-username")
        except Exception:
            raise Exception("Salesforce username not found in Secret Manager. Please set 'salesforce-username' secret.")
    
    @property
    def salesforce_password(self) -> str:
        try:
            return self.get_secret("salesforce-password")
        except Exception:
            raise Exception("Salesforce password not found in Secret Manager. Please set 'salesforce-password' secret.")
    
    @property
    def salesforce_security_token(self) -> str:
        try:
            return self.get_secret("salesforce-security-token")
        except Exception:
            raise Exception("Salesforce security token not found in Secret Manager. Please set 'salesforce-security-token' secret.")
    
    @property
    def salesforce_domain(self) -> str:
        return os.getenv("SALESFORCE_DOMAIN", "login")
    
    @property
    def dialpad_api_key(self) -> str:
        try:
            return self.get_secret("dialpad-api-key")
        except Exception:
            raise Exception("Dialpad API key not found in Secret Manager. Please set 'dialpad-api-key' secret.")
    
    @property
    def hubspot_api_key(self) -> str:
        try:
            return self.get_secret("hubspot-api-key")
        except Exception:
            raise Exception("HubSpot API key not found in Secret Manager. Please set 'hubspot-api-key' secret.")
    
    @property
    def openai_api_key(self) -> str:
        try:
            return self.get_secret("openai-api-key")
        except Exception:
            return ""  # Optional for Phase 1
    
    @property
    def anthropic_api_key(self) -> str:
        try:
            return self.get_secret("anthropic-api-key")
        except Exception:
            return ""  # Optional for Phase 1
    
    # Gmail OAuth (handled via OAuth flow, not stored)
    gmail_oauth_client_id: str = os.getenv("GMAIL_OAUTH_CLIENT_ID", "")
    gmail_oauth_client_secret: str = os.getenv("GMAIL_OAUTH_CLIENT_SECRET", "")
    
    # LLM Configuration
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic or vertex_ai
    llm_model: str = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Email Configuration
    gmail_mailboxes: list[str] = [
        "anand@maharaniweddings.com",
        # Add other 2 sales rep emails here
    ]
    
    # Sync Configuration
    gmail_sync_interval_minutes: int = 60  # Incremental sync every hour
    salesforce_sync_interval_hours: int = 24  # Daily sync
    dialpad_sync_interval_hours: int = 24  # Daily sync
    scoring_job_schedule: str = "0 7 * * *"  # 7 AM daily (before 8 AM target)
    
    # Data Quality Targets
    email_match_target_percentage: float = 90.0
    call_match_target_percentage: float = 85.0
    hubspot_enrollment_success_target: float = 98.0
    
    # Query Configuration
    max_query_results: int = 100
    query_timeout_seconds: int = 30
    
    # Data Retention
    data_retention_years: int = 3


# Global settings instance
settings = Settings()

