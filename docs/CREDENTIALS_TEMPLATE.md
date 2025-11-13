# Credentials Template

Use this template to document all required credentials. **DO NOT COMMIT THIS FILE WITH REAL VALUES** - keep it secure and use it as a reference.

## GCP Credentials

```
GCP Project ID: [your-project-id]
GCP Region: us-central1
Service Account Email: [service-account]@[project-id].iam.gserviceaccount.com
Service Account Key File: [path-to-json-key-file]
```

## Gmail OAuth

```
OAuth Client ID: [xxxxx].apps.googleusercontent.com
OAuth Client Secret: [xxxxx]
Authorized Redirect URI: https://[your-domain]/oauth/callback

Mailbox 1 (Anand):
  Email: anand@maharaniweddings.com
  Refresh Token: [token]

Mailbox 2:
  Email: [email]
  Refresh Token: [token]

Mailbox 3:
  Email: [email]
  Refresh Token: [token]
```

## Salesforce

```
Username: [username]
Password: [password]
Security Token: [token]
Domain: login (or test for sandbox)
Instance URL: https://[instance].salesforce.com

Connected App:
  Consumer Key: [key]
  Consumer Secret: [secret]
  Callback URL: [url]

Integration User:
  Username: integration@maharaniweddings.com
  User ID: [sf-user-id]
```

## Dialpad

```
API Key: [api-key]
API Base URL: https://dialpad.com/api/v2

User IDs:
  User 1 (Anand): [user-id]
  User 2: [user-id]
  User 3: [user-id]
```

## HubSpot

```
API Key: [api-key]
OR
OAuth Access Token: [token]
OAuth Refresh Token: [token]
```

## LLM Provider

### Anthropic
```
API Key: [api-key]
Model: claude-3-5-sonnet-20241022
```

### OpenAI
```
API Key: [api-key]
Organization ID: [org-id] (optional)
Model: gpt-4
Embedding Model: text-embedding-3-small
```

### Vertex AI
```
Project ID: [same as GCP project]
Region: us-central1
Service Account: [same as GCP service account]
```

## Secret Manager Secret Names

```
salesforce-username
salesforce-password
salesforce-security-token
dialpad-api-key
hubspot-api-key
openai-api-key
anthropic-api-key
```

## Environment Variables

```bash
# Copy to .env file (DO NOT COMMIT)
GCP_PROJECT_ID=[your-project-id]
GCP_REGION=us-central1
BIGQUERY_DATASET=sales_intelligence
SALESFORCE_DOMAIN=login
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
EMBEDDING_MODEL=text-embedding-3-small
GMAIL_OAUTH_CLIENT_ID=[client-id]
GMAIL_OAUTH_CLIENT_SECRET=[client-secret]
```

## Quick Setup Commands

```bash
# Set GCP project
gcloud config set project [your-project-id]

# Create secrets (replace [value] with actual values)
echo -n "[value]" | gcloud secrets create salesforce-username --data-file=-
echo -n "[value]" | gcloud secrets create salesforce-password --data-file=-
echo -n "[value]" | gcloud secrets create salesforce-security-token --data-file=-
echo -n "[value]" | gcloud secrets create dialpad-api-key --data-file=-
echo -n "[value]" | gcloud secrets create hubspot-api-key --data-file=-
echo -n "[value]" | gcloud secrets create openai-api-key --data-file=-
echo -n "[value]" | gcloud secrets create anthropic-api-key --data-file=-

# Grant service account access to secrets
gcloud secrets add-iam-policy-binding salesforce-username \
  --member="serviceAccount:[service-account-email]" \
  --role="roles/secretmanager.secretAccessor"
# Repeat for all secrets...
```

---

**⚠️ SECURITY WARNING**: 
- Never commit this file with real credentials
- Store credentials only in Secret Manager
- Use environment variables for non-sensitive config
- Rotate credentials regularly
- Use least-privilege access principles

