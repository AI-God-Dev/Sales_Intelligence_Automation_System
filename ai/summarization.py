"""
Unified Summarization Provider
Provides text summarization capabilities using LLM.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from ai.models import get_model_provider, ModelProvider

logger = logging.getLogger(__name__)


class SummarizationProvider(ABC):
    """Abstract base class for summarization providers."""
    
    @abstractmethod
    def summarize_emails(self, emails: List[Dict[str, Any]], timeframe: str = "daily") -> str:
        """Summarize a list of emails."""
        pass
    
    @abstractmethod
    def summarize_account_activity(self, account_data: Dict[str, Any], days: int = 7) -> str:
        """Summarize account activity over a period."""
        pass


class LLMSummarizationProvider(SummarizationProvider):
    """LLM-based summarization provider."""
    
    def __init__(self, model_provider: Optional[ModelProvider] = None):
        self.model_provider = model_provider or get_model_provider()
    
    def summarize_emails(self, emails: List[Dict[str, Any]], timeframe: str = "daily") -> str:
        """Summarize emails using LLM."""
        if not emails:
            return "No emails to summarize."
        
        # Build email content
        email_texts = []
        for email in emails:
            subject = email.get("subject", "No Subject")
            body = email.get("body_text", "") or email.get("body_html", "")
            from_email = email.get("from_email", "Unknown")
            sent_at = email.get("sent_at", "Unknown")
            
            email_texts.append(f"From: {from_email}\nDate: {sent_at}\nSubject: {subject}\n\n{body[:500]}...")
        
        prompt = f"""Summarize the following {timeframe} emails. Focus on:
- Key topics discussed
- Action items
- Important decisions
- Next steps

Emails:
{chr(10).join(email_texts)}"""
        
        system_prompt = "You are an expert email summarizer. Provide concise, actionable summaries."
        
        try:
            summary = self.model_provider.generate(prompt, system_prompt=system_prompt, max_tokens=1000)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing emails: {e}", exc_info=True)
            return f"Error generating summary: {str(e)}"
    
    def summarize_account_activity(self, account_data: Dict[str, Any], days: int = 7) -> str:
        """Summarize account activity using LLM."""
        prompt_parts = [f"Summarize account activity over the last {days} days:"]
        
        # Add emails
        emails = account_data.get("emails", [])
        if emails:
            prompt_parts.append(f"\nEmails ({len(emails)}):")
            for email in emails[:10]:
                prompt_parts.append(f"- {email.get('subject', 'N/A')} ({email.get('sent_at', 'N/A')})")
        
        # Add calls
        calls = account_data.get("calls", [])
        if calls:
            prompt_parts.append(f"\nCalls ({len(calls)}):")
            for call in calls[:5]:
                prompt_parts.append(f"- {call.get('direction', 'N/A')} call ({call.get('call_time', 'N/A')})")
        
        # Add opportunities
        opportunities = account_data.get("opportunities", [])
        if opportunities:
            prompt_parts.append(f"\nOpportunities ({len(opportunities)}):")
            for opp in opportunities:
                prompt_parts.append(f"- {opp.get('name', 'N/A')}: ${opp.get('amount', 0):,.0f} ({opp.get('stage', 'N/A')})")
        
        prompt = "\n".join(prompt_parts)
        system_prompt = "You are an expert sales analyst. Provide a concise summary of account activity, highlighting key interactions and opportunities."
        
        try:
            summary = self.model_provider.generate(prompt, system_prompt=system_prompt, max_tokens=1000)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing account activity: {e}", exc_info=True)
            return f"Error generating summary: {str(e)}"


def get_summarization_provider(
    model_provider: Optional[ModelProvider] = None
) -> SummarizationProvider:
    """Factory function to get summarization provider."""
    return LLMSummarizationProvider(model_provider)
