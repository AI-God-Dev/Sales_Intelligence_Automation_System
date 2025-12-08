"""
Root-level entrypoints for Cloud Functions Gen2 deployments.

Cloud Functions Gen2 resolves targets from this file only. We re-export all
deployable functions here so deployments must always use:

    --entry-point=<function_name>

Never use module paths in --entry-point for Gen2.
"""

# Ingestion / sync Cloud Functions (Gen2 requires root-level exports)
from cloud_functions.gmail_sync.main import gmail_sync
from cloud_functions.salesforce_sync.main import salesforce_sync
from cloud_functions.dialpad_sync.main import dialpad_sync
from cloud_functions.hubspot_sync.main import hubspot_sync
from cloud_functions.entity_resolution.main import entity_resolution

# Intelligence / AI jobs (Vertex-only)
from intelligence.scoring.main import account_scoring_job
from intelligence.vector_search.main import semantic_search
from intelligence.email_replies.main import generate_email_reply
from intelligence.automation.main import enroll_hubspot, get_hubspot_sequences, create_leads
from intelligence.embeddings.main import generate_embeddings
from intelligence.nlp_query.main import nlp_query

# Public exports for functions-framework / gcloud --entry-point
__all__ = [
    "gmail_sync",
    "salesforce_sync",
    "dialpad_sync",
    "hubspot_sync",
    "entity_resolution",
    "account_scoring_job",
    "semantic_search",
    "generate_email_reply",
    "enroll_hubspot",
    "get_hubspot_sequences",
    "create_leads",
    "generate_embeddings",
    "nlp_query",
]
