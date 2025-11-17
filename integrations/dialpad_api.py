"""
Dialpad API Integration
Retrieves API key from Secret Manager and fetches call logs and transcriptions.
"""
import logging
from typing import List, Dict, Any, Optional
import requests
from utils.secret_manager import get_dialpad_api_key, get_secret_client

logger = logging.getLogger(__name__)


class DialpadAPIClient:
    """
    Dialpad API client for retrieving call logs and transcriptions.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Dialpad API client.
        
        Args:
            project_id: Optional GCP project ID override
        """
        self.project_id = project_id
        self.base_url = "https://dialpad.com/api/v2"
        self.api_key: Optional[str] = None
    
    def authenticate(self) -> None:
        """
        Authenticate with Dialpad using API key from Secret Manager.
        """
        try:
            self.api_key = get_dialpad_api_key(self.project_id)
            logger.info("Successfully retrieved Dialpad API key from Secret Manager")
        except Exception as e:
            logger.error(f"Failed to retrieve Dialpad API key: {e}")
            raise
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Dialpad API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
        
        Returns:
            Response JSON as dictionary
        """
        if not self.api_key:
            self.authenticate()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            logger.error(f"HTTP error in Dialpad API request: {e}")
            if response.status_code == 401:
                logger.error("Authentication failed. Check API key.")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error in Dialpad API: {e}")
            raise
    
    def get_call_logs(
        self,
        limit: int = 5,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch call logs from Dialpad.
        
        Args:
            limit: Maximum number of calls to retrieve
            user_id: Optional user ID to filter calls
            start_time: Optional start time filter (ISO format)
            end_time: Optional end time filter (ISO format)
        
        Returns:
            List of call log records
        """
        try:
            params = {
                "limit": limit
            }
            
            if user_id:
                params["user_id"] = user_id
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            response = self._make_request("GET", "/calls", params=params)
            
            calls = response.get("items", []) or response.get("calls", [])
            logger.info(f"Retrieved {len(calls)} call logs")
            
            return calls
            
        except Exception as e:
            logger.error(f"Error fetching call logs: {e}")
            raise
    
    def get_call_transcription(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transcription for a specific call.
        
        Args:
            call_id: Dialpad call ID
        
        Returns:
            Transcription data or None if not available
        """
        try:
            response = self._make_request("GET", f"/calls/{call_id}/transcription")
            
            transcription = response.get("transcription") or response
            return transcription
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Transcription not found for call {call_id}")
                return None
            raise
        except Exception as e:
            logger.error(f"Error fetching transcription for call {call_id}: {e}")
            raise


def main():
    """
    Example usage: Fetch and display last 5 call logs.
    """
    client = DialpadAPIClient()
    
    try:
        # Authenticate
        client.authenticate()
        
        # Fetch call logs
        print("\n=== Fetching Last 5 Call Logs ===\n")
        calls = client.get_call_logs(limit=5)
        
        for i, call in enumerate(calls, 1):
            print(f"Call {i}:")
            print(f"  Call ID: {call.get('id', 'N/A')}")
            print(f"  From: {call.get('from_number', 'N/A')}")
            print(f"  To: {call.get('to_number', 'N/A')}")
            print(f"  Duration: {call.get('duration_seconds', 0)} seconds")
            print(f"  Call Time: {call.get('start_time', call.get('call_time', 'N/A'))}")
            print(f"  Direction: {call.get('direction', 'N/A')}")
            
            # Try to get transcription if available
            call_id = call.get('id')
            if call_id:
                transcription = client.get_call_transcription(call_id)
                if transcription:
                    transcript_text = transcription.get('text', '')
                    if transcript_text:
                        print(f"  Transcript: {transcript_text[:100]}...")
            
            print()
        
    except Exception as e:
        logger.error(f"Error in Dialpad API example: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

