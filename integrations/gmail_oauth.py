"""
Gmail API Integration using OAuth 2.0
Retrieves OAuth credentials from Google Secret Manager and authenticates with Gmail API.
"""
import logging
import base64
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.secret_manager import get_gmail_oauth_credentials, get_secret_client

logger = logging.getLogger(__name__)

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailOAuthClient:
    """
    Gmail API client using OAuth 2.0 credentials from Secret Manager.
    
    Supports multiple users: Anand, Larnie, and Lia.
    """
    
    def __init__(self, user: str = "anand", project_id: Optional[str] = None):
        """
        Initialize Gmail OAuth client for a specific user.
        
        Args:
            user: User name (anand, larnie, or lia)
            project_id: Optional GCP project ID override
        """
        self.user = user.lower()
        self.project_id = project_id
        self.credentials: Optional[Credentials] = None
        self.service = None
        
        # Validate user
        if self.user not in ["anand", "larnie", "lia"]:
            raise ValueError(f"Invalid user: {user}. Must be one of: anand, larnie, lia")
    
    def authenticate(self) -> None:
        """
        Authenticate with Gmail API using OAuth 2.0 credentials from Secret Manager.
        """
        try:
            # Retrieve OAuth credentials from Secret Manager
            creds_dict = get_gmail_oauth_credentials(self.user, self.project_id)
            
            # Create credentials object
            self.credentials = Credentials(
                token=None,  # Will be refreshed
                refresh_token=creds_dict["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=creds_dict["client_id"],
                client_secret=creds_dict["client_secret"],
                scopes=GMAIL_SCOPES
            )
            
            # Refresh the token if needed
            if not self.credentials.valid:
                if self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    logger.info(f"Refreshed OAuth token for user: {self.user}")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info(f"Successfully authenticated Gmail API for user: {self.user}")
            
        except Exception as e:
            logger.error(f"Failed to authenticate Gmail API for {self.user}: {e}", exc_info=True)
            raise
    
    def get_latest_emails(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch the latest emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to retrieve (default: 5)
        
        Returns:
            List of email dictionaries with subject and sender information
        """
        if not self.service:
            self.authenticate()
        
        try:
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                logger.info(f"No messages found for user: {self.user}")
                return []
            
            # Fetch full message details
            email_list = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    
                    # Extract headers
                    headers = message.get('payload', {}).get('headers', [])
                    header_dict = {h['name']: h['value'] for h in headers}
                    
                    email_info = {
                        'id': message['id'],
                        'thread_id': message.get('threadId'),
                        'subject': header_dict.get('Subject', '(No Subject)'),
                        'sender': header_dict.get('From', 'Unknown'),
                        'date': header_dict.get('Date', ''),
                        'snippet': message.get('snippet', '')
                    }
                    
                    email_list.append(email_info)
                    
                except HttpError as e:
                    logger.error(f"Error fetching message {msg['id']}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(email_list)} emails for user: {self.user}")
            return email_list
            
        except HttpError as e:
            logger.error(f"Error listing messages: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching emails: {e}", exc_info=True)
            raise
    
    def print_latest_emails(self, max_results: int = 5) -> None:
        """
        Print the latest emails with subject and sender.
        
        Args:
            max_results: Maximum number of emails to retrieve and print
        """
        emails = self.get_latest_emails(max_results)
        
        print(f"\n=== Latest {len(emails)} Emails for {self.user.upper()} ===\n")
        
        for i, email in enumerate(emails, 1):
            print(f"Email {i}:")
            print(f"  Subject: {email['subject']}")
            print(f"  From: {email['sender']}")
            print(f"  Date: {email['date']}")
            print(f"  Snippet: {email['snippet'][:100]}...")
            print()


def main():
    """
    Example usage: Fetch and print latest 5 emails for each user.
    """
    users = ["anand", "larnie", "lia"]
    
    for user in users:
        try:
            print(f"\n{'='*60}")
            print(f"Processing emails for: {user.upper()}")
            print(f"{'='*60}")
            
            client = GmailOAuthClient(user=user)
            client.print_latest_emails(max_results=5)
            
        except Exception as e:
            print(f"Error processing emails for {user}: {e}")
            logger.error(f"Error processing emails for {user}: {e}", exc_info=True)
            continue


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

