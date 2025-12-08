# AI System Guide - Sales Intelligence Automation System

## Overview

The AI Intelligence Layer provides semantic search, account scoring, natural language queries, summarization, and insights generation using Large Language Models (LLMs) and vector embeddings. The system uses a **unified abstraction layer** that supports multiple providers and local/mock modes for testing.

---

## Architecture

### Unified Model Abstraction Layer

All AI operations go through a unified interface located in the `ai/` directory:

```
ai/
├── __init__.py           # Package exports
├── models.py             # LLM provider abstraction
├── embeddings.py         # Embedding provider abstraction
├── semantic_search.py    # Semantic search provider
├── scoring.py            # Account scoring provider
├── summarization.py      # Text summarization provider
└── insights.py           # Insights generation provider
```

### Provider Support

The system supports multiple AI providers:

1. **Vertex AI** (Recommended - Default)
   - Models: `gemini-pro`, `text-bison@001`
   - Embeddings: `textembedding-gecko@001`
   - No API keys needed (uses GCP service account)

2. **OpenAI**
   - Models: `gpt-4`, `gpt-3.5-turbo`
   - Embeddings: `text-embedding-3-small`, `text-embedding-3-large`
   - Requires API key in Secret Manager

3. **Anthropic**
   - Models: `claude-3-5-sonnet-20241022`
   - Requires API key in Secret Manager

4. **Mock Mode** (Testing)
   - Fake responses for testing without API calls
   - Deterministic outputs

5. **Local Mode** (Development)
   - Local embeddings using numpy
   - SQLite database support
   - No external API calls

---

## Configuration

### Environment Variables

```bash
# LLM Provider (vertex_ai, openai, anthropic, mock)
LLM_PROVIDER=vertex_ai

# LLM Model
LLM_MODEL=gemini-pro

# Embedding Provider (vertex_ai, openai, local, mock)
EMBEDDING_PROVIDER=vertex_ai

# Embedding Model
EMBEDDING_MODEL=textembedding-gecko@001

# Mock Mode (1 = enabled, 0 = disabled)
MOCK_MODE=0

# Local Mode (1 = enabled, 0 = disabled)
LOCAL_MODE=0
```

### Secret Manager

For OpenAI and Anthropic, store API keys in Secret Manager:
- `openai-api-key`: OpenAI API key
- `anthropic-api-key`: Anthropic API key

---

## Components

### 1. Model Provider (`ai/models.py`)

**Purpose**: Abstract LLM calls across different providers

**Usage**:
```python
from ai.models import get_model_provider

# Get provider (automatically uses MOCK_MODE if set)
provider = get_model_provider()

# Generate text
response = provider.generate(
    prompt="Analyze this account data...",
    system_prompt="You are an expert sales analyst.",
    max_tokens=2000,
    temperature=0.7
)

# Streaming
for chunk in provider.generate_stream(prompt="..."):
    print(chunk, end="")
```

**Supported Providers**:
- `VertexAIModelProvider`: Vertex AI (Gemini)
- `OpenAIModelProvider`: OpenAI (GPT-4, GPT-3.5)
- `AnthropicModelProvider`: Anthropic (Claude)
- `MockModelProvider`: Mock responses for testing

### 2. Embedding Provider (`ai/embeddings.py`)

**Purpose**: Generate vector embeddings for semantic search

**Usage**:
```python
from ai.embeddings import get_embedding_provider

# Get provider (automatically uses MOCK_MODE/LOCAL_MODE if set)
provider = get_embedding_provider()

# Generate single embedding
embedding = provider.generate_embedding("This is the text to embed")

# Generate batch embeddings
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = provider.generate_embeddings_batch(texts, batch_size=100)

# Get embedding dimensions
dimensions = provider.dimensions  # e.g., 768 for Vertex AI
```

**Supported Providers**:
- `VertexAIEmbeddingProvider`: Vertex AI embeddings
- `OpenAIEmbeddingProvider`: OpenAI embeddings
- `LocalEmbeddingProvider`: Local numpy-based embeddings
- `MockEmbeddingProvider`: Mock embeddings for testing

### 3. Semantic Search Provider (`ai/semantic_search.py`)

**Purpose**: Search emails and calls by semantic intent

