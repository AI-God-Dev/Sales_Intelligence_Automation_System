"""
Cloud Function endpoints for automation features:
- Lead creation
- HubSpot enrollment
"""
import functions_framework
import logging
from intelligence.automation.lead_creation import LeadCreator
from intelligence.automation.hubspot_enrollment import HubSpotEnroller
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


@functions_framework.http
def create_leads(request):
    """
    HTTP endpoint for creating leads from unmatched emails.
    
    Expected request body:
    {
        "limit": 10 (optional, default: 10),
        "owner_id": "salesforce_user_id" (optional)
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        limit = request_json.get("limit", 10)
        owner_id = request_json.get("owner_id")
        
        bq_client = BigQueryClient()
        lead_creator = LeadCreator(bq_client)
        
        result = lead_creator.process_unmatched_emails(limit=limit, owner_id=owner_id)
        
        return result, 200
        
    except Exception as e:
        logger.error(f"Lead creation failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


@functions_framework.http
def enroll_hubspot(request):
    """
    HTTP endpoint for enrolling contacts in HubSpot sequences.
    
    Expected request body:
    {
        "email": "contact@example.com",
        "sequence_id": "sequence_123",
        "first_name": "John" (optional),
        "last_name": "Doe" (optional)
    }
    
    OR for multiple contacts:
    {
        "contacts": [
            {"email": "contact1@example.com", "first_name": "John", "last_name": "Doe"},
            {"email": "contact2@example.com", "first_name": "Jane", "last_name": "Smith"}
        ],
        "sequence_id": "sequence_123"
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        
        bq_client = BigQueryClient()
        enroller = HubSpotEnroller(bq_client)
        
        # Check if single or multiple contacts
        if "contacts" in request_json:
            # Multiple contacts
            contacts = request_json["contacts"]
            sequence_id = request_json["sequence_id"]
            result = enroller.enroll_multiple_contacts(contacts, sequence_id)
        else:
            # Single contact
            email = request_json.get("email")
            sequence_id = request_json.get("sequence_id")
            first_name = request_json.get("first_name", "")
            last_name = request_json.get("last_name", "")
            
            if not email or not sequence_id:
                return {
                    "error": "email and sequence_id are required"
                }, 400
            
            result = enroller.enroll_contact_in_sequence(
                email,
                sequence_id,
                first_name,
                last_name
            )
        
        return result, 200
        
    except Exception as e:
        logger.error(f"HubSpot enrollment failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500


@functions_framework.http
def get_hubspot_sequences(request):
    """
    HTTP endpoint to get available HubSpot sequences.
    """
    try:
        bq_client = BigQueryClient()
        enroller = HubSpotEnroller(bq_client)
        
        sequences = enroller.get_available_sequences()
        
        return {
            "sequences": sequences
        }, 200
        
    except Exception as e:
        logger.error(f"Failed to get sequences: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

