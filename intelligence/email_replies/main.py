"""
HTTP API endpoint for AI email reply generation.
"""
import functions_framework
import logging
from intelligence.email_replies.generator import EmailReplyGenerator
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


@functions_framework.http
def generate_email_reply(request):
    """
    HTTP endpoint for generating AI email replies.
    
    Expected request body:
    {
        "thread_id": "thread_123",
        "message_id": "msg_456",
        "reply_to_email": "customer@example.com",
        "account_id": "account_789" (optional),
        "access_token": "gmail_oauth_token" (optional, for sending)
        "send": false (optional, if true, sends the email)
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        thread_id = request_json.get("thread_id")
        message_id = request_json.get("message_id")
        reply_to_email = request_json.get("reply_to_email")
        account_id = request_json.get("account_id")
        access_token = request_json.get("access_token")
        send = request_json.get("send", False)
        
        if not thread_id or not message_id or not reply_to_email:
            return {
                "error": "thread_id, message_id, and reply_to_email are required"
            }, 400
        
        bq_client = BigQueryClient()
        generator = EmailReplyGenerator(bq_client)
        
        # Generate reply
        result = generator.generate_reply(
            thread_id,
            message_id,
            reply_to_email,
            account_id
        )
        
        if "error" in result:
            return result, 400
        
        # Send reply if requested
        if send and access_token:
            send_result = generator.send_reply(
                access_token,
                thread_id,
                result["reply_text"],
                message_id,
                reply_to_email,
                result["subject"]
            )
            
            if send_result.get("success"):
                result["sent"] = True
                result["sent_message_id"] = send_result.get("message_id")
            else:
                result["sent"] = False
                result["send_error"] = send_result.get("error")
        
        return result, 200
        
    except Exception as e:
        logger.error(f"Email reply generation failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

