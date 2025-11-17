"""
Comprehensive Examples for All Integration Modules

This file demonstrates how to use all the integration modules and setup scripts.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.secret_manager import (
    get_hubspot_access_token,
    get_gmail_oauth_credentials,
    get_salesforce_credentials,
    get_dialpad_api_key,
    SecretManagerClient
)
from integrations.gmail_oauth import GmailOAuthClient
from integrations.hubspot_api import HubSpotAPIClient
from integrations.salesforce_oauth import SalesforceOAuthClient
from integrations.dialpad_api import DialpadAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_secret_manager():
    """Example 1: Using Secret Manager to retrieve credentials."""
    print("\n" + "=" * 60)
    print("Example 1: Secret Manager Integration")
    print("=" * 60)
    
    # Initialize Secret Manager client
    secret_client = SecretManagerClient()
    
    # Retrieve HubSpot access token
    try:
        hubspot_token = get_hubspot_access_token()
        print(f"✓ HubSpot token retrieved: {hubspot_token[:20]}...")
    except Exception as e:
        print(f"✗ Error retrieving HubSpot token: {e}")
    
    # Retrieve Gmail OAuth credentials for Anand
    try:
        gmail_creds = get_gmail_oauth_credentials("anand")
        print(f"✓ Gmail credentials retrieved for Anand")
        print(f"  Client ID: {gmail_creds['client_id'][:30]}...")
    except Exception as e:
        print(f"✗ Error retrieving Gmail credentials: {e}")
    
    # Retrieve Salesforce credentials
    try:
        sf_creds = get_salesforce_credentials()
        print(f"✓ Salesforce credentials retrieved")
        print(f"  Client ID: {sf_creds['client_id'][:30]}...")
    except Exception as e:
        print(f"✗ Error retrieving Salesforce credentials: {e}")
    
    # Retrieve Dialpad API key
    try:
        dialpad_key = get_dialpad_api_key()
        print(f"✓ Dialpad API key retrieved: {dialpad_key[:20]}...")
    except Exception as e:
        print(f"✗ Error retrieving Dialpad API key: {e}")


def example_gmail_integration():
    """Example 2: Gmail API integration with OAuth 2.0."""
    print("\n" + "=" * 60)
    print("Example 2: Gmail API Integration")
    print("=" * 60)
    
    # Fetch emails for Anand
    try:
        client = GmailOAuthClient(user="anand")
        emails = client.get_latest_emails(max_results=3)
        
        print(f"\n✓ Retrieved {len(emails)} emails for Anand:")
        for i, email in enumerate(emails, 1):
            print(f"\n  Email {i}:")
            print(f"    Subject: {email['subject']}")
            print(f"    From: {email['sender']}")
            print(f"    Date: {email['date']}")
    except Exception as e:
        print(f"✗ Error with Gmail integration: {e}")
        logger.error(f"Gmail integration error: {e}", exc_info=True)


def example_hubspot_integration():
    """Example 3: HubSpot API integration."""
    print("\n" + "=" * 60)
    print("Example 3: HubSpot API Integration")
    print("=" * 60)
    
    try:
        client = HubSpotAPIClient()
        client.authenticate()
        
        # Get email engagement events
        print("\nFetching email engagement events...")
        events = client.get_email_engagement_events(limit=5)
        print(f"✓ Retrieved {len(events)} email engagement events")
        
        # Get sequences
        print("\nFetching sequences...")
        sequences = client.get_sequences(limit=3)
        print(f"✓ Retrieved {len(sequences)} sequences")
        
        # Example sequence enrollment (commented out to avoid actual enrollment)
        # if sequences and events:
        #     sequence_id = sequences[0].get('id')
        #     contact_id = events[0].get('contactId')
        #     if sequence_id and contact_id:
        #         enrollment = client.enroll_in_sequence(contact_id, sequence_id)
        #         print(f"✓ Enrolled contact {contact_id} in sequence {sequence_id}")
        
    except Exception as e:
        print(f"✗ Error with HubSpot integration: {e}")
        logger.error(f"HubSpot integration error: {e}", exc_info=True)


def example_salesforce_integration():
    """Example 4: Salesforce API integration."""
    print("\n" + "=" * 60)
    print("Example 4: Salesforce API Integration")
    print("=" * 60)
    
    try:
        client = SalesforceOAuthClient()
        client.authenticate()
        
        # Fetch accounts
        print("\nFetching Salesforce accounts...")
        accounts = client.get_accounts(limit=3)
        print(f"✓ Retrieved {len(accounts)} accounts")
        
        for i, account in enumerate(accounts, 1):
            print(f"\n  Account {i}:")
            print(f"    Name: {account.get('Name', 'N/A')}")
            print(f"    Annual Revenue: ${account.get('AnnualRevenue', 0):,.2f}" 
                  if account.get('AnnualRevenue') else "    Annual Revenue: N/A")
        
        # Fetch contacts
        print("\nFetching Salesforce contacts...")
        contacts = client.get_contacts(limit=3)
        print(f"✓ Retrieved {len(contacts)} contacts")
        
        # Fetch leads
        print("\nFetching Salesforce leads...")
        leads = client.get_leads(limit=3)
        print(f"✓ Retrieved {len(leads)} leads")
        
        # Fetch opportunities
        print("\nFetching Salesforce opportunities...")
        opportunities = client.get_opportunities(limit=3)
        print(f"✓ Retrieved {len(opportunities)} opportunities")
        
    except Exception as e:
        print(f"✗ Error with Salesforce integration: {e}")
        logger.error(f"Salesforce integration error: {e}", exc_info=True)


def example_dialpad_integration():
    """Example 5: Dialpad API integration."""
    print("\n" + "=" * 60)
    print("Example 5: Dialpad API Integration")
    print("=" * 60)
    
    try:
        client = DialpadAPIClient()
        client.authenticate()
        
        # Fetch call logs
        print("\nFetching call logs...")
        calls = client.get_call_logs(limit=5)
        print(f"✓ Retrieved {len(calls)} call logs")
        
        for i, call in enumerate(calls, 1):
            print(f"\n  Call {i}:")
            print(f"    From: {call.get('from_number', 'N/A')}")
            print(f"    To: {call.get('to_number', 'N/A')}")
            print(f"    Duration: {call.get('duration_seconds', 0)} seconds")
            print(f"    Call Time: {call.get('start_time', call.get('call_time', 'N/A'))}")
        
    except Exception as e:
        print(f"✗ Error with Dialpad integration: {e}")
        logger.error(f"Dialpad integration error: {e}", exc_info=True)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Sales Intelligence Integration Examples")
    print("=" * 60)
    
    # Run examples
    example_secret_manager()
    example_gmail_integration()
    example_hubspot_integration()
    example_salesforce_integration()
    example_dialpad_integration()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Run setup scripts to configure infrastructure:")
    print("   - python scripts/setup_pubsub.py")
    print("   - python scripts/setup_bigquery.py")
    print("   - python scripts/setup_cloud_functions.py")
    print("   - python scripts/setup_cloud_scheduler.py")
    print("   - python scripts/check_iam_permissions.py")
    print("\n2. Deploy Cloud Functions and set up scheduled jobs")
    print("3. Start ingesting data from all sources")


if __name__ == "__main__":
    main()

