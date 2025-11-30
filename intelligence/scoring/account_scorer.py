"""
Daily account scoring using LLM analysis.
Aggregates email, call, and activity data to generate priority scores.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import uuid
from google.cloud import bigquery
import warnings
from google.cloud import aiplatform
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

# Suppress pkg_resources deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.aiplatform")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")

# Conditional import for Anthropic (only if needed)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = setup_logger(__name__)


class AccountScorer:
    """Generate AI-powered account scores using LLM analysis."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        self.llm_model = settings.llm_model
        
        if settings.llm_provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured. Set 'anthropic-api-key' secret or use vertex_ai provider.")
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model = None
        elif settings.llm_provider == "vertex_ai":
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    warnings.filterwarnings("ignore", message=".*pkg_resources.*")
                    aiplatform.init(project=settings.gcp_project_id, location=settings.gcp_region)
                
                # Import vertexai first to ensure it's available
                import vertexai
                from vertexai.generative_models import GenerativeModel
                self.model = GenerativeModel(self.llm_model)
                self.client = None
            except ImportError as e:
                logger.error(f"Failed to import Vertex AI: {e}")
                raise ValueError(f"Vertex AI package not found. Ensure 'vertexai' package is installed. Error: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise ValueError(f"Vertex AI initialization failed: {e}. Ensure Vertex AI API is enabled and service account has permissions.")
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}. Use 'vertex_ai' or 'anthropic'.")
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with prompt and return response."""
        try:
            if settings.llm_provider == "anthropic":
                if not self.client:
                    raise ValueError("Anthropic client not initialized")
                message = self.client.messages.create(
                    model=self.llm_model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return message.content[0].text
            else:
                # Vertex AI
                if not self.model:
                    raise ValueError("Vertex AI model not initialized")
                # Combine system prompt and user prompt
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = self.model.generate_content(full_prompt)
                # Handle Vertex AI response format
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    return response.candidates[0].content.parts[0].text
                else:
                    raise ValueError(f"Unexpected Vertex AI response format: {response}")
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            raise
    
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
        
        account_info = self.bq_client.query(account_query, job_config=job_config)
        account_data = account_info[0] if account_info else {}
        
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
        
        # Build prompt for LLM
        prompt = self._build_scoring_prompt(account_data)
        
        system_prompt = """You are a sales intelligence analyst. Analyze account data and provide:
1. Priority Score (0-100): Overall priority based on engagement, opportunities, and buying signals
2. Budget Likelihood (0-100): Likelihood they're discussing 2026 budget based on communication signals
3. Engagement Score (0-100): Recent engagement level
4. Reasoning: Brief explanation of scores
5. Recommended Action: Next step to take
6. Key Signals: Array of detected buying signals

Respond in JSON format:
{
  "priority_score": <int>,
  "budget_likelihood": <int>,
  "engagement_score": <int>,
  "reasoning": "<string>",
  "recommended_action": "<string>",
  "key_signals": ["<signal1>", "<signal2>"]
}"""
        
        try:
            response = self._call_llm(prompt, system_prompt)
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                score_data = json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                logger.warning(f"Could not parse JSON from LLM response: {response}")
                score_data = {
                    "priority_score": 50,
                    "budget_likelihood": 50,
                    "engagement_score": 50,
                    "reasoning": "Unable to parse LLM response",
                    "recommended_action": "Review account manually",
                    "key_signals": []
                }
            
            # Determine last interaction date
            last_interaction = None
            if account_data.get("emails"):
                last_interaction = account_data["emails"][0].get("sent_at")
            if account_data.get("calls"):
                call_time = account_data["calls"][0].get("call_time")
                if not last_interaction or (call_time and call_time > last_interaction):
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
                "last_interaction_date": last_interaction.date().isoformat() if last_interaction else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error scoring account {account_id}: {e}", exc_info=True)
            raise
    
    def _build_scoring_prompt(self, account_data: Dict[str, Any]) -> str:
        """Build prompt for LLM scoring."""
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
    
    def score_all_accounts(self) -> int:
        """Score all active accounts. Returns count of accounts scored.
        
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
        count_result = self.bq_client.query(count_query)
        total_accounts = count_result[0]["total"] if count_result else 0
        logger.info(f"Scoring {total_accounts} accounts (processing one at a time to save memory)")
        
        scored_count = 0
        offset = 0
        chunk_size = 50  # Fetch 50 account IDs at a time from BigQuery
        
        while offset < total_accounts:
            # Fetch a chunk of account IDs
            query = f"""
            SELECT DISTINCT account_id
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts`
            WHERE account_id IS NOT NULL
            ORDER BY account_id
            LIMIT {chunk_size}
            OFFSET {offset}
            """
            
            accounts_chunk = self.bq_client.query(query)
            
            # Process each account one at a time and insert immediately
            for account in accounts_chunk:
                try:
                    account_id = account["account_id"]
                    recommendation = self.score_account(account_id)
                    
                    # Insert immediately (one at a time) to free memory
                    self.bq_client.insert_rows("account_recommendations", [recommendation])
                    scored_count += 1
                    
                    # Force garbage collection every 5 accounts
                    if scored_count % 5 == 0:
                        gc.collect()
                        logger.info(f"Processed {scored_count}/{total_accounts} accounts")
                    
                except Exception as e:
                    logger.error(f"Failed to score account {account.get('account_id')}: {e}")
                    # Continue with next account even if one fails
            
            offset += chunk_size
            # Force garbage collection after each chunk
            gc.collect()
        
        logger.info(f"Completed scoring {scored_count} accounts")
        return scored_count


