"""Entity resolution logic for matching emails and calls to Salesforce contacts/accounts."""
import logging
from typing import Optional, Dict, Any, List
from google.cloud import bigquery
from utils.email_normalizer import normalize_email
from utils.phone_normalizer import normalize_phone, match_phone_numbers, extract_last_10_digits
from utils.bigquery_client import BigQueryClient
from config.config import settings

logger = logging.getLogger(__name__)


class EntityMatcher:
    """Matches emails and phone numbers to Salesforce contacts and accounts."""
    
    def __init__(self, bq_client: BigQueryClient = None):
        self.bq_client = bq_client or BigQueryClient()
    
    def match_email_to_contact(
        self,
        email: str,
        check_manual_mappings: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Match email address to Salesforce contact.
        
        Args:
            email: Email address to match
            check_manual_mappings: Whether to check manual_mappings table
        
        Returns:
            Dictionary with contact_id, account_id, match_confidence or None
        """
        normalized_email = normalize_email(email)
        if not normalized_email:
            return None
        
        # Check manual mappings first
        if check_manual_mappings:
            manual_match = self._check_manual_email_mapping(normalized_email)
            if manual_match and manual_match.get("sf_contact_id") and manual_match.get("sf_account_id"):
                return {
                    "contact_id": manual_match.get("sf_contact_id"),
                    "account_id": manual_match.get("sf_account_id"),
                    "match_confidence": "manual"
                }
        
        # Exact match against sf_contacts
        query = f"""
        SELECT 
            contact_id,
            account_id,
            email
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_contacts`
        WHERE email = @email
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", normalized_email)
            ]
        )
        
        results = self.bq_client.query(query, job_config)
        
        if results:
            contact = results[0]
            return {
                "contact_id": contact["contact_id"],
                "account_id": contact["account_id"],
                "match_confidence": "exact"
            }
        
        return None
    
    def match_phone_to_contact(
        self,
        phone: str,
        check_manual_mappings: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Match phone number to Salesforce contact.
        
        Args:
            phone: Phone number to match
            check_manual_mappings: Whether to check manual_mappings table
        
        Returns:
            Dictionary with contact_id, account_id, match_confidence or None
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return None
        
        # Check manual mappings first
        if check_manual_mappings:
            manual_match = self._check_manual_phone_mapping(normalized_phone)
            if manual_match and manual_match.get("sf_contact_id") and manual_match.get("sf_account_id"):
                return {
                    "contact_id": manual_match.get("sf_contact_id"),
                    "account_id": manual_match.get("sf_account_id"),
                    "match_confidence": "manual"
                }
            # Fallback: if a contact/account match structure is returned, accept as exact
            if manual_match and manual_match.get("contact_id") and manual_match.get("account_id"):
                return {
                    "contact_id": manual_match.get("contact_id"),
                    "account_id": manual_match.get("account_id"),
                    "match_confidence": "exact"
                }
        
        # Try exact match first
        query = f"""
        SELECT 
            contact_id,
            account_id,
            phone,
            mobile_phone
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_contacts`
        WHERE phone = @phone OR mobile_phone = @phone
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("phone", "STRING", normalized_phone)
            ]
        )
        
        results = self.bq_client.query(query, job_config)
        
        if results:
            contact = results[0]
            return {
                "contact_id": contact["contact_id"],
                "account_id": contact["account_id"],
                "match_confidence": "exact"
            }
        
        # Try partial match (last 10 digits)
        last_10 = extract_last_10_digits(phone)
        if last_10:
            # This would require a more complex query with string functions
            # For now, return None if exact match fails
            pass
        
        return None
    
    def _check_manual_email_mapping(self, email: str) -> Optional[Dict[str, Any]]:
        """Check manual_mappings table for email."""
        query = f"""
        SELECT 
            sf_contact_id,
            sf_account_id
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.manual_mappings`
        WHERE email_address = @email
          AND is_active = TRUE
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )
        
        results = self.bq_client.query(query, job_config)
        return results[0] if results else None
    
    def _check_manual_phone_mapping(self, phone: str) -> Optional[Dict[str, Any]]:
        """Check manual_mappings table for phone."""
        query = f"""
        SELECT 
            sf_contact_id,
            sf_account_id
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.manual_mappings`
        WHERE phone_number = @phone
          AND is_active = TRUE
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("phone", "STRING", phone)
            ]
        )
        
        results = self.bq_client.query(query, job_config)
        return results[0] if results else None
    
    def match_phone_to_contact_enhanced(
        self,
        phone: str,
        check_manual_mappings: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Enhanced phone matching with fuzzy matching support.
        
        Args:
            phone: Phone number to match
            check_manual_mappings: Whether to check manual_mappings table
        
        Returns:
            Dictionary with contact_id, account_id, match_confidence or None
        """
        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            return None
        
        # Skip manual mappings in enhanced flow to allow proper exact→fuzzy sequence
        
        # Try exact match first
        query = f"""
        SELECT 
            contact_id,
            account_id,
            phone,
            mobile_phone
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_contacts`
        WHERE phone = @phone OR mobile_phone = @phone
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("phone", "STRING", normalized_phone)
            ]
        )
        
        results = self.bq_client.query(query, job_config)
        
        if results:
            contact = results[0]
            return {
                "contact_id": contact["contact_id"],
                "account_id": contact["account_id"],
                "match_confidence": "exact"
            }
        
        # Try fuzzy match (last 10 digits)
        last_10 = extract_last_10_digits(normalized_phone)
        if last_10:
            fuzzy_query = f"""
            SELECT 
                contact_id,
                account_id,
                phone,
                mobile_phone
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_contacts`
            WHERE REGEXP_EXTRACT(phone, r'\\d{{10}}$') = @last_10
               OR REGEXP_EXTRACT(mobile_phone, r'\\d{{10}}$') = @last_10
            LIMIT 1
            """
            
            fuzzy_job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("last_10", "STRING", last_10)
                ]
            )
            
            fuzzy_results = self.bq_client.query(fuzzy_query, fuzzy_job_config)
            if fuzzy_results:
                contact = fuzzy_results[0]
                return {
                    "contact_id": contact["contact_id"],
                    "account_id": contact["account_id"],
                    "match_confidence": "fuzzy"
                }
        
        return None
    
    def update_participant_matches(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Batch update gmail_participants with contact/account matches.
        
        Args:
            batch_size: Number of participants to process at once
        
        Returns:
            Dictionary with match statistics
        """
        stats = {
            "processed": 0,
            "matched": 0,
            "unmatched": 0,
            "errors": 0
        }
        
        # Get unmatched participants
        query = f"""
        SELECT 
            participant_id,
            email_address
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants`
        WHERE sf_contact_id IS NULL
          AND email_address IS NOT NULL
        LIMIT {batch_size}
        """
        
        try:
            participants = self.bq_client.query(query)
            
            updates = []
            for participant in participants:
                try:
                    stats["processed"] += 1
                    match = self.match_email_to_contact(participant["email_address"], check_manual_mappings=False)
                    
                    if match:
                        updates.append({
                            "participant_id": participant["participant_id"],
                            "sf_contact_id": match["contact_id"],
                            "sf_account_id": match["account_id"],
                            "match_confidence": match["match_confidence"]
                        })
                        stats["matched"] += 1
                    else:
                        stats["unmatched"] += 1
                except Exception as e:
                    logger.error(f"Error matching participant {participant.get('participant_id')}: {e}")
                    stats["errors"] += 1
            
            # Batch update using MERGE statement
            if updates:
                self._batch_update_participants(updates)
            
            logger.info(f"Entity resolution batch: {stats}")
            
        except Exception as e:
            logger.error(f"Error in batch participant matching: {e}", exc_info=True)
            stats["errors"] += 1
        
        return stats
    
    def update_call_matches(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Batch update dialpad_calls with contact/account matches.
        
        Args:
            batch_size: Number of calls to process at once
        
        Returns:
            Dictionary with match statistics
        """
        stats = {
            "processed": 0,
            "matched": 0,
            "unmatched": 0,
            "errors": 0
        }
        
        # Get unmatched calls
        query = f"""
        SELECT 
            call_id,
            from_number,
            to_number
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls`
        WHERE matched_contact_id IS NULL
          AND (from_number IS NOT NULL OR to_number IS NOT NULL)
        LIMIT {batch_size}
        """
        
        try:
            calls = self.bq_client.query(query)
            
            updates = []
            for call in calls:
                try:
                    stats["processed"] += 1
                    
                    # Try to match from_number first, then to_number
                    phone = call.get("from_number") or call.get("to_number")
                    match = self.match_phone_to_contact_enhanced(phone, check_manual_mappings=False) if phone else None
                    
                    if match:
                        updates.append({
                            "call_id": call["call_id"],
                            "matched_contact_id": match["contact_id"],
                            "matched_account_id": match["account_id"]
                        })
                        stats["matched"] += 1
                    else:
                        stats["unmatched"] += 1
                except Exception as e:
                    logger.error(f"Error matching call {call.get('call_id')}: {e}")
                    stats["errors"] += 1
            
            # Batch update using MERGE statement
            if updates:
                self._batch_update_calls(updates)
            
            logger.info(f"Call entity resolution batch: {stats}")
            
        except Exception as e:
            logger.error(f"Error in batch call matching: {e}", exc_info=True)
            stats["errors"] += 1
        
        return stats
    
    def _batch_update_participants(self, updates: List[Dict[str, Any]]):
        """Batch update participants using MERGE statement."""
        if not updates:
            return
        
        # Build MERGE statement for batch update
        merge_query = f"""
        MERGE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants` AS target
        USING UNNEST(@updates) AS source
        ON target.participant_id = source.participant_id
        WHEN MATCHED THEN
          UPDATE SET
            sf_contact_id = source.sf_contact_id,
            sf_account_id = source.sf_account_id,
            match_confidence = source.match_confidence
        """
        
        # Convert updates to BigQuery-compatible format
        update_rows = [
            {
                "participant_id": u["participant_id"],
                "sf_contact_id": u.get("sf_contact_id"),
                "sf_account_id": u.get("sf_account_id"),
                "match_confidence": u.get("match_confidence")
            }
            for u in updates
        ]
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter(
                    "updates",
                    "STRUCT<participant_id STRING, sf_contact_id STRING, sf_account_id STRING, match_confidence STRING>[]",
                    update_rows
                )
            ]
        )
        
        try:
            self.bq_client.query(merge_query, job_config)
            logger.info(f"Updated {len(updates)} participant matches")
        except Exception as e:
            logger.error(f"Error batch updating participants: {e}", exc_info=True)
            # Fallback to individual updates if batch fails
            for update in updates:
                try:
                    update_query = f"""
                    UPDATE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants`
                    SET 
                      sf_contact_id = @contact_id,
                      sf_account_id = @account_id,
                      match_confidence = @confidence
                    WHERE participant_id = @participant_id
                    """
                    update_job_config = bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter("participant_id", "STRING", update["participant_id"]),
                            bigquery.ScalarQueryParameter("contact_id", "STRING", update.get("sf_contact_id")),
                            bigquery.ScalarQueryParameter("account_id", "STRING", update.get("sf_account_id")),
                            bigquery.ScalarQueryParameter("confidence", "STRING", update.get("match_confidence"))
                        ]
                    )
                    self.bq_client.query(update_query, update_job_config)
                except Exception as e2:
                    logger.error(f"Error updating participant {update.get('participant_id')}: {e2}")
    
    def _batch_update_calls(self, updates: List[Dict[str, Any]]):
        """Batch update calls using MERGE statement."""
        if not updates:
            return
        
        # Build MERGE statement for batch update
        merge_query = f"""
        MERGE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls` AS target
        USING UNNEST(@updates) AS source
        ON target.call_id = source.call_id
        WHEN MATCHED THEN
          UPDATE SET
            matched_contact_id = source.matched_contact_id,
            matched_account_id = source.matched_account_id
        """
        
        # Convert updates to BigQuery-compatible format
        update_rows = [
            {
                "call_id": u["call_id"],
                "matched_contact_id": u.get("matched_contact_id"),
                "matched_account_id": u.get("matched_account_id")
            }
            for u in updates
        ]
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter(
                    "updates",
                    "STRUCT<call_id STRING, matched_contact_id STRING, matched_account_id STRING>[]",
                    update_rows
                )
            ]
        )
        
        try:
            self.bq_client.query(merge_query, job_config)
            logger.info(f"Updated {len(updates)} call matches")
        except Exception as e:
            logger.error(f"Error batch updating calls: {e}", exc_info=True)
            # Fallback to individual updates if batch fails
            for update in updates:
                try:
                    update_query = f"""
                    UPDATE `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls`
                    SET 
                      matched_contact_id = @contact_id,
                      matched_account_id = @account_id
                    WHERE call_id = @call_id
                    """
                    update_job_config = bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter("call_id", "STRING", update["call_id"]),
                            bigquery.ScalarQueryParameter("contact_id", "STRING", update.get("matched_contact_id")),
                            bigquery.ScalarQueryParameter("account_id", "STRING", update.get("matched_account_id"))
                        ]
                    )
                    self.bq_client.query(update_query, update_job_config)
                except Exception as e2:
                    logger.error(f"Error updating call {update.get('call_id')}: {e2}")

