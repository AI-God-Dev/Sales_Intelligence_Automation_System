"""
Unified Scoring Provider
Provides account scoring capabilities using LLM analysis.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from ai.models import get_model_provider, ModelProvider
from utils.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class ScoringProvider(ABC):
    """Abstract base class for scoring providers."""
    
    @abstractmethod
    def score_account(self, account_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score an account based on aggregated data."""
        pass


class LLMScoringProvider(ScoringProvider):
    """LLM-based account scoring provider."""
    
    def __init__(
        self,
        model_provider: Optional[ModelProvider] = None,
        bq_client: Optional[BigQueryClient] = None
    ):
        self.model_provider = model_provider or get_model_provider()
        self.bq_client = bq_client or BigQueryClient()
        # Store project_id and dataset_id for convenience
        self.project_id = self.bq_client.project_id
        self.dataset_id = self.bq_client.dataset_id
    
    def score_account(self, account_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score account using LLM analysis."""
        # Build prompt from account data
        prompt = self._build_scoring_prompt(account_data)
        
        system_prompt = """You are an expert sales analyst. Analyze the provided account data and generate a JSON response with:
- priority_score: integer 0-100 (overall priority)
- budget_likelihood: integer 0-100 (likelihood discussing 2026 budget)
- engagement_score: integer 0-100 (recent engagement level)
- reasoning: string (explanation of scores)
- recommended_action: string (suggested next step)
- key_signals: array of strings (detected buying signals)

Return ONLY valid JSON, no additional text."""
        
        try:
            # Use Vertex AI Gemini's structured JSON output capability
            response = self.model_provider.generate(
                prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent JSON output
            )
            
            # Parse JSON response
            # Sometimes LLM wraps JSON in markdown code blocks
            response = response.strip()
            if response.startswith("```"):
                # Extract JSON from code block
                lines = response.split("\n")
                json_lines = [l for l in lines if not l.strip().startswith("```")]
                response = "\n".join(json_lines)
            
            score_data = json.loads(response)
            
            # Validate and normalize scores
            return {
                "priority_score": min(100, max(0, int(score_data.get("priority_score", 50)))),
                "budget_likelihood": min(100, max(0, int(score_data.get("budget_likelihood", 50)))),
                "engagement_score": min(100, max(0, int(score_data.get("engagement_score", 50)))),
                "reasoning": str(score_data.get("reasoning", "")),
                "recommended_action": str(score_data.get("recommended_action", "")),
                "key_signals": list(score_data.get("key_signals", []))
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM scoring response: {e}")
            logger.error(f"Response was: {response}")
            # Return default scores
            return {
                "priority_score": 50,
                "budget_likelihood": 50,
                "engagement_score": 50,
                "reasoning": "Error parsing LLM response",
                "recommended_action": "Review account manually",
                "key_signals": []
            }
        except Exception as e:
            logger.error(f"Error in account scoring: {e}", exc_info=True)
            raise
    
    def _build_scoring_prompt(self, account_data: Dict[str, Any]) -> str:
        """Build prompt from account data."""
        prompt_parts = []
        
        # Account info
        if account_data.get("account_name"):
            prompt_parts.append(f"Account: {account_data['account_name']}")
        if account_data.get("industry"):
            prompt_parts.append(f"Industry: {account_data['industry']}")
        if account_data.get("annual_revenue"):
            prompt_parts.append(f"Annual Revenue: ${account_data['annual_revenue']:,.0f}")
        
        # Recent emails
        emails = account_data.get("emails", [])
        if emails:
            prompt_parts.append("\nRecent Emails:")
            for email in emails[:5]:
                prompt_parts.append(f"- Subject: {email.get('subject', 'N/A')}")
                prompt_parts.append(f"  From: {email.get('from_email', 'N/A')}")
                prompt_parts.append(f"  Date: {email.get('sent_at', 'N/A')}")
                body_preview = (email.get('body_text', '') or '')[:200]
                if body_preview:
                    prompt_parts.append(f"  Preview: {body_preview}...")
        
        # Recent calls
        calls = account_data.get("calls", [])
        if calls:
            prompt_parts.append("\nRecent Calls:")
            for call in calls[:3]:
                prompt_parts.append(f"- Date: {call.get('call_time', 'N/A')}")
                prompt_parts.append(f"  Direction: {call.get('direction', 'N/A')}")
                prompt_parts.append(f"  Sentiment: {call.get('sentiment_score', 'N/A')}")
                transcript_preview = (call.get('transcript_text', '') or '')[:200]
                if transcript_preview:
                    prompt_parts.append(f"  Preview: {transcript_preview}...")
        
        # Opportunities
        opportunities = account_data.get("opportunities", [])
        if opportunities:
            prompt_parts.append("\nOpen Opportunities:")
            for opp in opportunities:
                prompt_parts.append(f"- {opp.get('name', 'N/A')}: ${opp.get('amount', 0):,.0f}")
                prompt_parts.append(f"  Stage: {opp.get('stage', 'N/A')}")
                prompt_parts.append(f"  Probability: {opp.get('probability', 0)}%")
        
        # Activities
        activities = account_data.get("activities", [])
        if activities:
            prompt_parts.append("\nRecent Activities:")
            for activity in activities[:5]:
                prompt_parts.append(f"- {activity.get('activity_type', 'N/A')}: {activity.get('subject', 'N/A')}")
                prompt_parts.append(f"  Date: {activity.get('activity_date', 'N/A')}")
        
        prompt_parts.append("\nAnalyze this account and provide scores based on engagement, budget signals, and buying intent.")
        
        return "\n".join(prompt_parts)


def get_scoring_provider(
    model_provider: Optional[ModelProvider] = None,
    bq_client: Optional[BigQueryClient] = None
) -> ScoringProvider:
    """Factory function to get scoring provider."""
    return LLMScoringProvider(model_provider, bq_client)