**Usage**:
```python
from ai.semantic_search import get_semantic_search_provider
from utils.bigquery_client import BigQueryClient

bq_client = BigQueryClient()
search = get_semantic_search_provider(bq_client=bq_client)

# Search emails
results = search.search_emails_by_intent(
    query_text="budget discussions for 2026",
    limit=50,
    days_back=60,
    min_similarity=0.7
)

# Search calls
results = search.search_calls_by_intent(
    query_text="renewal concerns",
    limit=50,
    days_back=60,
    min_similarity=0.7
)
```

**How It Works**:
1. Generates embedding for query text
2. Uses BigQuery vector search with cosine similarity
3. Returns results ranked by similarity score

### 4. Scoring Provider (`ai/scoring.py`)

**Purpose**: Generate AI-powered account scores

**Usage**:
```python
from ai.scoring import get_scoring_provider

scorer = get_scoring_provider()

# Score account
account_data = {
    "account_name": "Acme Corp",
    "emails": [...],
    "calls": [...],
    "opportunities": [...],
    "activities": [...]
}

scores = scorer.score_account("account_123", account_data)
# Returns:
# {
#   "priority_score": 75,
#   "budget_likelihood": 60,
#   "engagement_score": 80,
#   "reasoning": "...",
#   "recommended_action": "...",
#   "key_signals": [...]
# }
```

**Scoring Process**:
1. Aggregates account data (emails, calls, opportunities, activities)
2. Builds prompt with account context
3. LLM analyzes and generates scores
4. Returns structured JSON with scores and recommendations

### 5. Summarization Provider (`ai/summarization.py`)

**Purpose**: Generate text summaries

**Usage**:
```python
from ai.summarization import get_summarization_provider

summarizer = get_summarization_provider()

# Summarize emails
emails = [
    {"subject": "...", "body_text": "...", "from_email": "...", "sent_at": "..."},
    ...
]
summary = summarizer.summarize_emails(emails, timeframe="daily")

# Summarize account activity
account_data = {...}
summary = summarizer.summarize_account_activity(account_data, days=7)
```

### 6. Insights Provider (`ai/insights.py`)

**Purpose**: Generate AI-powered insights for accounts

**Usage**:
```python
from ai.insights import get_insights_provider

insights_provider = get_insights_provider()

# Generate comprehensive insights
account_data = {...}
insights = insights_provider.generate_account_insights(account_data)
# Returns:
# {
#   "strengths": [...],
#   "risks": [...],
#   "opportunities": [...],
#   "recommendations": [...],
#   "key_metrics": {...}
# }

# Detect risks
risks = insights_provider.detect_risks(account_data)

# Detect opportunities
opportunities = insights_provider.detect_opportunities(account_data)
```

---

## Mock Mode

### Purpose

Mock mode provides fake AI responses for testing without making API calls. This is useful for:
- Unit testing
- Integration testing
- Development without API costs
- CI/CD pipelines

### Enabling Mock Mode

```bash
export MOCK_MODE=1
```

Or in code:
```python
import os
os.environ["MOCK_MODE"] = "1"
```

### Behavior

When `MOCK_MODE=1`:
- **Model Provider**: Returns deterministic mock responses
- **Embedding Provider**: Returns deterministic mock embeddings based on text hash
- **All AI operations**: Use mock implementations

### Mock Responses

- **Scoring**: Returns sample scores (priority_score: 75, etc.)
- **Summarization**: Returns "Mock summary: ..."
- **Insights**: Returns sample insights
- **Embeddings**: Deterministic embeddings based on text content

---

## Local Mode

### Purpose

Local mode provides local implementations for development without external dependencies:
- Local embeddings using numpy
- SQLite database (optional)
- No API calls

### Enabling Local Mode

```bash
export LOCAL_MODE=1
```

### Behavior

When `LOCAL_MODE=1`:
- **Embedding Provider**: Uses `LocalEmbeddingProvider` (numpy-based)
- **Database**: Can use SQLite instead of BigQuery (if implemented)
- **No API calls**: All operations are local

---

## Embeddings Generation

### Sources

Embeddings are generated for:
1. **Gmail emails**: Subject + body text
2. **Dialpad calls**: Transcript text
3. **Salesforce activities**: Notes and descriptions
4. **Salesforce opportunities**: Descriptions

### Storage

