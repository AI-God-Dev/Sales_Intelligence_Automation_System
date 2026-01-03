# Configuration Guide

Complete configuration reference for the Sales Intelligence Automation System.

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | `my-project-123` |
| `GCP_REGION` | GCP region | `us-central1` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATASET_ID` | BigQuery dataset name | `sales_intelligence` |
| `BQ_DATASET_NAME` | Alternative dataset name | `sales_intelligence` |
| `LLM_PROVIDER` | AI provider | `vertex_ai` |
| `LLM_MODEL` | Gemini model name | `gemini-2.5-pro` |
| `EMBEDDING_MODEL` | Embedding model | `textembedding-gecko@001` |
| `MOCK_MODE` | Use mock AI responses | `0` |
| `LOCAL_MODE` | Use local implementations | `0` |
| `SALESFORCE_DOMAIN` | Salesforce domain | `login` (or `test` for sandbox) |

### Example `.env` File

```bash
# Required
GCP_PROJECT_ID=my-project-123
GCP_REGION=us-central1

# Optional
DATASET_ID=sales_intelligence
LLM_PROVIDER=vertex_ai
LLM_MODEL=gemini-2.5-pro
SALESFORCE_DOMAIN=login
```

---

## Secret Manager Secrets

All sensitive credentials must be stored in Google Secret Manager.

### Required Secrets

| Secret Name | Description | Format |
|------------|-------------|--------|
| `salesforce-client-id` | Salesforce OAuth Client ID | String |
| `salesforce-client-secret` | Salesforce OAuth Client Secret | String |
| `dialpad-api-key` | Dialpad API Key | String |
| `hubspot-api-key` | HubSpot Private App Token | `pat-na1-xxx...` |

### Optional Secrets

| Secret Name | Description | When Required |
|------------|-------------|---------------|
| `salesforce-username` | Salesforce username | Legacy auth |
| `salesforce-password` | Salesforce password | Legacy auth |
| `salesforce-security-token` | Salesforce security token | Legacy auth |
| `salesforce-refresh-token` | OAuth refresh token | Refresh flow |
| `salesforce-instance-url` | Salesforce instance URL | Custom domain |

### Creating Secrets

```bash
# Create secret
gcloud secrets create salesforce-client-id

# Add value
echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding salesforce-client-id \
  --member="serviceAccount:sales-intelligence-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Salesforce Configuration

### OAuth Setup (Recommended)

1. **Create Connected App** in Salesforce Setup
   - OAuth Settings > Enable OAuth
   - Callback URL: `https://login.salesforce.com/services/oauth2/callback`
   - Scopes: `api`, `refresh_token`, `offline_access`

2. **Store Credentials**
   ```bash
   echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=-
   echo -n "YOUR_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=-
   ```

### Domain Configuration

| Environment | Domain Value |
|------------|--------------|
| Production | `login` |
| Sandbox | `test` |

```bash
export SALESFORCE_DOMAIN=login  # or "test" for sandbox
```

See [SALESFORCE_OAUTH_SETUP.md](SALESFORCE_OAUTH_SETUP.md) for detailed setup.

---

## Gmail Configuration

Gmail integration requires Domain-Wide Delegation for service account access.

### Setup Steps

1. **Enable Domain-Wide Delegation**
   - GCP Console > IAM > Service Accounts
   - Select service account > Enable Domain-Wide Delegation
   - Note the Client ID

2. **Configure Google Workspace Admin**
   - Admin Console > Security > API Controls > Domain-wide Delegation
   - Add new client with service account Client ID
   - Scopes: `https://www.googleapis.com/auth/gmail.readonly`

3. **Configure Mailboxes**
   
   Edit `config/config.py`:
   ```python
   gmail_mailboxes: list[str] = [
       "sales1@yourdomain.com",
       "sales2@yourdomain.com",
   ]
   ```

See [GMAIL_DWD_SETUP.md](GMAIL_DWD_SETUP.md) for detailed setup.

---

## HubSpot Configuration

### Private App Setup

1. **Create Private App** in HubSpot
   - Settings > Integrations > Private Apps
   - Create app with required scopes (see [HUBSPOT_SCOPES.md](HUBSPOT_SCOPES.md))

2. **Store Token**
   ```bash
   echo -n "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" | \
     gcloud secrets versions add hubspot-api-key --data-file=-
   ```

See [HUBSPOT_SETUP.md](HUBSPOT_SETUP.md) for detailed setup.

---

## Dialpad Configuration

### API Key Setup

1. **Get API Key** from Dialpad Admin Console
2. **Store Key**
   ```bash
   echo -n "YOUR_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=-
   ```

---

## Vertex AI Configuration

Vertex AI uses Application Default Credentials (ADC) - no API keys required.

### Required IAM Roles

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

### Model Configuration

| Variable | Description | Options |
|----------|-------------|---------|
| `LLM_MODEL` | Text generation model | `gemini-2.5-pro`, `gemini-1.5-flash` |
| `EMBEDDING_MODEL` | Embedding model | `textembedding-gecko@001` |

---

## BigQuery Configuration

### Dataset Settings

| Setting | Value |
|---------|-------|
| Dataset ID | `sales_intelligence` |
| Location | `us-central1` |
| Tables | 16 core tables |

### Table Schema

See `bigquery/schemas/create_tables.sql` for complete schema definitions.

---

## Cloud Scheduler Jobs

| Job Name | Schedule | Function |
|----------|----------|----------|
| `gmail-sync-hourly` | `0 * * * *` | `gmail-sync` |
| `salesforce-sync-daily` | `0 2 * * *` | `salesforce-sync` |
| `dialpad-sync-daily` | `0 3 * * *` | `dialpad-sync` |
| `hubspot-sync-daily` | `0 4 * * *` | `hubspot-sync` |
| `account-scoring-daily` | `0 7 * * *` | `account-scoring` |
| `generate-embeddings-daily` | `0 8 * * *` | `generate-embeddings` |

---

## Local Development

### Mock Mode

For testing without API calls:

```bash
export MOCK_MODE=1
export LOCAL_MODE=1
```

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run web app locally
cd web_app
streamlit run app.py

# Test functions locally
functions-framework --target=gmail_sync --port=8080
```

---

## Validation

### Verify Configuration

```bash
# Check environment
echo $GCP_PROJECT_ID
echo $GCP_REGION

# Check secrets
gcloud secrets list
gcloud secrets versions access latest --secret=salesforce-client-id

# Check IAM
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:sales-intelligence-sa"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Secret not found | Verify secret exists and has version |
| Permission denied | Check IAM roles on service account |
| Model not found | Verify `LLM_MODEL` is valid |
| API not enabled | Enable required GCP APIs |

See [Troubleshooting Guide](../operations/TROUBLESHOOTING.md) for detailed solutions.

