"""
Daily account scoring using LLM analysis.
Aggregates email, call, and activity data to generate priority scores.
Uses unified AI abstraction layer for provider-agnostic LLM calls.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import uuid
from google.cloud import bigquery
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings
from ai.models import get_model_provider, ModelProvider
from ai.scoring import get_scoring_provider, ScoringProvider

logger = setup_logger(__name__)


class AccountScorer:
    """Generate AI-powered account scores using LLM analysis."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None, model_provider: Optional[ModelProvider] = None, scoring_provider: Optional[ScoringProvider] = None):
        self.bq_client = bq_client or BigQueryClient()
        # Use provided providers or get from factory (respects MOCK_MODE/LOCAL_MODE)
        self.model_provider = model_provider or get_model_provider(
            provider=settings.llm_provider,
            project_id=settings.gcp_project_id,
            region=settings.gcp_region,
            model_name=settings.llm_model,
            api_key=getattr(settings, 'anthropic_api_key', None) if settings.llm_provider == 'anthropic' else (getattr(settings, 'openai_api_key', None) if settings.llm_provider == 'openai' else None)
        )
        self.scoring_provider = scoring_provider or get_scoring_provider(model_provider=self.model_provider, bq_client=self.bq_client)
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with prompt and return response using unified abstraction."""
        return self.model_provider.generate(prompt, system_prompt=system_prompt, max_tokens=2000)
    
    def get_account_data(self, account_id: str) -> Dict[str, Any]:
        """Aggregate all relevant data for an account."""
        # Get last 5 emails
        email_query = f"""
        SELECT 
            m.subject,
            m.body_text,
            m.sent_at,
            m.from_email
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages` m
        JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants` p
          ON m.message_id = p.message_id
        WHERE p.sf_account_id = @account_id
          AND m.sent_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        ORDER BY m.sent_at DESC
        LIMIT 5
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("account_id", "STRING", account_id)
            ]
        )
        emails = self.bq_client.query(email_query, job_config=job_config)
        
        # Get last 3 calls
        call_query = f"""
        SELECT 
            transcript_text,
            sentiment_score,
            call_time,
            direction
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.dialpad_calls`
        WHERE matched_account_id = @account_id
          AND call_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        ORDER BY call_time DESC
        LIMIT 3
        """
        
        calls = self.bq_client.query(call_query, job_config=job_config)
        
        # Get open opportunities
        opp_query = f"""
        SELECT 
            name,
            stage,
            amount,
            close_date,
            probability
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_opportunities`
        WHERE account_id = @account_id
          AND is_closed = FALSE
        ORDER BY amount DESC
        """
        
        opportunities = self.bq_client.query(opp_query, job_config=job_config)
        
        # Get recent activities
        activity_query = f"""
        SELECT 
            activity_type,
            subject,
            description,
            activity_date
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_activities`
        WHERE matched_account_id = @account_id
          AND activity_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY activity_date DESC
        LIMIT 10
        """
        
        activities = self.bq_client.query(activity_query, job_config=job_config)
        
        # Get account info
        account_query = f"""
        SELECT 
            account_name,
            industry,
            annual_revenue
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts`
        WHERE account_id = @account_id
        """
        
        try:
            account_info = self.bq_client.query(account_query, job_config=job_config)
            account_data = account_info[0] if account_info and len(account_info) > 0 else {}
        except Exception as e:
            logger.warning(f"Failed to get account info for {account_id}: {e}")
            account_data = {}
        
        return {
            "account_id": account_id,
            "account_name": account_data.get("account_name", ""),
            "industry": account_data.get("industry", ""),
            "annual_revenue": account_data.get("annual_revenue", 0),
            "emails": emails,
            "calls": calls,
            "opportunities": opportunities,
            "activities": activities
        }
    
    def score_account(self, account_id: str) -> Dict[str, Any]:
        """Generate score for a single account using LLM."""
        logger.info(f"Scoring account {account_id}")
        
        account_data = self.get_account_data(account_id)
        
        # Use unified scoring provider
        try:
            score_data = self.scoring_provider.score_account(account_id, account_data)
            # Score data is already validated by scoring provider
            
            # Determine last interaction date
            last_interaction = None
            
            # Helper function to parse date/datetime
            def parse_datetime(value):
                """Parse datetime from various formats."""
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    try:
                        from dateutil import parser
                        return parser.parse(value)
                    except:
                        try:
                            # Try ISO format
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            logger.warning(f"Could not parse datetime: {value}")
                            return None
                return None
            
            # Check emails (list of dicts from BigQuery)
            if account_data.get("emails") and len(account_data["emails"]) > 0:
                email_date = account_data["emails"][0].get("sent_at")
                email_date = parse_datetime(email_date)
                if email_date and (not last_interaction or email_date > last_interaction):
                    last_interaction = email_date
            
            # Check calls (list of dicts from BigQuery)
            if account_data.get("calls") and len(account_data["calls"]) > 0:
                call_time = account_data["calls"][0].get("call_time")
                call_time = parse_datetime(call_time)
                if call_time and (not last_interaction or call_time > last_interaction):
                    last_interaction = call_time
            
            return {
                "recommendation_id": str(uuid.uuid4()),
                "account_id": account_id,
                "score_date": datetime.now(timezone.utc).date().isoformat(),
                "priority_score": score_data.get("priority_score", 50),
                "budget_likelihood": score_data.get("budget_likelihood", 50),
                "engagement_score": score_data.get("engagement_score", 50),
                "reasoning": score_data.get("reasoning", ""),
                "recommended_action": score_data.get("recommended_action", ""),
                "key_signals": score_data.get("key_signals", []),
                "last_interaction_date": last_interaction.date().isoformat() if last_interaction and hasattr(last_interaction, 'date') else (last_interaction.isoformat()[:10] if last_interaction else None),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error scoring account {account_id}: {e}", exc_info=True)
            raise
    
    def _build_scoring_prompt(self, account_data: Dict[str, Any]) -> str:
        """Build prompt for LLM scoring. Used by scoring provider internally."""
        # This method is kept for backward compatibility but scoring provider has its own
        # The scoring provider's _build_scoring_prompt is used instead
        prompt_parts = [
            f"Account: {account_data.get('account_name', 'Unknown')}",
            f"Industry: {account_data.get('industry', 'Unknown')}",
            f"Annual Revenue: ${account_data.get('annual_revenue', 0):,.0f}" if account_data.get('annual_revenue') else "",
        ]
        
        # Add opportunities
        if account_data.get("opportunities"):
            prompt_parts.append("\nOpen Opportunities:")
            for opp in account_data["opportunities"]:
                prompt_parts.append(
                    f"- {opp.get('name')}: Stage={opp.get('stage')}, "
                    f"Amount=${opp.get('amount', 0):,.0f}, "
                    f"Probability={opp.get('probability', 0)}%, "
                    f"Close Date={opp.get('close_date')}"
                )
        
        # Add recent emails
        if account_data.get("emails"):
            prompt_parts.append("\nRecent Emails (last 5):")
            for email in account_data["emails"]:
                subject = email.get('subject', 'No subject')
                body_preview = (email.get('body_text', '') or '')[:200]
                prompt_parts.append(f"- Subject: {subject}")
                prompt_parts.append(f"  Preview: {body_preview}...")
                prompt_parts.append(f"  Date: {email.get('sent_at')}")
        
        # Add recent calls
        if account_data.get("calls"):
            prompt_parts.append("\nRecent Calls (last 3):")
            for call in account_data["calls"]:
                transcript_preview = (call.get('transcript_text', '') or '')[:200]
                sentiment = call.get('sentiment_score', 0)
                prompt_parts.append(
                    f"- Direction: {call.get('direction')}, "
                    f"Sentiment: {sentiment:.2f}, "
                    f"Date: {call.get('call_time')}"
                )
                if transcript_preview:
                    prompt_parts.append(f"  Transcript preview: {transcript_preview}...")
        
        # Add recent activities
        if account_data.get("activities"):
            prompt_parts.append("\nRecent Activities:")
            for activity in account_data["activities"][:5]:
                prompt_parts.append(
                    f"- {activity.get('activity_type')}: {activity.get('subject')} "
                    f"({activity.get('activity_date')})"
                )
        
        prompt_parts.append(
            "\nAnalyze this account and provide scores based on engagement, "
            "budget signals, and buying intent."
        )
        
        return "\n".join(prompt_parts)
    
    def score_all_accounts(self, limit: Optional[int] = None) -> int:
        """Score active accounts. Returns count of accounts scored.
        
        Args:
            limit: Optional limit on number of accounts to score (for testing).
                  If None, scores all accounts.
        
        Memory-optimized: Processes accounts one at a time and inserts immediately
        to prevent memory overflow.
        """
        import gc
        
        # First, get total count for logging
        count_query = f"""
        SELECT COUNT(DISTINCT account_id) as total
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts`
        WHERE account_id IS NOT NULL
        """
        try:
            count_result = self.bq_client.query(count_query)
            total_accounts = count_result[0]["total"] if count_result and len(count_result) > 0 else 0
        except Exception as e:
            logger.error(f"Failed to get account count: {e}")
            raise ValueError(f"Cannot determine account count: {e}")
        
        if total_accounts == 0:
            logger.warning("No accounts found to score")
            return 0
        
        # Apply limit if specified
        max_accounts = limit if limit is not None and limit > 0 else total_accounts
        accounts_to_score = min(max_accounts, total_accounts)
        
        if limit:
            logger.info(f"Scoring {accounts_to_score} accounts (limited from {total_accounts} total)")
        else:
            logger.info(f"Scoring {accounts_to_score} accounts (processing one at a time to save memory)")
        
        scored_count = 0
        failed_count = 0
        offset = 0
        chunk_size = 50  # Fetch 50 account IDs at a time from BigQuery
        
        while offset < accounts_to_score:
            # Fetch a chunk of account IDs
            query = f"""
            SELECT DISTINCT account_id
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts`
            WHERE account_id IS NOT NULL
            ORDER BY account_id
            LIMIT {chunk_size}
            OFFSET {offset}
            """
            
            try:
                accounts_chunk = self.bq_client.query(query)
            except Exception as e:
                logger.error(f"Failed to fetch account chunk (offset {offset}): {e}")
                failed_count += chunk_size
                offset += chunk_size
                continue
            
            if not accounts_chunk or len(accounts_chunk) == 0:
                logger.info(f"No more accounts to process at offset {offset}")
                break
            
            # Process each account one at a time and insert immediately
            for account in accounts_chunk:
                try:
                    account_id = account.get("account_id")
                    if not account_id:
                        logger.warning(f"Skipping account with no account_id: {account}")
                        failed_count += 1
                        continue
                    
                    recommendation = self.score_account(account_id)
                    
                    # Insert immediately (one at a time) to free memory
                    self.bq_client.insert_rows("account_recommendations", [recommendation])
                    scored_count += 1
                    
                    # Force garbage collection every 5 accounts
                    if scored_count % 5 == 0:
                        gc.collect()
                        logger.info(f"Processed {scored_count}/{total_accounts} accounts (failed: {failed_count})")
                    
                except Exception as e:
                    failed_count += 1
                    account_id = account.get('account_id', 'unknown')
                    logger.error(f"Failed to score account {account_id}: {e}", exc_info=True)
                    # Continue with next account even if one fails
            
            offset += chunk_size
            # Force garbage collection after each chunk
            gc.collect()
        
        logger.info(f"Completed scoring {scored_count} accounts (failed: {failed_count}, total: {total_accounts})")
        
        if scored_count == 0 and total_accounts > 0:
            raise ValueError(f"Failed to score any accounts. {failed_count} failures out of {total_accounts} total accounts.")
        
        return scored_count


