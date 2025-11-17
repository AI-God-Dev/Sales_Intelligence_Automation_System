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
        """Retrieve secret from Google Secret Manager."""
        if self._secret_client is None:
            self._secret_client = secretmanager.SecretManagerServiceClient()
        
        name = f"projects/{self.gcp_project_id}/secrets/{secret_id}/versions/{version}"
        response = self._secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    
    # API Credentials (loaded from Secret Manager)
    @property
    def salesforce_username(self) -> str:
        return self.get_secret("salesforce-username")
    
    @property
    def salesforce_password(self) -> str:
        return self.get_secret("salesforce-password")
    
    @property
    def salesforce_security_token(self) -> str:
        return self.get_secret("salesforce-security-token")
    
    @property
    def salesforce_domain(self) -> str:
        return os.getenv("SALESFORCE_DOMAIN", "login")
    
    @property
    def dialpad_api_key(self) -> str:
        return self.get_secret("dialpad-api-key")
    
    @property
    def hubspot_api_key(self) -> str:
        return self.get_secret("hubspot-api-key")
    
    @property
    def openai_api_key(self) -> str:
        return self.get_secret("openai-api-key")
    
    @property
    def anthropic_api_key(self) -> str:
        return self.get_secret("anthropic-api-key")
    
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

