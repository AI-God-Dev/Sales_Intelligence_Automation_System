# Intelligence Layer - Phase 2

This directory contains all Phase 2 components: AI-powered intelligence and automation features.

## Structure

```
intelligence/
├── embeddings/          # Embedding generation for semantic search
├── scoring/            # Account scoring using LLM
├── nlp_query/          # Natural language to SQL queries
├── automation/         # Lead creation and HubSpot enrollment
└── email_replies/      # AI email reply generation
```

## Components

### 1. Embeddings Generation (`embeddings/`)

Generates vector embeddings for emails and call transcripts using OpenAI or Vertex AI.

**Key Features:**
- Batch processing for historical data
- Incremental updates for new content
- Supports OpenAI `text-embedding-3-small` and Vertex AI embeddings
- Cloud Function endpoint for scheduled runs

**Usage:**
```python
from intelligence.embeddings.generator import EmbeddingGenerator

generator = EmbeddingGenerator()
# Generate embeddings for emails without them
count = generator.update_email_embeddings(limit=1000)
```

**Cloud Function:** `POST /generate-embeddings`
```json
{
  "type": "both",  // "emails", "calls", or "both"
  "limit": 1000
}
```

### 2. Account Scoring (`scoring/`)

Daily AI-powered account scoring using LLM analysis.

**Key Features:**
- Aggregates last 5 emails, last 3 calls, open opportunities, recent activities
- Generates priority score, budget likelihood, engagement score
- LLM-powered reasoning and recommendations
- Stores results in `account_recommendations` table

**Usage:**
```python
from intelligence.scoring.account_scorer import AccountScorer

scorer = AccountScorer()
recommendation = scorer.score_account("account_123")
```

**Cloud Function:** `POST /account-scoring` (runs daily via Cloud Scheduler)

### 3. Natural Language Queries (`nlp_query/`)

Convert natural language questions to BigQuery SQL queries with safety validation.

**Key Features:**
- LLM-powered SQL generation
- Safety validation (SELECT only, table whitelist)
- Result summarization using LLM
- Supports all BigQuery tables and views

**Usage:**
```python
from intelligence.nlp_query.query_generator import NLPQueryGenerator

generator = NLPQueryGenerator()
result = generator.execute_query("Show me accounts with high engagement in the last week")
```

**Cloud Function:** `POST /nlp-query`
```json
{
  "query": "Show me accounts discussing budget in 2026"
}
```

### 4. Automation (`automation/`)

#### Lead Creation (`lead_creation.py`)

Creates Salesforce leads from unmatched emails.

**Key Features:**
- Extracts name and company from emails
- Creates leads with proper source tracking
- Records in BigQuery for monitoring

**Cloud Function:** `POST /create-leads`
```json
{
  "limit": 10,
  "owner_id": "salesforce_user_id"
}
```

#### HubSpot Enrollment (`hubspot_enrollment.py`)

Enrolls contacts in HubSpot sequences.

**Key Features:**
- Finds or creates contacts automatically
- Supports single and bulk enrollment
- Error handling and tracking

**Cloud Function:** `POST /enroll-hubspot`
```json
{
  "email": "contact@example.com",
  "sequence_id": "sequence_123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 5. AI Email Replies (`email_replies/`)

Generates contextual email replies using LLM with full conversation history.

**Key Features:**
- Retrieves full email thread context
- Includes account context from Salesforce
- Considers recent interactions
- Can send replies via Gmail API

**Usage:**
```python
from intelligence.email_replies.generator import EmailReplyGenerator

generator = EmailReplyGenerator()
result = generator.generate_reply(
    thread_id="thread_123",
    message_id="msg_456",
    reply_to_email="customer@example.com",
    account_id="account_789"
)
```

**Cloud Function:** `POST /generate-email-reply`
```json
{
  "thread_id": "thread_123",
  "message_id": "msg_456",
  "reply_to_email": "customer@example.com",
  "account_id": "account_789",
  "access_token": "gmail_oauth_token",
  "send": false
}
```

## Configuration

All components use the configuration from `config.config`:
- LLM provider (Anthropic Claude or Vertex AI)
- Embedding model
- BigQuery project and dataset
- API keys from Secret Manager

## Deployment

Each component can be deployed as a Cloud Function:

```bash
# Deploy embeddings generator
gcloud functions deploy generate-embeddings \
  --runtime python311 \
  --trigger http \
  --source intelligence/embeddings

# Deploy account scoring
gcloud functions deploy account-scoring \
  --runtime python311 \
  --trigger http \
  --source intelligence/scoring \
  --schedule "0 7 * * *"  # Daily at 7 AM

# Deploy NLP query
gcloud functions deploy nlp-query \
  --runtime python311 \
  --trigger http \
  --source intelligence/nlp_query

# Deploy automation
gcloud functions deploy create-leads \
  --runtime python311 \
  --trigger http \
  --source intelligence/automation

# Deploy email replies
gcloud functions deploy generate-email-reply \
  --runtime python311 \
  --trigger http \
  --source intelligence/email_replies
```

## Testing

Run unit tests:
```bash
pytest tests/test_intelligence.py
```

## Next Steps

1. **Vector Search**: Implement BigQuery Vector Search for semantic queries
2. **UI Integration**: Build web app interfaces for all features
3. **Performance Optimization**: Optimize LLM calls and caching
4. **Monitoring**: Add comprehensive metrics and alerting

