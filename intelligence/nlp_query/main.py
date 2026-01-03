"""
HTTP API endpoint for natural language queries.
"""
import functions_framework
import logging
from intelligence.nlp_query.query_generator import NLPQueryGenerator
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


@functions_framework.http
def nlp_query(request):
    """
    HTTP endpoint for natural language queries.
    
    Expected request body:
    {
        "query": "Show me accounts with high engagement in the last week"
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        user_query = request_json.get("query")
        
        if not user_query:
            return {
                "error": "Query parameter is required",
                "error_type": "validation_error"
            }, 400
        
        # Validate input length
        if len(user_query) > 1000:
            return {
                "error": "Query is too long (maximum 1000 characters)",
                "error_type": "validation_error"
            }, 400
        
        bq_client = BigQueryClient()
        generator = NLPQueryGenerator(bq_client)
        
        result = generator.execute_query(user_query)
        
        if "error" in result:
            # Return appropriate status code based on error type
            status_code = 400
            if result.get("error_type") == "model_not_found":
                status_code = 503  # Service unavailable
            elif result.get("error_type") == "permission_error":
                status_code = 403  # Forbidden
            return result, status_code
        
        return result, 200
        
    except Exception as e:
        logger.error(f"NLP query failed: {str(e)}", exc_info=True)
        error_str = str(e).lower()
        
        # Provide helpful error messages
        if "404" in error_str or "not found" in error_str:
            error_type = "model_not_found"
            suggestion = (
                "The AI model may not be configured correctly. "
                "Please check LLM_MODEL environment variable and Vertex AI API access."
            )
        else:
            error_type = "unknown_error"
            suggestion = "Please check the logs for more details."
        
        return {
            "error": str(e),
            "error_type": error_type,
            "suggestion": suggestion
        }, 500

