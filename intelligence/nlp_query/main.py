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
            return {"error": "Query parameter is required"}, 400
        
        bq_client = BigQueryClient()
        generator = NLPQueryGenerator(bq_client)
        
        result = generator.execute_query(user_query)
        
        if "error" in result:
            return result, 400
        
        return result, 200
        
    except Exception as e:
        logger.error(f"NLP query failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

