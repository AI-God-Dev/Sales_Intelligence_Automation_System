"""
Salesforce API Integration using OAuth 2.0
Retrieves OAuth credentials from Secret Manager and syncs Salesforce data.
Only syncs Salesforce-specific data: Accounts, Contacts, Leads, Opportunities.
Does NOT sync HubSpot contacts.
"""
import logging
from typing import List, Dict, Any, Optional
import requests
from utils.secret_manager import get_salesforce_credentials, get_secret_client

logger = logging.getLogger(__name__)


class SalesforceOAuthClient:
    """
    Salesforce API client using OAuth 2.0 credentials from Secret Manager.
    
    Syncs only Salesforce-specific data:
    - Accounts
    - Contacts
    - Leads
    - Opportunities
    """
    
    def __init__(
        self,
        instance_url: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        Initialize Salesforce OAuth client.
        
        Args:
            instance_url: Salesforce instance URL (e.g., https://yourinstance.salesforce.com)
                         If not provided, will be retrieved from OAuth token response
            project_id: Optional GCP project ID override
        """
        self.project_id = project_id
        self.instance_url = instance_url
        self.access_token: Optional[str] = None
        self.api_version = "v58.0"  # Latest API version
    
    def authenticate(self) -> None:
        """
        Authenticate with Salesforce using OAuth 2.0 credentials from Secret Manager.
        Uses refresh token flow to get access token.
        """
        try:
            # Retrieve OAuth credentials from Secret Manager
            creds = get_salesforce_credentials(self.project_id)
            
            # Salesforce OAuth token endpoint
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
            # Request new access token using refresh token
            data = {
                "grant_type": "refresh_token",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "refresh_token": creds["refresh_token"]
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            # Get instance URL if not provided
            if not self.instance_url:
                self.instance_url = token_data.get("instance_url")
            
            logger.info("Successfully authenticated with Salesforce")
            logger.debug(f"Instance URL: {self.instance_url}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Salesforce: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Salesforce authentication: {e}")
            raise
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Salesforce API.
        
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
        
        url = f"{self.instance_url}/services/data/{self.api_version}{endpoint}"
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
            if response.status_code == 401:
                # Token expired, re-authenticate
                logger.warning("Access token expired, re-authenticating...")
                self.authenticate()
                return self._make_request(method, endpoint, params, data)
            logger.error(f"HTTP error in Salesforce API request: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error in Salesforce API: {e}")
            raise
    
    def query(self, soql: str) -> List[Dict[str, Any]]:
        """
        Execute a SOQL query.
        
        Args:
            soql: SOQL query string
        
        Returns:
            List of records
        """
        try:
            params = {"q": soql}
            response = self._make_request("GET", "/query", params=params)
            
            records = response.get("records", [])
            logger.info(f"Query returned {len(records)} records")
            
            return records
            
        except Exception as e:
            logger.error(f"Error executing SOQL query: {e}")
            raise
    
    def get_accounts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch accounts from Salesforce.
        
        Args:
            limit: Maximum number of accounts to retrieve
        
        Returns:
            List of account records
        """
        soql = f"""
        SELECT Id, Name, Website, Industry, AnnualRevenue, OwnerId, 
               CreatedDate, LastModifiedDate
        FROM Account
        ORDER BY LastModifiedDate DESC
        LIMIT {limit}
        """
        
        return self.query(soql)
    
    def get_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch contacts from Salesforce.
        
        Args:
            limit: Maximum number of contacts to retrieve
        
        Returns:
            List of contact records
        """
        soql = f"""
        SELECT Id, AccountId, FirstName, LastName, Email, Phone, 
               MobilePhone, Title, CreatedDate, LastModifiedDate
        FROM Contact
        ORDER BY LastModifiedDate DESC
        LIMIT {limit}
        """
        
        return self.query(soql)
    
    def get_leads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch leads from Salesforce.
        
        Args:
            limit: Maximum number of leads to retrieve
        
        Returns:
            List of lead records
        """
        soql = f"""
        SELECT Id, FirstName, LastName, Email, Company, Phone, Title, 
               LeadSource, Status, OwnerId, CreatedDate, LastModifiedDate
        FROM Lead
        ORDER BY LastModifiedDate DESC
        LIMIT {limit}
        """
        
        return self.query(soql)
    
    def get_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch opportunities from Salesforce.
        
        Args:
            limit: Maximum number of opportunities to retrieve
        
        Returns:
            List of opportunity records
        """
        soql = f"""
        SELECT Id, AccountId, Name, StageName, Amount, CloseDate, 
               Probability, OwnerId, IsClosed, IsWon, CreatedDate, LastModifiedDate
        FROM Opportunity
        ORDER BY LastModifiedDate DESC
        LIMIT {limit}
        """
        
        return self.query(soql)


def main():
    """
    Example usage: Fetch and display Salesforce accounts.
    """
    client = SalesforceOAuthClient()
    
    try:
        # Authenticate
        client.authenticate()
        
        # Fetch accounts
        print("\n=== Fetching Salesforce Accounts ===\n")
        accounts = client.get_accounts(limit=5)
        
        for i, account in enumerate(accounts, 1):
            print(f"Account {i}:")
            print(f"  Account Name: {account.get('Name', 'N/A')}")
            print(f"  Annual Revenue: ${account.get('AnnualRevenue', 0):,.2f}" if account.get('AnnualRevenue') else "  Annual Revenue: N/A")
            print(f"  Industry: {account.get('Industry', 'N/A')}")
            print(f"  Website: {account.get('Website', 'N/A')}")
            print(f"  ID: {account.get('Id', 'N/A')}")
            print()
        
        # Example: Fetch contacts
        print("\n=== Fetching Salesforce Contacts ===\n")
        contacts = client.get_contacts(limit=3)
        
        for i, contact in enumerate(contacts, 1):
            print(f"Contact {i}:")
            print(f"  Name: {contact.get('FirstName', '')} {contact.get('LastName', '')}")
            print(f"  Email: {contact.get('Email', 'N/A')}")
            print(f"  Phone: {contact.get('Phone', 'N/A')}")
            print()
        
        # Example: Fetch leads
        print("\n=== Fetching Salesforce Leads ===\n")
        leads = client.get_leads(limit=3)
        
        for i, lead in enumerate(leads, 1):
            print(f"Lead {i}:")
            print(f"  Name: {lead.get('FirstName', '')} {lead.get('LastName', '')}")
            print(f"  Company: {lead.get('Company', 'N/A')}")
            print(f"  Email: {lead.get('Email', 'N/A')}")
            print()
        
        # Example: Fetch opportunities
        print("\n=== Fetching Salesforce Opportunities ===\n")
        opportunities = client.get_opportunities(limit=3)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"Opportunity {i}:")
            print(f"  Name: {opp.get('Name', 'N/A')}")
            print(f"  Stage: {opp.get('StageName', 'N/A')}")
            print(f"  Amount: ${opp.get('Amount', 0):,.2f}" if opp.get('Amount') else "  Amount: N/A")
            print()
        
    except Exception as e:
        logger.error(f"Error in Salesforce API example: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

