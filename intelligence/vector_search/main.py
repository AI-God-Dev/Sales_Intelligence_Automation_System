"""
Cloud Function for semantic search using BigQuery Vector Search.
"""
import functions_framework
import logging
from intelligence.vector_search.semantic_search import SemanticSearch
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


@functions_framework.http
def semantic_search(request):
    """
    HTTP endpoint for semantic search.
    
    Expected request body:
    {
        "query": "accounts discussing budget for 2026",
        "type": "emails" | "calls" | "accounts" (default: "accounts"),
        "limit": 50 (optional),
        "days_back": 60 (optional),
        "min_similarity": 0.7 (optional)
    }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        query_text = request_json.get("query")
        search_type = request_json.get("type", "accounts")
        limit = request_json.get("limit", 50)
        days_back = request_json.get("days_back", 60)
        min_similarity = request_json.get("min_similarity", 0.7)
        
        if not query_text:
            return {"error": "query parameter is required"}, 400
        
        bq_client = BigQueryClient()
        searcher = SemanticSearch(bq_client)
        
        if search_type == "emails":
            results = searcher.search_emails_by_intent(
                query_text, limit=limit, days_back=days_back, min_similarity=min_similarity
            )
        elif search_type == "calls":
            results = searcher.search_calls_by_intent(
                query_text, limit=limit, days_back=days_back, min_similarity=min_similarity
            )
        else:  # accounts
            results = searcher.search_accounts_by_intent(
                query_text, limit=limit, days_back=days_back
            )
        
        return {
            "query": query_text,
            "type": search_type,
            "results": results,
            "count": len(results)
        }, 200
        
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

