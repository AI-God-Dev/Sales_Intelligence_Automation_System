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
        case_sensitive=False,
        extra="ignore"
    )
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "maharani-sales-hub-11-2025").strip()
    gcp_region: str = os.getenv("GCP_REGION", "us-central1").strip()
    # BigQuery dataset name (must come from env var)
    bigquery_dataset: str = os.getenv("BQ_DATASET_NAME", os.getenv("BIGQUERY_DATASET", "sales_intelligence"))
    
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
            # Ensure project ID is clean (remove any whitespace or extra content)
            project_id = str(self.gcp_project_id).strip()
            if not project_id or " " in project_id:
                # Fallback to environment variable directly if project_id is malformed
                project_id = os.getenv("GCP_PROJECT_ID", "").strip()
                if not project_id:
                    raise Exception(f"Invalid GCP_PROJECT_ID: '{self.gcp_project_id}'. Please set GCP_PROJECT_ID environment variable correctly.")
            
            if self._secret_client is None:
                # Initialize Secret Manager client with explicit project
                self._secret_client = secretmanager.SecretManagerServiceClient()
            
            # Construct secret name with clean project ID
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
            logger.debug(f"Accessing secret: {name}")
            response = self._secret_client.access_secret_version(request={"name": name})
            # Strip whitespace and newlines from secret value
            secret_value = response.payload.data.decode("UTF-8").strip()
            return secret_value
        except Exception as e:
            error_msg = f"Failed to retrieve secret '{secret_id}' from Secret Manager: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    # API Credentials (loaded from Secret Manager)
    # OAuth 2.0 (Preferred - more secure)
    @property
    def salesforce_client_id(self) -> str:
        try:
            return self.get_secret("salesforce-client-id")
        except Exception:
            raise Exception("Salesforce client ID not found in Secret Manager. Please set 'salesforce-client-id' secret.")
    
    @property
    def salesforce_client_secret(self) -> str:
        try:
            return self.get_secret("salesforce-client-secret")
        except Exception:
            raise Exception("Salesforce client secret not found in Secret Manager. Please set 'salesforce-client-secret' secret.")
    
    @property
    def salesforce_refresh_token(self) -> str:
        try:
            return self.get_secret("salesforce-refresh-token")
        except Exception:
            return ""  # Optional - only needed for refresh token flow
    
    @property
    def salesforce_instance_url(self) -> str:
        """Salesforce instance URL (e.g., https://dc0000000qzo7mag.lightning.force.com/)"""
        try:
            return self.get_secret("salesforce-instance-url")
        except Exception:
            return ""  # Optional - only needed for client credentials flow
    
    @property
    def salesforce_domain(self) -> str:
        """Salesforce login domain: 'login' for production, 'test' for sandbox"""
        return os.getenv("SALESFORCE_DOMAIN", "login")
    
    # Legacy username/password (fallback if OAuth not available)
    @property
    def salesforce_username(self) -> str:
        try:
            return self.get_secret("salesforce-username")
        except Exception:
            return ""  # Optional - only used if OAuth not available
    
    @property
    def salesforce_password(self) -> str:
        try:
            return self.get_secret("salesforce-password")
        except Exception:
            return ""  # Optional - only used if OAuth not available
    
    @property
    def salesforce_security_token(self) -> str:
        try:
            return self.get_secret("salesforce-security-token")
        except Exception:
            return ""  # Optional - only used if OAuth not available
    
    @property
    def dialpad_api_key(self) -> str:
        try:
            return self.get_secret("dialpad-api-key")
        except Exception:
            raise Exception("Dialpad API key not found in Secret Manager. Please set 'dialpad-api-key' secret.")
    
    @property
    def hubspot_api_key(self) -> str:
        try:
            api_key = self.get_secret("hubspot-api-key")
            # Check if API key is a placeholder
            if not api_key or api_key.upper() in ["PLACEHOLDER", ""]:
                raise Exception("HubSpot API key is set to PLACEHOLDER. Please update 'hubspot-api-key' secret with a valid HubSpot Private App access token (format: pat-[region]-[token]).")
            return api_key
        except Exception as e:
            if "PLACEHOLDER" in str(e):
                raise
            raise Exception("HubSpot API key not found in Secret Manager. Please set 'hubspot-api-key' secret.")
    
    # OpenAI and Anthropic API keys removed - Vertex AI only
    # Vertex AI uses Application Default Credentials (ADC) - no API keys needed
    
    # Gmail OAuth (handled via OAuth flow, not stored)
    gmail_oauth_client_id: str = os.getenv("GMAIL_OAUTH_CLIENT_ID", "")
    gmail_oauth_client_secret: str = os.getenv("GMAIL_OAUTH_CLIENT_SECRET", "")
    
    # LLM Configuration
    # Vertex AI ONLY - uses Application Default Credentials (ADC) for authentication
    llm_provider: str = os.getenv("LLM_PROVIDER", "vertex_ai")  # Only 'vertex_ai' or 'mock' supported
    llm_model: str = os.getenv("LLM_MODEL", "gemini-1.5-pro")  # Vertex AI: gemini-1.5-pro, gemini-1.5-flash
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "vertex_ai")  # Only 'vertex_ai', 'local', or 'mock' supported
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "textembedding-gecko@001")  # Vertex AI: textembedding-gecko@001
    
    # Local Testing & Mock Mode Configuration
    # MOCK_MODE: Use fake/mock AI responses (for testing without API calls)
    # LOCAL_MODE: Use local implementations (numpy embeddings, SQLite, etc.)
    mock_mode: bool = os.getenv("MOCK_MODE", "0").strip().lower() in ("1", "true", "yes")
    local_mode: bool = os.getenv("LOCAL_MODE", "0").strip().lower() in ("1", "true", "yes")
    
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

