# Google Secret Manager - Required Secrets

This document lists all secrets that need to be stored in Google Secret Manager for the Sales Intelligence system.

## Gmail Secrets

### `gmail-oauth-client-id`
- **Description**: Gmail OAuth 2.0 Client ID
- **Format**: String (e.g., `123456789-abcdefghijklmnop.apps.googleusercontent.com`)
- **Source**: Google Cloud Console → APIs & Services → Credentials
- **Usage**: Used for Gmail API authentication with domain-wide delegation
- **Required**: Yes

### `gmail-oauth-client-secret`
- **Description**: Gmail OAuth 2.0 Client Secret
- **Format**: String (e.g., `GOCSPX-abcdefghijklmnopqrstuvwxyz`)
- **Source**: Google Cloud Console → APIs & Services → Credentials
- **Usage**: Used for Gmail API authentication with domain-wide delegation
- **Required**: Yes

**Note**: For domain-wide delegation (DWD), these credentials are used with the service account to impersonate users without requiring individual OAuth flows.

## Salesforce Secrets

### `salesforce-client-id`
- **Description**: Salesforce Connected App Client ID (Consumer Key)
- **Format**: String (e.g., `3MVG9...`)
- **Source**: Salesforce Setup → App Manager → Connected Apps
- **Usage**: OAuth 2.0 authentication for Salesforce API
- **Required**: Yes

### `salesforce-client-secret`
- **Description**: Salesforce Connected App Client Secret (Consumer Secret)
- **Format**: String (e.g., `1234567890ABCDEF...`)
- **Source**: Salesforce Setup → App Manager → Connected Apps
- **Usage**: OAuth 2.0 authentication for Salesforce API
- **Required**: Yes

### `salesforce-username`
- **Description**: Salesforce API user username
- **Format**: String (e.g., `api-user@example.com`)
- **Source**: Salesforce user account
- **Usage**: Username for API authentication
- **Required**: Yes

### `salesforce-password`
- **Description**: Salesforce API user password
- **Format**: String (plain text password)
- **Source**: Salesforce user account
- **Usage**: Password for API authentication
- **Required**: Yes

### `salesforce-security-token`
- **Description**: Salesforce security token
- **Format**: String (24-character alphanumeric)
- **Source**: Salesforce user settings → Reset Security Token
- **Usage**: Required for API authentication when IP restrictions are enabled
- **Required**: Yes

### `salesforce-refresh-token`
- **Description**: OAuth 2.0 refresh token for Salesforce
- **Format**: String (long alphanumeric token)
- **Source**: Generated during OAuth flow
- **Usage**: Used to obtain new access tokens without re-authentication
- **Required**: Yes (if using OAuth flow instead of username/password)

## Dialpad Secrets

### `dialpad-api-key`
- **Description**: Dialpad API key
- **Format**: String (API key from Dialpad)
- **Source**: Dialpad Admin → Integrations → API
- **Usage**: Authentication for Dialpad API calls
- **Required**: Yes

## HubSpot Secrets

### `hubspot-client-id`
- **Description**: HubSpot Private App Client ID (if using OAuth)
- **Format**: String
- **Source**: HubSpot Private App settings
- **Usage**: OAuth 2.0 authentication (if using OAuth flow)
- **Required**: No (only if using OAuth instead of Private App token)

### `hubspot-client-secret`
- **Description**: HubSpot Private App Client Secret (if using OAuth)
- **Format**: String
- **Source**: HubSpot Private App settings
- **Usage**: OAuth 2.0 authentication (if using OAuth flow)
- **Required**: No (only if using OAuth instead of Private App token)

### `hubspot-api-key`
- **Description**: HubSpot Private App Access Token
- **Format**: String (e.g., `pat-na1-...`)
- **Source**: HubSpot Settings → Integrations → Private Apps → [Your App] → Access Token
- **Usage**: Authentication for HubSpot API calls
- **Required**: Yes

## LLM Provider Secrets

- Vertex AI only; uses Application Default Credentials (ADC). No OpenAI/Anthropic secrets are required.

## Secret Creation Commands

Use the following commands to create and populate secrets:

```bash
# Set project ID
export PROJECT_ID="maharani-sales-hub-11-2025"

# Create secret (example)
echo -n "YOUR_SECRET_VALUE" | gcloud secrets create SECRET_NAME \
  --data-file=- \
  --project="$PROJECT_ID" \
  --replication-policy="automatic"

# Grant service account access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID"
```

## Example: Creating All Secrets

```bash
#!/bin/bash
PROJECT_ID="maharani-sales-hub-11-2025"
SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

# Gmail
echo -n "YOUR_GMAIL_CLIENT_ID" | gcloud secrets versions add gmail-oauth-client-id --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_GMAIL_CLIENT_SECRET" | gcloud secrets versions add gmail-oauth-client-secret --data-file=- --project="$PROJECT_ID"

# Salesforce
echo -n "YOUR_SF_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SF_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SF_USERNAME" | gcloud secrets versions add salesforce-username --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SF_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SF_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_SF_REFRESH_TOKEN" | gcloud secrets versions add salesforce-refresh-token --data-file=- --project="$PROJECT_ID"

# Dialpad
echo -n "YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=- --project="$PROJECT_ID"

# HubSpot
echo -n "YOUR_HUBSPOT_API_KEY" | gcloud secrets versions add hubspot-api-key --data-file=- --project="$PROJECT_ID"

# LLM Providers
echo -n "YOUR_OPENAI_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project="$PROJECT_ID"
echo -n "YOUR_ANTHROPIC_KEY" | gcloud secrets versions add anthropic-api-key --data-file=- --project="$PROJECT_ID"
```

## Security Best Practices

1. **Never commit secrets to version control**
   - Use `.gitignore` to exclude files containing secrets
   - Use Secret Manager for all sensitive values

2. **Rotate secrets regularly**
   - Gmail OAuth: Every 90 days
   - Salesforce tokens: Every 90 days
   - API keys: Every 180 days

3. **Use least privilege**
   - Grant service account only `secretmanager.secretAccessor` role
   - Use separate service accounts for different environments

4. **Monitor secret access**
   - Enable Cloud Audit Logs for Secret Manager
   - Set up alerts for unusual access patterns

5. **Use secret versions**
   - Keep old versions for rollback capability
   - Use version labels for environment-specific values

## Placeholder Values

For development/testing, you can use placeholder values:

- Gmail: Use test OAuth credentials from Google Cloud Console
- Salesforce: Use sandbox credentials
- Dialpad: Use test API key from Dialpad
- HubSpot: Use test Private App token
- LLM: Use test API keys (with rate limits)

**Note**: Replace all placeholders with actual production values before deploying to production.

