"""
HubSpot sequence enrollment automation.
Enrolls contacts in HubSpot sequences from the web app.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from hubspot import HubSpot
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from utils.email_normalizer import normalize_email
from config.config import settings

logger = setup_logger(__name__)


class HubSpotEnroller:
    """Enroll contacts in HubSpot sequences."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        
        # Initialize HubSpot client
        self.api_client = HubSpot(access_token=settings.hubspot_api_key)
    
    def get_available_sequences(self) -> List[Dict[str, Any]]:
        """Get available sequences from BigQuery or HubSpot."""
        query = f"""
        SELECT 
            sequence_id,
            sequence_name,
            is_active,
            enrollment_count
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.hubspot_sequences`
        WHERE is_active = TRUE
        ORDER BY sequence_name
        """
        
        return self.bq_client.query(query)
    
    def find_contact_by_email(self, email: str) -> Optional[str]:
        """Find HubSpot contact ID by email address."""
        try:
            normalized_email = normalize_email(email)
            
            # Search for contact in HubSpot
            # HubSpot API: GET /crm/v3/objects/contacts/search
            search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": normalized_email
                            }
                        ]
                    }
                ]
            }
            
            result = self.api_client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )
            
            if result.results and len(result.results) > 0:
                return result.results[0].id
            
            return None
        except Exception as e:
            logger.error(f"Error finding contact by email {email}: {e}", exc_info=True)
            return None
    
    def create_contact_if_not_exists(self, email: str, first_name: str = "", last_name: str = "") -> Optional[str]:
        """Create HubSpot contact if it doesn't exist."""
        try:
            # Check if contact exists
            contact_id = self.find_contact_by_email(email)
            if contact_id:
                return contact_id
            
            # Create new contact
            contact_data = {
                "properties": {
                    "email": normalize_email(email),
                    "firstname": first_name,
                    "lastname": last_name
                }
            }
            
            result = self.api_client.crm.contacts.basic_api.create(
                simple_public_object_input=contact_data
            )
            
            logger.info(f"Created HubSpot contact {result.id} for {email}")
            return result.id
            
        except Exception as e:
            logger.error(f"Error creating contact for {email}: {e}", exc_info=True)
            return None
    
    def enroll_contact_in_sequence(
        self,
        contact_email: str,
        sequence_id: str,
        first_name: str = "",
        last_name: str = ""
    ) -> Dict[str, Any]:
        """Enroll a contact in a HubSpot sequence."""
        try:
            # Get or create contact
            contact_id = self.find_contact_by_email(contact_email)
            if not contact_id:
                contact_id = self.create_contact_if_not_exists(
                    contact_email,
                    first_name,
                    last_name
                )
            
            if not contact_id:
                return {
                    "success": False,
                    "error": "Failed to find or create contact"
                }
            
            # Enroll in sequence
            # HubSpot API: POST /marketing/v3/sequences/{sequenceId}/enrollments
            enrollment_data = {
                "contactIds": [contact_id]
            }
            
            # Note: HubSpot API structure may vary - adjust based on actual API
            # This is a simplified version
            enrollment_api = self.api_client.marketing.sequences.enrollments_api
            result = enrollment_api.enroll(
                sequence_id=sequence_id,
                enrollment_data=enrollment_data
            )
            
            logger.info(f"Enrolled contact {contact_id} in sequence {sequence_id}")
            
            # Track enrollment in BigQuery (optional)
            self._track_enrollment(contact_email, contact_id, sequence_id, success=True)
            
            return {
                "success": True,
                "contact_id": contact_id,
                "sequence_id": sequence_id,
                "enrollment_id": getattr(result, 'id', None)
            }
            
        except Exception as e:
            logger.error(f"Error enrolling {contact_email} in sequence {sequence_id}: {e}", exc_info=True)
            self._track_enrollment(contact_email, None, sequence_id, success=False, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _track_enrollment(
        self,
        email: str,
        contact_id: Optional[str],
        sequence_id: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Track enrollment in BigQuery for monitoring."""
        # This could be stored in a separate enrollments tracking table
        # For now, we'll just log it
        logger.info(
            f"Enrollment tracked: email={email}, contact_id={contact_id}, "
            f"sequence_id={sequence_id}, success={success}, error={error}"
        )
    
    def enroll_multiple_contacts(
        self,
        contacts: List[Dict[str, str]],
        sequence_id: str
    ) -> Dict[str, Any]:
        """Enroll multiple contacts in a sequence."""
        results = []
        success_count = 0
        failed_count = 0
        
        for contact in contacts:
            email = contact.get("email", "")
            first_name = contact.get("first_name", "")
            last_name = contact.get("last_name", "")
            
            result = self.enroll_contact_in_sequence(
                email,
                sequence_id,
                first_name,
                last_name
            )
            
            results.append({
                "email": email,
                "result": result
            })
            
            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "total": len(contacts),
            "success": success_count,
            "failed": failed_count,
            "results": results
        }