Embeddings are stored in:
- `gmail_messages.embedding` (ARRAY<FLOAT64>)
- `dialpad_calls.embedding` (ARRAY<FLOAT64>)
- `semantic_embeddings` table (optional centralized storage)

### Generation Process

1. **Batch Processing**: Processes in batches of 100 (configurable)
2. **Rate Limiting**: Respects API rate limits
3. **Error Handling**: Continues on individual failures
4. **Idempotency**: Safe to re-run (only processes missing embeddings)

### Cloud Function

**Function**: `generate-embeddings`
- Entry Point: `intelligence.embeddings.main.generate_embeddings`
- Trigger: Cloud Scheduler (daily) or HTTP POST
- Memory: 1024MB
- Timeout: 540 seconds

**Request Body**:
```json
{
  "type": "both",  // "emails", "calls", or "both"
  "limit": 1000
}
```

---

## Account Scoring

### Process

1. **Data Aggregation**:
   - Last 5 emails
   - Last 3 calls
   - Open opportunities
   - Recent activities

2. **LLM Analysis**:
   - Analyzes aggregated data
   - Generates priority score (0-100)
   - Generates budget likelihood (0-100)
   - Generates engagement score (0-100)
   - Provides reasoning and recommendations

3. **Storage**: Results stored in `account_recommendations` table

### Cloud Function

**Function**: `account-scoring`
- Entry Point: `intelligence.scoring.main.account_scoring_job`
- Trigger: Cloud Scheduler (daily at 7 AM)
- Memory: 1024MB
- Timeout: 540 seconds

### Scoring Criteria

- **Priority Score**: Overall account priority based on engagement, opportunities, and signals
- **Budget Likelihood**: Likelihood account is discussing 2026 budget
- **Engagement Score**: Recent engagement level (emails, calls, activities)

---

## Natural Language Queries

### Process

1. User submits natural language question
2. LLM converts to BigQuery SQL
3. Safety validation (SELECT only, no DROP/DELETE/UPDATE)
4. Query executed against BigQuery
5. Results summarized by LLM in natural language

### Cloud Function

**Function**: `nlp-query`
- Entry Point: `intelligence.nlp_query.main.nlp_query`
- Trigger: HTTP POST (called from web app)
- Memory: 512MB
- Timeout: 60 seconds

### Example Queries

- "Show me accounts with high engagement in the last week"
- "Which accounts are discussing budget for 2026?"
- "What are the top opportunities by amount?"

---

## Best Practices

### 1. Error Handling

Always wrap AI calls in try-except blocks:
```python
try:
    response = provider.generate(prompt)
except Exception as e:
    logger.error(f"AI call failed: {e}")
    # Fallback logic
```

### 2. Rate Limiting

Respect API rate limits:
- Batch operations when possible
- Use exponential backoff for retries
- Monitor API usage

### 3. Cost Management

- Use Vertex AI (no API costs, uses GCP service account)
- Enable MOCK_MODE for testing
- Cache embeddings when possible
- Batch embedding generation

### 4. Testing

- Use MOCK_MODE for unit tests
- Use LOCAL_MODE for integration tests
- Test with real providers in staging environment

### 5. Monitoring

- Log all AI calls
- Track API usage and costs
- Monitor response times
- Alert on high error rates

---

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Check Secret Manager for API keys
   - Verify service account has Secret Manager access

2. **Vertex AI Initialization Failed**
   - Ensure Vertex AI API is enabled
   - Verify service account has AI Platform User role

3. **Embedding Generation Fails**
   - Check text length (max 8000 characters)
   - Verify embedding model is correct
   - Check API rate limits

4. **Mock Mode Not Working**
   - Verify `MOCK_MODE=1` is set
   - Check environment variable is loaded
   - Restart application if needed

---

## Performance Optimization

### 1. Batch Processing

Always batch embedding generation:
```python
embeddings = provider.generate_embeddings_batch(texts, batch_size=100)
```

### 2. Caching

Cache embeddings when possible:
- Store in BigQuery
- Use `semantic_embeddings` table for centralized storage

### 3. Parallel Processing

For large batches, process in parallel:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_batch, batch) for batch in batches]
```

---

## Conclusion

The AI System provides powerful intelligence capabilities through a unified, provider-agnostic interface. The system supports multiple providers, local/mock modes for testing, and comprehensive error handling. Follow best practices for error handling, rate limiting, and cost management to ensure reliable and efficient operation.
