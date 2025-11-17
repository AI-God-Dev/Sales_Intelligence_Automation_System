"""
HubSpot API Integration
Retrieves credentials from Secret Manager and interacts with HubSpot API.
Focuses on email engagement data and sequence enrollment (no contact/company/deal sync).
"""
import logging
import time
from typing import List, Dict, Any, Optional
import requests
from utils.secret_manager import get_hubspot_access_token, get_secret_client

logger = logging.getLogger(__name__)

# HubSpot API rate limits
RATE_LIMIT_REQUESTS = 150  # requests per 10 seconds
RATE_LIMIT_WINDOW = 10  # seconds
RATE_LIMIT_DAILY = 500000  # daily limit


class HubSpotAPIClient:
    """
    HubSpot API client with rate limiting and error handling.
    
    Only syncs HubSpot-specific data:
    - Email engagement events
    - Sequence enrollments
    - Sequence metadata
    
    Does NOT sync contacts, companies, or deals.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize HubSpot API client.
        
        Args:
            project_id: Optional GCP project ID override
        """
        self.project_id = project_id
        self.base_url = "https://api.hubapi.com"
        self.access_token: Optional[str] = None
        self.request_times: List[float] = []  # Track request times for rate limiting
        
    def authenticate(self) -> None:
        """
        Authenticate with HubSpot using access token from Secret Manager.
        """
        try:
            self.access_token = get_hubspot_access_token(self.project_id)
            logger.info("Successfully retrieved HubSpot access token from Secret Manager")
        except Exception as e:
            logger.error(f"Failed to retrieve HubSpot access token: {e}")
            raise
    
    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limits.
        Respects: 150 requests per 10 seconds, 500K daily.
        """
        current_time = time.time()
        
        # Remove requests older than the rate limit window
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < RATE_LIMIT_WINDOW
        ]
        
        # If we've hit the limit, wait
        if len(self.request_times) >= RATE_LIMIT_REQUESTS:
            sleep_time = RATE_LIMIT_WINDOW - (current_time - self.request_times[0]) + 0.1
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Re-check after sleep
                self._check_rate_limit()
        
        # Record this request
        self.request_times.append(current_time)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to HubSpot API with rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
        
        Returns:
            Response JSON as dictionary
        """
        if not self.access_token:
            self.authenticate()
        
        # Check rate limit
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning("Rate limit exceeded. Waiting and retrying...")
                time.sleep(1)
                return self._make_request(method, endpoint, params, data)
            logger.error(f"HTTP error in HubSpot API request: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error in HubSpot API: {e}")
            raise
    
    def get_email_engagement_events(
        self,
        limit: int = 100,
        after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get email engagement events using GET /marketing/v3/emails/events.
        
        Args:
            limit: Maximum number of events to retrieve
            after: Pagination token for next page
        
        Returns:
            List of email engagement events
        """
        try:
            params = {
                "limit": limit
            }
            if after:
                params["after"] = after
            
            response = self._make_request(
                "GET",
                "/marketing/v3/emails/events",
                params=params
            )
            
            events = response.get("results", [])
            logger.info(f"Retrieved {len(events)} email engagement events")
            
            return events
            
        except Exception as e:
            logger.error(f"Error fetching email engagement events: {e}")
            raise
    
    def enroll_in_sequence(
        self,
        contact_id: str,
        sequence_id: str,
        enrollment_type: str = "CONTACT"
    ) -> Dict[str, Any]:
        """
        Enroll a contact in a sequence using POST /automation/v4/actions/enrollments.
        
        Args:
            contact_id: HubSpot contact ID
            sequence_id: HubSpot sequence ID
            enrollment_type: Type of enrollment (CONTACT, COMPANY, etc.)
        
        Returns:
            Enrollment response
        """
        try:
            data = {
                "enrollmentType": enrollment_type,
                "objectId": contact_id,
                "sequenceId": sequence_id
            }
            
            response = self._make_request(
                "POST",
                "/automation/v4/actions/enrollments",
                data=data
            )
            
            logger.info(f"Successfully enrolled contact {contact_id} in sequence {sequence_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error enrolling in sequence: {e}")
            raise
    
    def get_sequences(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get available sequences (for reference, not syncing).
        
        Args:
            limit: Maximum number of sequences to retrieve
        
        Returns:
            List of sequences
        """
        try:
            params = {"limit": limit}
            response = self._make_request(
                "GET",
                "/automation/v4/workflows",
                params=params
            )
            
            sequences = response.get("results", [])
            logger.info(f"Retrieved {len(sequences)} sequences")
            return sequences
            
        except Exception as e:
            logger.error(f"Error fetching sequences: {e}")
            raise


def main():
    """
    Example usage: Fetch email engagement events and demonstrate sequence enrollment.
    """
    client = HubSpotAPIClient()
    
    try:
        # Authenticate
        client.authenticate()
        
        # Get email engagement events
        print("\n=== Fetching Email Engagement Events ===\n")
        events = client.get_email_engagement_events(limit=10)
        
        for i, event in enumerate(events[:5], 1):
            print(f"Event {i}:")
            print(f"  Type: {event.get('type', 'N/A')}")
            print(f"  Email ID: {event.get('emailId', 'N/A')}")
            print(f"  Contact ID: {event.get('contactId', 'N/A')}")
            print(f"  Timestamp: {event.get('timestamp', 'N/A')}")
            print()
        
        # Get available sequences
        print("\n=== Fetching Available Sequences ===\n")
        sequences = client.get_sequences(limit=5)
        
        for i, seq in enumerate(sequences[:3], 1):
            print(f"Sequence {i}:")
            print(f"  ID: {seq.get('id', 'N/A')}")
            print(f"  Name: {seq.get('name', 'N/A')}")
            print(f"  Enabled: {seq.get('enabled', False)}")
            print()
        
        # Example: Enroll a contact in a sequence (commented out to avoid actual enrollment)
        # if sequences and events:
        #     sequence_id = sequences[0].get('id')
        #     contact_id = events[0].get('contactId')
        #     if sequence_id and contact_id:
        #         print(f"\n=== Enrolling Contact {contact_id} in Sequence {sequence_id} ===\n")
        #         enrollment = client.enroll_in_sequence(contact_id, sequence_id)
        #         print(f"Enrollment successful: {enrollment}")
        
    except Exception as e:
        logger.error(f"Error in HubSpot API example: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

