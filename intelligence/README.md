# Intelligence Module

AI-powered features for the Sales Intelligence Automation System.

## Components

### Account Scoring (`scoring/`)

Daily AI-generated account priority scores using Vertex AI (Gemini).

**Metrics:**
- Priority Score (0-100)
- Budget Likelihood (0-100)
- Engagement Score (0-100)

**Cloud Function:** `account-scoring`

```bash
gcloud functions call account-scoring --gen2 --region=us-central1
```

### Natural Language Query (`nlp_query/`)

Converts natural language questions to BigQuery SQL.

**Features:**
- Automatic SQL generation
- Safety validation (SELECT only)
- Result summarization

**Cloud Function:** `nlp-query`

```bash
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me top 10 accounts"}'
```

### Semantic Search (`vector_search/`)

Intent-based search using vector embeddings.

**Features:**
- Search emails, calls, accounts
- Cosine similarity ranking
- Configurable thresholds

**Cloud Function:** `semantic-search`

### Embeddings Generation (`embeddings/`)

Generates vector embeddings for semantic search.

**Model:** `textembedding-gecko@001` (768 dimensions)

**Cloud Function:** `generate-embeddings`

### Automation (`automation/`)

Automated workflows:
- Lead creation from unmatched emails
- HubSpot sequence enrollment

**Cloud Functions:** `create-leads`, `enroll-hubspot`

### Email Replies (`email_replies/`)

AI-generated email reply suggestions.

**Cloud Function:** `generate-email-reply`

## Architecture

```
intelligence/
├── scoring/           # Account scoring
├── nlp_query/         # NL to SQL
├── vector_search/     # Semantic search
├── embeddings/        # Vector generation
├── automation/        # Workflows
└── email_replies/     # AI replies
```

Each module contains:
- `main.py` - Cloud Function entry point
- `*.py` - Business logic
- `requirements.txt` - Dependencies

## Configuration

Set in environment variables:
- `LLM_MODEL` - Gemini model (default: `gemini-2.5-pro`)
- `EMBEDDING_MODEL` - Embedding model
- `MOCK_MODE` - Enable mock responses

## Deployment

```bash
# Deploy all intelligence functions
./scripts/deploy/deploy_phase2_functions.ps1
```

## Testing

```bash
# Run unit tests
pytest tests/test_ai_*.py

# Test functions locally
functions-framework --target=account_scoring_job
```
