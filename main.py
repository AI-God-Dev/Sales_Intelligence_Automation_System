"""
Root-level main.py for Gen2 Cloud Functions deployment.
This file makes all intelligence functions available for deployment.
"""
# Import all function entry points so they can be used as entry points
from intelligence.embeddings.main import generate_embeddings
from intelligence.scoring.main import account_scoring_job
from intelligence.nlp_query.main import nlp_query
from intelligence.automation.main import create_leads, enroll_hubspot, get_hubspot_sequences
from intelligence.email_replies.main import generate_email_reply
from intelligence.vector_search.main import semantic_search

# Re-export for easier access
__all__ = [
    'generate_embeddings',
    'account_scoring_job',
    'nlp_query',
    'create_leads',
    'enroll_hubspot',
    'get_hubspot_sequences',
    'generate_email_reply',
    'semantic_search'
]
