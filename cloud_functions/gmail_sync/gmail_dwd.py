"""
Gmail Domain-Wide Delegation (DWD) utilities.
Allows service account to impersonate users without OAuth tokens.
"""
import logging
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from config.config import settings

logger = logging.getLogger(__name__)

# Gmail API scopes for domain-wide delegation
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]


def get_gmail_service_for_user(
    user_email: str,
    service_account_file: Optional[str] = None
):
    """
    Get Gmail API service for a user using domain-wide delegation.
    
    Args:
        user_email: Email address of the user to impersonate
        service_account_file: Path to service account JSON key file (optional, uses default credentials if not provided)
    
    Returns:
        Gmail API service instance
    """
    try:
        # Get service account credentials
        if service_account_file:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=GMAIL_SCOPES
            )
        else:
            # Use default credentials (when running in Cloud Functions)
            from google.auth import default
            credentials, _ = default(scopes=GMAIL_SCOPES)
        
        # Delegate domain-wide authority to impersonate the user
        delegated_credentials = credentials.with_subject(user_email)
        
        # Build Gmail API service
        service = build('gmail', 'v1', credentials=delegated_credentials)
        
        logger.info(f"Successfully created Gmail service for user: {user_email}")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Gmail service for {user_email}: {str(e)}", exc_info=True)
        raise


def get_gmail_service_with_oauth_client(
    user_email: str,
    client_id: str,
    client_secret: str
):
    """
    Alternative method: Get Gmail service using OAuth client credentials with DWD.
    
    This method uses the OAuth client ID/secret from Secret Manager
    along with the service account to create delegated credentials.
    
    Args:
        user_email: Email address of the user to impersonate
        client_id: OAuth client ID from Secret Manager
        client_secret: OAuth client secret from Secret Manager
    
    Returns:
        Gmail API service instance
    """
    try:
        from google.oauth2 import service_account
        from google.auth import default
        
        # Get service account credentials
        credentials, project = default(scopes=GMAIL_SCOPES)
        
        # For DWD, we need to use the service account with subject delegation
        # The OAuth client ID/secret are used for the initial authentication
        # but the service account is what actually accesses Gmail
        
        # Create delegated credentials
        delegated_credentials = credentials.with_subject(user_email)
        
        # Build Gmail API service
        service = build('gmail', 'v1', credentials=delegated_credentials)
        
        logger.info(f"Successfully created Gmail service with OAuth client for user: {user_email}")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Gmail service with OAuth for {user_email}: {str(e)}", exc_info=True)
        raise

