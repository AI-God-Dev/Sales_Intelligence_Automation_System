"""
Salesforce Lead creation automation from unmatched emails.
Creates leads from emails that don't match existing contacts.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
from simple_salesforce import Salesforce
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from utils.email_normalizer import normalize_email
from config.config import settings

logger = setup_logger(__name__)


class LeadCreator:
    """Create Salesforce leads from unmatched emails."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        
        # Initialize Salesforce client
        self.sf = Salesforce(
            username=settings.salesforce_username,
            password=settings.salesforce_password,
            security_token=settings.salesforce_security_token,
            domain=settings.salesforce_domain
        )
    
    def get_unmatched_emails(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get unmatched emails from BigQuery."""
        query = f"""
        SELECT 
            p.participant_id,
            p.email_address,
            p.message_id,
            m.subject,
            m.sent_at,
            m.mailbox_email,
            m.from_email,
            m.body_text
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants` p
        JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages` m
          ON p.message_id = m.message_id
        WHERE p.sf_contact_id IS NULL
          AND p.role = 'from'
          AND m.sent_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
          AND p.email_address NOT LIKE '%maharaniweddings.com'
          AND p.email_address NOT LIKE '%noreply%'
          AND p.email_address NOT LIKE '%no-reply%'
        ORDER BY m.sent_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.bq_client.query(query)
    
    def extract_company_from_email(self, email: str) -> str:
        """Extract company name from email domain."""
        domain = email.split('@')[1] if '@' in email else ''
        # Remove common suffixes
        domain = domain.replace('.com', '').replace('.net', '').replace('.org', '')
        # Capitalize first letter of each word
        company = ' '.join(word.capitalize() for word in domain.split('.'))
        return company or 'Unknown Company'
    
    def extract_name_from_email(self, email: str, subject: str = "", body: str = "") -> tuple[str, str]:
        """Extract first and last name from email, subject, or body."""
        # Try to extract from email
        local_part = email.split('@')[0] if '@' in email else ''
        
        # Common patterns: first.last, first_last, firstlast
        if '.' in local_part:
            parts = local_part.split('.')
            if len(parts) >= 2:
                return parts[0].capitalize(), parts[-1].capitalize()
        elif '_' in local_part:
            parts = local_part.split('_')
            if len(parts) >= 2:
                return parts[0].capitalize(), parts[-1].capitalize()
        
        # Try to extract from email signature in body
        if body:
            # Look for patterns like "Best regards, First Last"
            import re
            pattern = r'(?:Best|Regards|Thanks),?\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)'
            match = re.search(pattern, body)
            if match:
                return match.group(1), match.group(2)
        
        # Fallback: split local part
        if local_part:
            return local_part.capitalize(), ""
        
        return "Unknown", "Lead"
    
    def create_lead(self, email_data: Dict[str, Any], owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a Salesforce lead from email data."""
        email = email_data.get("email_address", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body_text", "")
        
        # Extract information
        first_name, last_name = self.extract_name_from_email(email, subject, body)
        company = self.extract_company_from_email(email)
        
        # Prepare lead data
        lead_data = {
            "FirstName": first_name,
            "LastName": last_name,
            "Email": normalize_email(email),
            "Company": company,
            "LeadSource": "AI Inbound Email",
            "Status": "New",
            "Description": f"Auto-created from email:\nSubject: {subject}\n\nBody preview: {body[:500] if body else ''}"
        }
        
        if owner_id:
            lead_data["OwnerId"] = owner_id
        
        try:
            # Create lead in Salesforce
            result = self.sf.Lead.create(lead_data)
            lead_id = result.get('id')
            
            logger.info(f"Created lead {lead_id} from email {email}")
            
            # Record in BigQuery
            self._record_lead_creation(email_data, lead_id)
            
            return {
                "success": True,
                "lead_id": lead_id,
                "email": email,
                "lead_data": lead_data
            }
        except Exception as e:
            logger.error(f"Failed to create lead from {email}: {e}", exc_info=True)
            return {
                "success": False,
                "email": email,
                "error": str(e)
            }
    
    def _record_lead_creation(self, email_data: Dict[str, Any], lead_id: str):
        """Record lead creation in BigQuery."""
        lead_record = {
            "lead_id": lead_id,
            "first_name": email_data.get("first_name", "Unknown"),
            "last_name": email_data.get("last_name", "Lead"),
            "email": email_data.get("email_address", ""),
            "company": self.extract_company_from_email(email_data.get("email_address", "")),
            "phone": None,
            "title": None,
            "lead_source": "AI Inbound Email",
            "status": "New",
            "owner_id": None,
            "created_by_system": True,
            "source_message_id": email_data.get("message_id"),
            "created_date": datetime.now(timezone.utc).isoformat(),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.bq_client.insert_rows("sf_leads", [lead_record])
        except Exception as e:
            logger.error(f"Failed to record lead creation in BigQuery: {e}")
    
    def process_unmatched_emails(self, limit: int = 10, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Process unmatched emails and create leads."""
        logger.info(f"Processing unmatched emails (limit: {limit})")
        
        unmatched_emails = self.get_unmatched_emails(limit=limit)
        
        if not unmatched_emails:
            logger.info("No unmatched emails found")
            return {
                "processed": 0,
                "created": 0,
                "failed": 0,
                "results": []
            }
        
        results = []
        created_count = 0
        failed_count = 0
        
        for email_data in unmatched_emails:
            result = self.create_lead(email_data, owner_id)
            results.append(result)
            
            if result.get("success"):
                created_count += 1
            else:
                failed_count += 1
        
        return {
            "processed": len(unmatched_emails),
            "created": created_count,
            "failed": failed_count,
            "results": results
        }

