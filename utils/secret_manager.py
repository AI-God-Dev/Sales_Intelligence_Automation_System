"""
Google Cloud Secret Manager Integration
Securely retrieves API credentials from Secret Manager at runtime.
"""
import os
import logging
from typing import Optional, Dict, Any
from google.cloud import secretmanager
from google.api_core import exceptions

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """
    Client for securely accessing secrets from Google Cloud Secret Manager.
    
    All secrets are fetched dynamically at runtime, never hardcoded.
    Uses environment variables or metadata for project ID.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Secret Manager client.
        
        Args:
            project_id: GCP project ID. If not provided, will try:
                1. GCP_PROJECT_ID environment variable
                2. GCP project from metadata service
        """
        self.project_id = project_id or self._get_project_id()
        if not self.project_id:
            raise ValueError(
                "Project ID is required. Set GCP_PROJECT_ID environment variable "
                "or ensure running in GCP environment with metadata service."
            )
        
        self.client = secretmanager.SecretManagerServiceClient()
        logger.info(f"Initialized Secret Manager client for project: {self.project_id}")
    
    def _get_project_id(self) -> Optional[str]:
        """Get project ID from environment or metadata service."""
        # Try environment variable first
        project_id = os.getenv("GCP_PROJECT_ID")
        if project_id:
            return project_id
        
        # Try metadata service (when running in GCP)
        try:
            import requests
            metadata_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
            headers = {"Metadata-Flavor": "Google"}
            response = requests.get(metadata_url, headers=headers, timeout=2)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        
        return None
    
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Retrieve a secret from Secret Manager.
        
        Args:
            secret_id: Name of the secret (without project path)
            version: Secret version (default: "latest")
        
        Returns:
            Secret value as string
        
        Raises:
            NotFound: If secret doesn't exist
            PermissionDenied: If service account lacks permissions
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        
        try:
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            logger.debug(f"Successfully retrieved secret: {secret_id}")
            return secret_value
        except exceptions.NotFound:
            logger.error(f"Secret not found: {secret_id}")
            raise
        except exceptions.PermissionDenied:
            logger.error(f"Permission denied accessing secret: {secret_id}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_id}: {e}")
            raise
    
    def get_secret_json(self, secret_id: str, version: str = "latest") -> Dict[str, Any]:
        """
        Retrieve a JSON secret and parse it.
        
        Args:
            secret_id: Name of the secret
            version: Secret version (default: "latest")
        
        Returns:
            Parsed JSON as dictionary
        """
        import json
        secret_value = self.get_secret(secret_id, version)
        try:
            return json.loads(secret_value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON secret {secret_id}: {e}")
            raise ValueError(f"Secret {secret_id} is not valid JSON") from e


# Global instance
_secret_client: Optional[SecretManagerClient] = None


def get_secret_client(project_id: Optional[str] = None) -> SecretManagerClient:
    """Get or create global Secret Manager client instance."""
    global _secret_client
    if _secret_client is None:
        _secret_client = SecretManagerClient(project_id)
    return _secret_client


def get_hubspot_access_token(project_id: Optional[str] = None) -> str:
    """Retrieve HubSpot access token from Secret Manager."""
    client = get_secret_client(project_id)
    return client.get_secret("hubspot_access_token")


def get_gmail_oauth_credentials(user: str = "anand", project_id: Optional[str] = None) -> Dict[str, str]:
    """
    Retrieve Gmail OAuth credentials for a specific user.
    
    Args:
        user: User name (anand, larnie, or lia)
        project_id: Optional project ID override
    
    Returns:
        Dictionary with client_id, client_secret, and refresh_token
    """
    client = get_secret_client(project_id)
    
    # Secret names follow pattern: gmail_oauth_client_id_{user}
    client_id = client.get_secret(f"gmail_oauth_client_id_{user}")
    client_secret = client.get_secret(f"gmail_oauth_client_secret_{user}")
    refresh_token = client.get_secret(f"gmail_oauth_refresh_token_{user}")
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }


def get_salesforce_credentials(project_id: Optional[str] = None) -> Dict[str, str]:
    """
    Retrieve Salesforce OAuth credentials from Secret Manager.
    
    Returns:
        Dictionary with client_id, client_secret, and refresh_token
    """
    client = get_secret_client(project_id)
    
    return {
        "client_id": client.get_secret("salesforce_client_id"),
        "client_secret": client.get_secret("salesforce_client_secret"),
        "refresh_token": client.get_secret("salesforce_refresh_token")
    }


def get_dialpad_api_key(project_id: Optional[str] = None) -> str:
    """Retrieve Dialpad API key from Secret Manager."""
    client = get_secret_client(project_id)
    return client.get_secret("dialpad_api_key")


# Example usage function
def example_usage():
    """
    Example demonstrating how to retrieve and use secrets.
    """
    # Initialize client
    secret_client = SecretManagerClient()
    
    # Retrieve HubSpot access token
    hubspot_token = get_hubspot_access_token()
    print(f"HubSpot token retrieved: {hubspot_token[:10]}...")
    
    # Retrieve Gmail OAuth credentials for Anand
    gmail_creds = get_gmail_oauth_credentials("anand")
    print(f"Gmail client ID: {gmail_creds['client_id'][:20]}...")
    
    # Retrieve Salesforce credentials
    sf_creds = get_salesforce_credentials()
    print(f"Salesforce client ID: {sf_creds['client_id'][:20]}...")
    
    # Retrieve Dialpad API key
    dialpad_key = get_dialpad_api_key()
    print(f"Dialpad API key retrieved: {dialpad_key[:10]}...")


if __name__ == "__main__":
    # Run example
    example_usage()

