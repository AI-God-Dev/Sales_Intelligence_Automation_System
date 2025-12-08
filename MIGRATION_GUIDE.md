# Migration Guide - Unified AI Abstraction Layer

## Overview

This guide explains how to migrate from direct AI provider calls to the new unified abstraction layer in the `ai/` directory.

---

## Why Migrate?

The unified abstraction layer provides:
- **Provider Switching**: Easy switching between Vertex AI, OpenAI, Anthropic
- **MOCK_MODE Support**: Test without API calls
- **LOCAL_MODE Support**: Offline development
- **Consistent Interface**: Same API across all providers
- **Better Error Handling**: Unified error handling and retry logic

---

## Migration Status

### ✅ Already Migrated
- `intelligence/embeddings/generator.py` - Uses `ai.embeddings`
- `intelligence/scoring/account_scorer.py` - Uses `ai.models` and `ai.scoring`
- `intelligence/vector_search/semantic_search.py` - Uses `ai.semantic_search`
- `intelligence/nlp_query/query_generator.py` - Uses `ai.models`
- `intelligence/email_replies/generator.py` - Uses `ai.models`

### ⚠️ Legacy Code (Still Works)
Old direct calls still work but are deprecated:
```python
# Old way (still works, but deprecated)
from vertexai.generative_models import GenerativeModel
model = GenerativeModel("gemini-pro")
response = model.generate_content(prompt)
```

---

## Migration Steps

### Step 1: Replace Direct LLM Calls

**Before:**
```python
from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform

aiplatform.init(project=project_id, location=region)
model = GenerativeModel("gemini-pro")
response = model.generate_content(prompt)
```

**After:**
```python
from ai.models import get_model_provider

# Automatically respects MOCK_MODE, LOCAL_MODE, and provider settings
provider = get_model_provider()
response = provider.generate(prompt, system_prompt="...", max_tokens=2000)
```

### Step 2: Replace Direct Embedding Calls

**Before:**
```python
from vertexai.language_models import TextEmbeddingModel

model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
embeddings = model.get_embeddings([text])
```

**After:**
```python
from ai.embeddings import get_embedding_provider

# Automatically respects MOCK_MODE, LOCAL_MODE, and provider settings
provider = get_embedding_provider()
embedding = provider.generate_embedding(text)
```

### Step 3: Use Scoring Provider

**Before:**
```python
# Manual LLM call with prompt building
response = model.generate_content(scoring_prompt)
# Manual JSON parsing
scores = json.loads(response)
```

**After:**
```python
from ai.scoring import get_scoring_provider

scoring_provider = get_scoring_provider()
scores = scoring_provider.score_account(account_id, account_data)
# Returns validated dict with all scores
```

### Step 4: Use Semantic Search Provider

**Before:**
```python
# Manual embedding generation and BigQuery query
embedding = generate_embedding(query)
# Manual BigQuery vector search
results = bq_client.query(vector_search_query)
```

**After:**
```python
from ai.semantic_search import get_semantic_search_provider

search = get_semantic_search_provider(bq_client=bq_client)
results = search.search_emails_by_intent("budget discussions", limit=50)
```

---

## Backward Compatibility

### Old Code Still Works

The old direct calls still work. Migration is optional but recommended.

### Gradual Migration

You can migrate one component at a time:
1. Update one file
2. Test with MOCK_MODE
3. Verify with real provider
4. Move to next component

---

## Testing with MOCK_MODE

### Enable MOCK_MODE

```bash
export MOCK_MODE=1
```

### Test Your Code

```python
# Your code automatically uses mock providers
from ai.models import get_model_provider

provider = get_model_provider()  # Returns MockModelProvider if MOCK_MODE=1
response = provider.generate("test")
# Returns mock response, no API calls
```

---

## Environment Variables

### Provider Selection

```bash
# LLM Provider (Vertex-only; mock allowed for testing)
LLM_PROVIDER=vertex_ai  # or mock

# Embedding Provider (Vertex-only; local/mock for testing)
EMBEDDING_PROVIDER=vertex_ai  # or local, mock

# Testing Modes
MOCK_MODE=1  # Use fake responses
LOCAL_MODE=1  # Use local implementations
```

---

## Common Patterns

### Pattern 1: Conditional Provider

```python
from ai.models import get_model_provider

# Automatically uses MOCK_MODE if set
provider = get_model_provider()
response = provider.generate(prompt)
```

### Pattern 2: Explicit Provider

```python
from ai.models import get_model_provider

# Explicitly specify provider
provider = get_model_provider(
    provider="vertex_ai",
    project_id="my-project",
    region="us-central1",
    model_name="gemini-pro"
)
```

### Pattern 3: Dependency Injection

```python
from ai.models import get_model_provider

# Create provider once, inject into components
model_provider = get_model_provider()
scorer = AccountScorer(model_provider=model_provider)
```

---

## Benefits After Migration

1. **Testing**: Use MOCK_MODE for fast unit tests
2. **Development**: Use LOCAL_MODE for offline work
3. **Flexibility**: Switch providers via environment variables
4. **Consistency**: Same interface across all AI operations
5. **Error Handling**: Unified error handling and retry logic

---

## Troubleshooting

### Issue: Import Error

**Error**: `ModuleNotFoundError: No module named 'ai'`

**Solution**: Ensure you're running from project root, or add project root to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: MOCK_MODE Not Working

**Error**: Still making API calls when MOCK_MODE=1

**Solution**: 
1. Verify environment variable: `echo $MOCK_MODE`
2. Restart Python process
3. Check code uses `get_model_provider()` not direct instantiation

### Issue: Provider Not Found

**Error**: `Unsupported provider: xyz`

**Solution**: Check environment variable spelling and supported providers:
- LLM: `vertex_ai`, `mock` (Vertex-only in production)
- Embeddings: `vertex_ai`, `local`, `mock` (Vertex-only in production)

---

## Examples

### Example 1: Embedding Generation

```python
# Old way
from vertexai.language_models import TextEmbeddingModel
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
embedding = model.get_embeddings([text])[0].values

# New way
from ai.embeddings import get_embedding_provider
provider = get_embedding_provider()
embedding = provider.generate_embedding(text)
```

### Example 2: LLM Generation

```python
# Old way
from vertexai.generative_models import GenerativeModel
model = GenerativeModel("gemini-pro")
response = model.generate_content(prompt).text

# New way
from ai.models import get_model_provider
provider = get_model_provider()
response = provider.generate(prompt, system_prompt="...")
```

### Example 3: Account Scoring

```python
# Old way
# Manual prompt building, LLM call, JSON parsing

# New way
from ai.scoring import get_scoring_provider
scoring_provider = get_scoring_provider()
scores = scoring_provider.score_account(account_id, account_data)
```

---

## Next Steps

1. Review your code for direct AI provider calls
2. Replace with unified abstraction layer
3. Test with MOCK_MODE
4. Verify with real providers
5. Update documentation

---

## Support

- See **[AI_SYSTEM_GUIDE.md](AI_SYSTEM_GUIDE.md)** for detailed usage
- See **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** for testing
- See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common issues
