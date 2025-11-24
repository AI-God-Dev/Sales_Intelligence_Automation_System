"""
Natural language to SQL query generator with safety validation.
Converts user questions to BigQuery SQL queries.
"""
import logging
import re
import warnings
from typing import Dict, Any, Optional, Tuple
import anthropic
from google.cloud import bigquery
from google.cloud import aiplatform
from utils.bigquery_client import BigQueryClient
from utils.logger import setup_logger
from config.config import settings

# Suppress pkg_resources deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.aiplatform")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")

logger = setup_logger(__name__)

# Allowed table names for safety
ALLOWED_TABLES = [
    "gmail_messages",
    "gmail_participants",
    "sf_accounts",
    "sf_contacts",
    "sf_leads",
    "sf_opportunities",
    "sf_activities",
    "dialpad_calls",
    "account_recommendations",
    "hubspot_sequences",
    "v_unmatched_emails"  # Views are allowed
]

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "--", "/*", "*/"
]


class NLPQueryGenerator:
    """Convert natural language queries to BigQuery SQL with safety checks."""
    
    def __init__(self, bq_client: Optional[BigQueryClient] = None):
        self.bq_client = bq_client or BigQueryClient()
        self.llm_model = settings.llm_model
        
        if settings.llm_provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        elif settings.llm_provider == "vertex_ai":
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", message=".*pkg_resources.*")
                aiplatform.init(project=settings.gcp_project_id)
            from vertexai.generative_models import GenerativeModel
            self.model = GenerativeModel(self.llm_model)
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with prompt and return response."""
        try:
            if settings.llm_provider == "anthropic":
                message = self.client.messages.create(
                    model=self.llm_model,
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return message.content[0].text
            else:
                # Vertex AI
                response = self.model.generate_content(
                    f"{system_prompt}\n\n{prompt}"
                )
                return response.text
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            raise
    
    def get_schema_context(self) -> str:
        """Get schema information for LLM context."""
        schema_info = """
BigQuery Schema Context:

1. gmail_messages (partitioned by sent_at):
   - message_id, thread_id, mailbox_email, from_email
   - to_emails (ARRAY), cc_emails (ARRAY), subject, body_text, body_html
   - sent_at, labels (ARRAY), embedding, ingested_at

2. gmail_participants:
   - participant_id, message_id, email_address, role
   - sf_contact_id, sf_account_id, match_confidence

3. sf_accounts:
   - account_id, account_name, website, domain, industry
   - annual_revenue, owner_id, created_date, last_modified_date

4. sf_contacts:
   - contact_id, account_id, first_name, last_name, email, phone
   - mobile_phone, title, is_primary

5. sf_leads:
   - lead_id, first_name, last_name, email, company, phone
   - title, lead_source, status, owner_id, created_by_system

6. sf_opportunities:
   - opportunity_id, account_id, name, stage, amount, close_date
   - probability, owner_id, is_closed, is_won

7. sf_activities (partitioned by activity_date):
   - activity_id, activity_type, what_id, who_id, subject
   - description, activity_date, owner_id, matched_account_id

8. dialpad_calls (partitioned by call_time):
   - call_id, direction, from_number, to_number, duration_seconds
   - transcript_text, sentiment_score, call_time, user_id
   - matched_contact_id, matched_account_id, embedding

9. account_recommendations (partitioned by score_date):
   - recommendation_id, account_id, score_date, priority_score
   - budget_likelihood, engagement_score, reasoning
   - recommended_action, key_signals (ARRAY), last_interaction_date

10. v_unmatched_emails (view):
    - participant_id, email_address, message_id, subject
    - sent_at, mailbox_email, from_email
"""
        return schema_info
    
    def generate_sql(self, user_query: str) -> str:
        """Generate SQL query from natural language."""
        schema_context = self.get_schema_context()
        
        system_prompt = """You are a SQL query generator. Convert natural language questions to BigQuery SQL.
Rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use table names from the schema provided
3. Always use proper JOINs when combining data
4. Use LIMIT to restrict results (default 100)
5. Format dates properly (TIMESTAMP/DATE types)
6. Return only the SQL query, no explanation

Important:
- Use `{project_id}.{dataset_id}.table_name` format
- For partitioned tables, consider filtering by date
- Use ARRAY functions when working with array columns
- Always qualify column names to avoid ambiguity"""
        
        prompt = f"""Schema Context:
{schema_context}

User Question: {user_query}

Generate a BigQuery SQL query to answer this question. Return ONLY the SQL query, nothing else."""
        
        response = self._call_llm(prompt, system_prompt)
        
        # Extract SQL from response
        sql = self._extract_sql(response)
        
        return sql
    
    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from LLM response."""
        # Try to find SQL between code blocks
        sql_match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()
        
        sql_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        # Try to find SELECT statement
        select_match = re.search(r'(SELECT\s+.*?;?\s*$)', text, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        # Return as-is if no pattern matches
        return text.strip()
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL for safety.
        Returns (is_valid, error_message)
        """
        sql_upper = sql.upper().strip()
        
        # Check for forbidden keywords
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Forbidden keyword detected: {keyword}"
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"
        
        # Check table names (basic check)
        # This is a simplified check - in production, use a proper SQL parser
        for table in ALLOWED_TABLES:
            if table in sql:
                # Found at least one allowed table
                break
        else:
            # Check if it's using the full table reference format
            if f"{self.bq_client.project_id}.{self.bq_client.dataset_id}" not in sql:
                return False, "Query must reference tables from the allowed schema"
        
        return True, None
    
    def execute_query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute a natural language query.
        Returns query results and summary.
        """
        try:
            # Generate SQL
            sql = self.generate_sql(user_query)
            logger.info(f"Generated SQL: {sql[:200]}...")
            
            # Validate SQL
            is_valid, error = self.validate_sql(sql)
            if not is_valid:
                return {
                    "error": f"Query validation failed: {error}",
                    "sql": sql
                }
            
            # Replace placeholders in SQL
            sql = sql.replace("{project_id}", self.bq_client.project_id)
            sql = sql.replace("{dataset_id}", self.bq_client.dataset_id)
            
            # Execute query
            results = self.bq_client.query(sql, max_results=settings.max_query_results)
            
            # Generate summary
            summary = self._generate_summary(user_query, results, sql)
            
            return {
                "query": user_query,
                "sql": sql,
                "results": results[:settings.max_query_results],
                "row_count": len(results),
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return {
                "error": str(e),
                "query": user_query
            }
    
    def _generate_summary(self, query: str, results: list, sql: str) -> str:
        """Generate natural language summary of query results."""
        if not results:
            return "No results found for this query."
        
        system_prompt = """You are a data analyst. Summarize query results in natural language.
Be concise and highlight key insights."""
        
        prompt = f"""Original Question: {query}

Query returned {len(results)} rows. Here's a sample of the data:
{str(results[:5])}

Provide a brief summary (2-3 sentences) of the key findings."""
        
        try:
            summary = self._call_llm(prompt, system_prompt)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Query returned {len(results)} results."

