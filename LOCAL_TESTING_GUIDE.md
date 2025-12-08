# Local Testing Guide - Sales Intelligence Automation System

## Overview

This guide provides comprehensive instructions for running and testing the Sales Intelligence Automation System locally. The system supports **LOCAL_MODE** and **MOCK_MODE** for full offline development and testing capabilities.

---

## Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Google Cloud SDK** (optional, for BigQuery access)
   ```bash
   gcloud --version
   ```

3. **Git**
   ```bash
   git --version
   ```

### Required Python Packages

Install all dependencies:
```bash
pip install -r requirements.txt
pip install -r web_app/requirements.txt
```

Key packages:
- `functions-framework`: For running Cloud Functions locally
- `streamlit`: For web application
- `google-cloud-bigquery`: For BigQuery access (optional in LOCAL_MODE)
- `numpy`: For local embeddings

---

## Local Testing Modes

### 1. MOCK_MODE

**Purpose**: Test without API calls, using fake AI responses

**Enable**:
```bash
export MOCK_MODE=1
```

**Behavior**:
- Fake LLM responses
- Deterministic mock embeddings
- No external API calls
- Fast execution

**Use Cases**:
- Unit testing
- Integration testing
- CI/CD pipelines
- Development without API costs

### 2. LOCAL_MODE

**Purpose**: Full local development with local implementations

**Enable**:
```bash
export LOCAL_MODE=1
```

**Behavior**:
- Local embeddings using numpy
- SQLite database (optional)
- No external API calls
- No GCP dependencies

**Use Cases**:
- Offline development
- Testing without GCP access
- Local debugging

### 3. Hybrid Mode

**Purpose**: Use real BigQuery with mock AI

**Enable**:
```bash
export MOCK_MODE=1
# Don't set LOCAL_MODE (uses real BigQuery)
```

**Behavior**:
- Real BigQuery queries
- Mock AI responses
- Best of both worlds

---

## Setting Up Local Environment

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd SALES
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r web_app/requirements.txt
```

### Step 4: Set Environment Variables

**For MOCK_MODE**:
```bash
# Windows PowerShell
$env:MOCK_MODE = "1"
$env:GCP_PROJECT_ID = "your-project-id"  # Optional if using LOCAL_MODE
$env:GCP_REGION = "us-central1"

# Linux/Mac
export MOCK_MODE=1
export GCP_PROJECT_ID="your-project-id"  # Optional if using LOCAL_MODE
export GCP_REGION="us-central1"
```

**For LOCAL_MODE**:
```bash
# Windows PowerShell
$env:LOCAL_MODE = "1"
$env:GCP_PROJECT_ID = "your-project-id"  # Still needed for some operations
$env:GCP_REGION = "us-central1"

# Linux/Mac
export LOCAL_MODE=1
export GCP_PROJECT_ID="your-project-id"  # Still needed for some operations
export GCP_REGION="us-central1"
```

### Step 5: Authenticate with GCP (Optional)

If using real BigQuery:
```bash
gcloud auth application-default login
```

---

## Running Cloud Functions Locally

### Using Functions Framework

The `functions-framework` package allows running Cloud Functions locally.

### 1. Gmail Sync Function

```bash
functions-framework \
  --target=gmail_sync \
  --source=cloud_functions/gmail_sync \
  --port=8080
```

**Test**:
```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"mailbox": "test@example.com"}'
```

### 2. Salesforce Sync Function

```bash
functions-framework \
  --target=salesforce_sync \
  --source=cloud_functions/salesforce_sync \
  --port=8081
```

### 3. Embeddings Generation Function

```bash
functions-framework \
  --target=generate_embeddings \
  --source=intelligence/embeddings \
  --port=8082
```

**Test**:
```bash
curl -X POST http://localhost:8082 \
  -H "Content-Type: application/json" \
  -d '{"type": "emails", "limit": 10}'
```

### 4. Account Scoring Function

```bash
functions-framework \
  --target=account_scoring_job \
  --source=intelligence/scoring \
  --port=8083
```

### 5. NLP Query Function

```bash
functions-framework \
  --target=nlp_query \
  --source=intelligence/nlp_query \
  --port=8084
```

**Test**:
```bash
curl -X POST http://localhost:8084 \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me high priority accounts"}'
```

---

## Running Web Application Locally

### Method 1: Direct Streamlit

```bash
cd web_app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Method 2: Using Script

**Windows**:
```powershell
.\run_local.ps1
```

**Linux/Mac**:
```bash
./run_local.sh
```

### Testing Web App in MOCK_MODE

1. Set environment variable:
   ```bash
   export MOCK_MODE=1
   ```

2. Run app:
   ```bash
   cd web_app
   streamlit run app.py
   ```

3. Test features:
   - Account scoring (will use mock scores)
   - Semantic search (will use mock embeddings)
   - NLP queries (will use mock responses)

---

## Testing AI Components

### 1. Testing Model Provider

```python
import os
os.environ["MOCK_MODE"] = "1"

from ai.models import get_model_provider

provider = get_model_provider()
response = provider.generate("Test prompt")
print(response)  # Mock response
```

### 2. Testing Embedding Provider

