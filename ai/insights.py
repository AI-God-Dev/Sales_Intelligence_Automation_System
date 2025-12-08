"""
Unified Insights Provider
Provides AI-powered insights generation for accounts and opportunities.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from ai.models import get_model_provider, ModelProvider

logger = logging.getLogger(__name__)


class InsightsProvider(ABC):
    """Abstract base class for insights providers."""
    
    @abstractmethod
    def generate_account_insights(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights for an account."""
        pass
    
    @abstractmethod
    def detect_risks(self, account_data: Dict[str, Any]) -> List[str]:
        """Detect risks for an account."""
        pass
    
    @abstractmethod
    def detect_opportunities(self, account_data: Dict[str, Any]) -> List[str]:
        """Detect opportunities for an account."""
        pass


class LLMInsightsProvider(InsightsProvider):
    """LLM-based insights provider."""
    
    def __init__(self, model_provider: Optional[ModelProvider] = None):
        self.model_provider = model_provider or get_model_provider()
    
    def generate_account_insights(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights for an account."""
        prompt = self._build_insights_prompt(account_data)
        
        system_prompt = """You are an expert sales strategist. Analyze the account data and provide insights in JSON format:
{
  "strengths": ["strength1", "strength2"],
  "risks": ["risk1", "risk2"],
  "opportunities": ["opportunity1", "opportunity2"],
  "recommendations": ["recommendation1", "recommendation2"],
  "key_metrics": {
    "engagement_trend": "increasing/decreasing/stable",
    "budget_signals": "strong/moderate/weak",
    "decision_timeline": "immediate/30_days/90_days/unknown"
  }
}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.model_provider.generate(
                prompt,
                system_prompt=system_prompt,
                max_tokens=2000
            )
            
            # Parse JSON response
            import json
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                json_lines = [l for l in lines if not l.strip().startswith("```")]
                response = "\n".join(json_lines)
            
            insights = json.loads(response)
            
            return {
                "strengths": list(insights.get("strengths", [])),
                "risks": list(insights.get("risks", [])),
                "opportunities": list(insights.get("opportunities", [])),
                "recommendations": list(insights.get("recommendations", [])),
                "key_metrics": dict(insights.get("key_metrics", {}))
            }
        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
            return {
                "strengths": [],
                "risks": [],
                "opportunities": [],
                "recommendations": [],
                "key_metrics": {}
            }
    
    def detect_risks(self, account_data: Dict[str, Any]) -> List[str]:
        """Detect risks for an account."""
        insights = self.generate_account_insights(account_data)
        return insights.get("risks", [])
    
    def detect_opportunities(self, account_data: Dict[str, Any]) -> List[str]:
        """Detect opportunities for an account."""
        insights = self.generate_account_insights(account_data)
        return insights.get("opportunities", [])
    
    def _build_insights_prompt(self, account_data: Dict[str, Any]) -> str:
        """Build prompt for insights generation."""
        prompt_parts = ["Analyze this account and provide insights:"]
        
        if account_data.get("account_name"):
            prompt_parts.append(f"\nAccount: {account_data['account_name']}")
        
        # Add key data points
        emails = account_data.get("emails", [])
        calls = account_data.get("calls", [])
        opportunities = account_data.get("opportunities", [])
        
        prompt_parts.append(f"\nData Summary:")
        prompt_parts.append(f"- Recent emails: {len(emails)}")
        prompt_parts.append(f"- Recent calls: {len(calls)}")
        prompt_parts.append(f"- Open opportunities: {len(opportunities)}")
        
        # Add sample content
        if emails:
            prompt_parts.append(f"\nSample email subjects:")
            for email in emails[:5]:
                prompt_parts.append(f"- {email.get('subject', 'N/A')}")
        
        if opportunities:
            prompt_parts.append(f"\nOpportunities:")
            for opp in opportunities:
                prompt_parts.append(f"- {opp.get('name', 'N/A')}: ${opp.get('amount', 0):,.0f} ({opp.get('stage', 'N/A')})")
        
        return "\n".join(prompt_parts)


def get_insights_provider(
    model_provider: Optional[ModelProvider] = None
) -> InsightsProvider:
    """Factory function to get insights provider."""
    return LLMInsightsProvider(model_provider)
