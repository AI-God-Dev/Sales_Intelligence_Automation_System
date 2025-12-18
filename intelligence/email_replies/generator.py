"""
AI email reply generation with context retrieval.
Generates contextual email replies using LLM with full conversation history.
Uses unified AI abstraction layer for provider-agnostic LLM calls.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings
from ai.models import get_model_provider, ModelProvider

logger = setup_logger(__name__)


class EmailReplyGenerator:
    """Generate AI-powered email replies with context."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None, model_provider: Optional[ModelProvider] = None):
        self.bq_client = bq_client or BigQueryClient()
        # Use provided provider or get from factory (respects MOCK_MODE/LOCAL_MODE)
        # Vertex AI uses Application Default Credentials - no API key needed
        self.model_provider = model_provider or get_model_provider(
            provider=settings.llm_provider,
            project_id=settings.gcp_project_id,
            region=settings.gcp_region,
            model_name=settings.llm_model
        )
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with prompt and return response using unified abstraction."""
        return self.model_provider.generate(prompt, system_prompt=system_prompt, max_tokens=2000)
    
    def get_email_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all emails in a thread from BigQuery."""
        query = f"""
        SELECT 
            message_id,
            from_email,
            to_emails,
            subject,
            body_text,
            sent_at,
            mailbox_email
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages`
        WHERE thread_id = @thread_id
        ORDER BY sent_at ASC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("thread_id", "STRING", thread_id)
            ]
        )
        
        return self.bq_client.query(query, job_config=job_config)
    
    def get_account_context(self, account_id: Optional[str]) -> str:
        """Get account context for email reply."""
        if not account_id:
            return ""
        
        query = f"""
        SELECT 
            account_name,
            industry,
            annual_revenue
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.sf_accounts`
        WHERE account_id = @account_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("account_id", "STRING", account_id)
            ]
        )
        
        accounts = self.bq_client.query(query, job_config=job_config)
        if not accounts:
            return ""
        
        account = accounts[0]
        context = f"Account: {account.get('account_name', 'Unknown')}"
        if account.get('industry'):
            context += f"\nIndustry: {account['industry']}"
        if account.get('annual_revenue'):
            context += f"\nAnnual Revenue: ${account['annual_revenue']:,.0f}"
        
        return context
    
    def get_recent_interactions(self, email: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent interactions with this email address."""
        query = f"""
        SELECT 
            m.subject,
            m.body_text,
            m.sent_at,
            m.mailbox_email as direction
        FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_messages` m
        JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_id}.gmail_participants` p
          ON m.message_id = p.message_id
        WHERE p.email_address = @email
          AND m.sent_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY m.sent_at DESC
        LIMIT {limit}
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email.lower())
            ]
        )
        
        return self.bq_client.query(query, job_config=job_config)
    
    def generate_reply(
        self,
        thread_id: str,
        message_id: str,
        reply_to_email: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI email reply with full context."""
        logger.info(f"Generating reply for thread {thread_id}, message {message_id}")
        
        # Get thread context
        thread_emails = self.get_email_thread(thread_id)
        
        if not thread_emails:
            return {
                "error": "Thread not found"
            }
        
        # Find the specific message
        current_message = None
        for msg in thread_emails:
            if msg['message_id'] == message_id:
                current_message = msg
                break
        
        if not current_message:
            return {
                "error": "Message not found in thread"
            }
        
        # Get account context
        account_context = self.get_account_context(account_id)
        
        # Get recent interactions
        recent_interactions = self.get_recent_interactions(reply_to_email)
        
        # Build prompt
        prompt = self._build_reply_prompt(
            thread_emails,
            current_message,
            account_context,
            recent_interactions
        )
        
        system_prompt = """You are a professional sales representative writing an email reply.
Guidelines:
1. Be professional, friendly, and helpful
2. Address the sender's questions directly
3. Reference relevant context from the conversation
4. Keep it concise (2-3 paragraphs max)
5. Include a clear call-to-action if appropriate
6. Match the tone of the conversation
7. Do NOT include email headers, subject, or signatures - just the body text"""
        
        try:
            reply_text = self._call_llm(prompt, system_prompt)
            
            return {
                "success": True,
                "reply_text": reply_text.strip(),
                "thread_id": thread_id,
                "message_id": message_id,
                "reply_to": reply_to_email,
                "subject": f"Re: {current_message.get('subject', '')}"
            }
        except Exception as e:
            logger.error(f"Error generating reply: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_reply_prompt(
        self,
        thread_emails: List[Dict[str, Any]],
        current_message: Dict[str, Any],
        account_context: str,
        recent_interactions: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM reply generation."""
        prompt_parts = []
        
        if account_context:
            prompt_parts.append(f"Account Context:\n{account_context}\n")
        
        prompt_parts.append("Email Thread (in chronological order):\n")
        
        for email in thread_emails:
            sender = email.get('from_email', 'Unknown')
            subject = email.get('subject', 'No subject')
            body = email.get('body_text', '')[:500]  # Limit body length
            sent_at = email.get('sent_at', '')
            
            prompt_parts.append(f"From: {sender}")
            prompt_parts.append(f"Subject: {subject}")
            prompt_parts.append(f"Date: {sent_at}")
            prompt_parts.append(f"Body: {body}")
            prompt_parts.append("---")
        
        if recent_interactions:
            prompt_parts.append("\nRecent Interactions with this contact (last 30 days):\n")
            for interaction in recent_interactions[:3]:
                subject = interaction.get('subject', 'No subject')
                direction = "Sent by us" if interaction.get('direction') in settings.gmail_mailboxes else "Received"
                prompt_parts.append(f"- {direction}: {subject} ({interaction.get('sent_at')})")
        
        prompt_parts.append(
            f"\nPlease generate a professional email reply to the most recent message in this thread. "
            f"The most recent message is from: {current_message.get('from_email', '')}"
        )
        
        return "\n".join(prompt_parts)
    
    def send_reply(
        self,
        access_token: str,
        thread_id: str,
        reply_text: str,
        reply_to_message_id: str,
        to_email: str,
        subject: str
    ) -> Dict[str, Any]:
        """Send the generated reply via Gmail API."""
        try:
            # Build Gmail service
            credentials = Credentials(token=access_token)
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create email message
            message_body = {
                'raw': self._create_message_raw(
                    to_email,
                    subject,
                    reply_text,
                    thread_id,
                    reply_to_message_id
                )
            }
            
            # Send message
            message = service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()
            
            logger.info(f"Sent reply message {message.get('id')}")
            
            return {
                "success": True,
                "message_id": message.get('id'),
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"Error sending reply: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_message_raw(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        thread_id: str,
        reply_to_message_id: str
    ) -> str:
        """Create raw email message for Gmail API."""
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(body_text)
        message['To'] = to_email
        message['Subject'] = subject
        message['In-Reply-To'] = reply_to_message_id
        message['References'] = reply_to_message_id
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return raw_message