```python
import os
os.environ["MOCK_MODE"] = "1"

from ai.embeddings import get_embedding_provider

provider = get_embedding_provider()
embedding = provider.generate_embedding("Test text")
print(f"Embedding dimensions: {len(embedding)}")
```

### 3. Testing Semantic Search

```python
import os
os.environ["MOCK_MODE"] = "1"

from ai.semantic_search import get_semantic_search_provider
from utils.bigquery_client import BigQueryClient

bq_client = BigQueryClient()
search = get_semantic_search_provider(bq_client=bq_client)

results = search.search_emails_by_intent("budget discussions")
print(f"Found {len(results)} results")
```

### 4. Testing Account Scoring

```python
import os
os.environ["MOCK_MODE"] = "1"

from ai.scoring import get_scoring_provider

scorer = get_scoring_provider()
account_data = {
    "account_name": "Test Account",
    "emails": [],
    "calls": [],
    "opportunities": [],
    "activities": []
}

scores = scorer.score_account("test_account_123", account_data)
print(scores)  # Mock scores
```

---

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_email_normalizer.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Integration Tests

```bash
# Set MOCK_MODE for integration tests
export MOCK_MODE=1
pytest tests/test_integration.py
```

### Test Coverage

```bash
pytest --cov=. --cov-report=term-missing
```

---

## Local Database (Optional)

### SQLite Setup

For full LOCAL_MODE, you can use SQLite instead of BigQuery:

```python
import sqlite3

# Create local database
conn = sqlite3.connect('local_sales_intelligence.db')

# Create tables (simplified schema)
conn.execute('''
CREATE TABLE IF NOT EXISTS gmail_messages (
    message_id TEXT PRIMARY KEY,
    subject TEXT,
    body_text TEXT,
    sent_at TIMESTAMP
)
''')

conn.commit()
conn.close()
```

**Note**: This is optional. The system primarily uses BigQuery, but SQLite can be used for local testing.

---

## Testing Ingestion Pipelines

### 1. Gmail Sync (Mock)

```python
import os
os.environ["MOCK_MODE"] = "1"

from cloud_functions.gmail_sync.main import gmail_sync

# Mock request
request = {
    "mailbox": "test@example.com",
    "sync_type": "incremental"
}

result = gmail_sync(request)
print(result)
```

### 2. Salesforce Sync (Mock)

```python
import os
os.environ["MOCK_MODE"] = "1"

from cloud_functions.salesforce_sync.main import salesforce_sync

request = {
    "object_type": "Account",
    "sync_type": "incremental"
}

result = salesforce_sync(request)
print(result)
```

---

## Debugging

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check Environment Variables

```python
import os
print(f"MOCK_MODE: {os.getenv('MOCK_MODE')}")
print(f"LOCAL_MODE: {os.getenv('LOCAL_MODE')}")
print(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID')}")
```

### 3. Test AI Providers

```python
# Test each provider
from ai.models import get_model_provider

# Mock
os.environ["MOCK_MODE"] = "1"
provider = get_model_provider()
print(provider.generate("test"))

# Vertex AI (requires GCP auth)
os.environ.pop("MOCK_MODE", None)
os.environ["LLM_PROVIDER"] = "vertex_ai"
provider = get_model_provider()
print(provider.generate("test"))
```

---

## Common Issues

### 1. MOCK_MODE Not Working

**Solution**:
- Verify environment variable is set: `echo $MOCK_MODE`
- Restart Python process
- Check code is using `get_model_provider()` not direct instantiation

### 2. Functions Framework Not Found

**Solution**:
```bash
pip install functions-framework
```

### 3. BigQuery Access Denied

**Solution**:
- Use MOCK_MODE or LOCAL_MODE
- Or authenticate: `gcloud auth application-default login`
- Or use service account key file

### 4. Import Errors

**Solution**:
- Ensure you're in the project root
- Add project root to PYTHONPATH:
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)"
  ```

---

## Best Practices

### 1. Use MOCK_MODE for Unit Tests

```python
import os
import pytest

@pytest.fixture(autouse=True)
def mock_mode():
    os.environ["MOCK_MODE"] = "1"
    yield
    os.environ.pop("MOCK_MODE", None)
```

### 2. Use LOCAL_MODE for Integration Tests

```python
import os
import pytest

@pytest.fixture(autouse=True)
def local_mode():
    os.environ["LOCAL_MODE"] = "1"
    yield
    os.environ.pop("LOCAL_MODE", None)
```

### 3. Test Both Modes

Always test with both MOCK_MODE and real providers:
```bash
# Test with mock
MOCK_MODE=1 pytest

# Test with real (if available)
pytest
```

### 4. Isolate Tests

Each test should be independent:
- Use fixtures for setup/teardown
- Don't rely on external state
- Clean up after tests

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install -r web_app/requirements.txt
      - run: pip install pytest pytest-cov
      - env:
          MOCK_MODE: 1
        run: pytest --cov=. --cov-report=xml
```

---

## Conclusion

The local testing system provides comprehensive capabilities for developing and testing the Sales Intelligence Automation System without external dependencies. Use MOCK_MODE for fast unit testing, LOCAL_MODE for offline development, and real providers for integration testing. Follow best practices for isolation, coverage, and CI/CD integration.
