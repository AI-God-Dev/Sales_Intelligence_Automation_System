# Complete Client Deployment Guide
## Sales Intelligence & Automation System

This comprehensive guide will walk you through deploying the entire Sales Intelligence & Automation System on your own GCP infrastructure with your own credentials and data.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Project Setup](#gcp-project-setup)
3. [Service Account Creation](#service-account-creation)
4. [Enable Required APIs](#enable-required-apis)
5. [BigQuery Setup](#bigquery-setup)
6. [Secret Manager Configuration](#secret-manager-configuration)
7. [Phase 1: Data Ingestion Functions](#phase-1-data-ingestion-functions)
8. [Phase 2: Intelligence & Automation Functions](#phase-2-intelligence--automation-functions)
9. [Web Application Deployment](#web-application-deployment)
10. [Cloud Scheduler Setup](#cloud-scheduler-setup)
11. [Testing & Verification](#testing--verification)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Access

- [ ] **Google Cloud Platform Account**
  - Active GCP project with billing enabled
  - Owner or Editor role on the project
  - Access to create service accounts and manage IAM

- [ ] **Google Workspace Admin Access** (for Gmail integration)
  - Admin access to configure Domain-Wide Delegation
  - Ability to create OAuth consent screen

- [ ] **Salesforce Admin Access**
  - Admin access to create Connected App
  - API access enabled
  - Username, password, and security token

- [ ] **Dialpad Admin Access**
  - API key generation access
  - User IDs for sales representatives

- [ ] **HubSpot Admin Access**
  - Access to create Private App
  - API key generation

### Required Software

- [ ] **Google Cloud SDK** (`gcloud`) installed and configured
  ```bash
  # Verify installation
  gcloud --version
  
  # Login
  gcloud auth login
  
  # Set default project (replace with your project ID)
  gcloud config set project YOUR_PROJECT_ID
  ```

- [ ] **Python 3.11+** installed
  ```bash
  python --version  # Should be 3.11 or higher
  ```

- [ ] **Git** installed (to clone the repository)

---

## GCP Project Setup

### Step 1: Create or Select GCP Project

```bash
# List existing projects
gcloud projects list

# Create new project (if needed)
gcloud projects create YOUR_PROJECT_ID --name="Sales Intelligence System"

# Set as default project
gcloud config set project YOUR_PROJECT_ID

# Enable billing (required for Cloud Functions and Vertex AI)
# Do this via GCP Console: https://console.cloud.google.com/billing
```

**Replace `YOUR_PROJECT_ID` with your actual GCP project ID throughout this guide.**

### Step 2: Set Environment Variables

```bash
# Windows PowerShell
$env:GCP_PROJECT_ID = "YOUR_PROJECT_ID"
$env:GCP_REGION = "us-central1"  # or your preferred region
$env:BIGQUERY_DATASET = "sales_intelligence"

# Linux/Mac
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
export GCP_REGION="us-central1"
export BIGQUERY_DATASET="sales_intelligence"
```

---

## Service Account Creation

### Step 1: Create Service Account

```bash
# Set variables
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT_NAME = "sales-intelligence-sa"  # Change if desired
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
  --display-name="Sales Intelligence Service Account" `
  --description="Service account for Sales Intelligence Cloud Functions" `
  --project=$PROJECT_ID
```

### Step 2: Grant Required Roles

```bash
# BigQuery roles
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/bigquery.jobUser"

# Vertex AI role (for LLM and embeddings)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/aiplatform.user"

# Secret Manager role
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/secretmanager.secretAccessor"

# Cloud Functions invoker (for function-to-function calls)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/cloudfunctions.invoker"

# Cloud Run invoker (for Gen2 functions)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/run.invoker"

# Logging (for Cloud Functions logs)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/logging.logWriter"

# Pub/Sub (for error notifications)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
  --role="roles/pubsub.publisher"
```

### Step 3: Grant Your User Account Permissions

```bash
# Replace YOUR_EMAIL with your actual email
$YOUR_EMAIL = "your-email@example.com"

# Grant yourself Service Account User role (needed to deploy functions)
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL `
  --member="user:$YOUR_EMAIL" `
  --role="roles/iam.serviceAccountUser" `
  --project=$PROJECT_ID

# Grant yourself Cloud Functions Admin (to deploy functions)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="user:$YOUR_EMAIL" `
  --role="roles/cloudfunctions.admin"

# Grant yourself Cloud Run Admin (for Gen2 functions)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="user:$YOUR_EMAIL" `
  --role="roles/run.admin"

# Grant yourself Secret Manager Admin (to create secrets)
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="user:$YOUR_EMAIL" `
  --role="roles/secretmanager.admin"
```

---

## Enable Required APIs

Enable all required Google Cloud APIs:

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"

# Core APIs
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID

# Data & Storage
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID

# AI & ML
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID  # Vertex AI

# Messaging
gcloud services enable pubsub.googleapis.com --project=$PROJECT_ID

# Gmail API (for email sync)
gcloud services enable gmail.googleapis.com --project=$PROJECT_ID

# IAM
gcloud services enable iam.googleapis.com --project=$PROJECT_ID

# Logging & Monitoring
gcloud services enable logging.googleapis.com --project=$PROJECT_ID
gcloud services enable monitoring.googleapis.com --project=$PROJECT_ID

# Verify APIs are enabled
gcloud services list --enabled --project=$PROJECT_ID
```

---

## BigQuery Setup

### Step 1: Create Dataset

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"
$DATASET_ID = "sales_intelligence"
$REGION = "us-central1"  # Match your GCP region

# Create dataset
bq mk --dataset `
  --location=$REGION `
  --description="Sales Intelligence data warehouse" `
  $PROJECT_ID:$DATASET_ID
```

### Step 2: Create Tables

```bash
# Update the SQL file with your project ID
# Replace all instances of 'maharani-sales-hub-11-2025' with YOUR_PROJECT_ID

# Windows PowerShell - Update SQL file
(Get-Content bigquery/schemas/create_tables.sql) `
  -replace 'maharani-sales-hub-11-2025', 'YOUR_PROJECT_ID' `
  | Set-Content bigquery/schemas/create_tables.sql

# Linux/Mac
sed -i 's/maharani-sales-hub-11-2025/YOUR_PROJECT_ID/g' bigquery/schemas/create_tables.sql

# Execute SQL to create tables
bq query --use_legacy_sql=false --project_id=$PROJECT_ID < bigquery/schemas/create_tables.sql
```

**Or manually run the SQL file in BigQuery Console:**
1. Go to [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Select your project
3. Click "Compose New Query"
4. Copy contents of `bigquery/schemas/create_tables.sql`
5. Replace `maharani-sales-hub-11-2025` with `YOUR_PROJECT_ID`
6. Click "Run"

---

## Secret Manager Configuration

All API keys and credentials must be stored in Google Secret Manager for security.

### Step 1: Create Secrets

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"

# Create secret placeholders (you'll add values in next step)
gcloud secrets create salesforce-client-id --project=$PROJECT_ID
gcloud secrets create salesforce-client-secret --project=$PROJECT_ID
gcloud secrets create salesforce-username --project=$PROJECT_ID
gcloud secrets create salesforce-password --project=$PROJECT_ID
gcloud secrets create salesforce-security-token --project=$PROJECT_ID
gcloud secrets create salesforce-refresh-token --project=$PROJECT_ID
gcloud secrets create salesforce-instance-url --project=$PROJECT_ID
gcloud secrets create dialpad-api-key --project=$PROJECT_ID
gcloud secrets create hubspot-api-key --project=$PROJECT_ID
gcloud secrets create openai-api-key --project=$PROJECT_ID  # Optional
gcloud secrets create anthropic-api-key --project=$PROJECT_ID  # Optional
```

### Step 2: Add Secret Values

**⚠️ SECURITY WARNING**: Never commit these values to git. Only store in Secret Manager.

```bash
# Add Salesforce credentials
echo -n "YOUR_SALESFORCE_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_USERNAME" | gcloud secrets versions add salesforce-username --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=- --project=$PROJECT_ID

# Add Dialpad API key
echo -n "YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=- --project=$PROJECT_ID

# Add HubSpot API key (Private App access token)
echo -n "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" | gcloud secrets versions add hubspot-api-key --data-file=- --project=$PROJECT_ID

# Optional: Add LLM API keys (if not using Vertex AI)
# echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$PROJECT_ID
# echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=- --project=$PROJECT_ID
```

### Step 3: Grant Service Account Access to Secrets

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"
$SERVICE_ACCOUNT_EMAIL = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# List of all secrets
$secrets = @(
    "salesforce-client-id",
    "salesforce-client-secret",
    "salesforce-username",
    "salesforce-password",
    "salesforce-security-token",
    "salesforce-refresh-token",
    "salesforce-instance-url",
    "dialpad-api-key",
    "hubspot-api-key",
    "openai-api-key",
    "anthropic-api-key"
)

# Grant access to each secret
foreach ($secret in $secrets) {
    gcloud secrets add-iam-policy-binding $secret `
      --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
      --role="roles/secretmanager.secretAccessor" `
      --project=$PROJECT_ID
}
```

### Step 4: Gmail OAuth Setup

Gmail integration requires OAuth 2.0 credentials. These are stored as environment variables, not secrets.

**Create OAuth Credentials:**
1. Go to [GCP Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Web application"
4. Authorized redirect URIs: `http://localhost:8080` (for local testing)
5. Save Client ID and Client Secret

**Set Environment Variables:**
```bash
# Windows PowerShell
$env:GMAIL_OAUTH_CLIENT_ID = "YOUR_GMAIL_CLIENT_ID"
$env:GMAIL_OAUTH_CLIENT_SECRET = "YOUR_GMAIL_CLIENT_SECRET"

# Linux/Mac
export GMAIL_OAUTH_CLIENT_ID="YOUR_GMAIL_CLIENT_ID"
export GMAIL_OAUTH_CLIENT_SECRET="YOUR_GMAIL_CLIENT_SECRET"
```

**Configure Domain-Wide Delegation (for Gmail API):**
1. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your service account
3. Click "Show Domain-Wide Delegation"
4. Enable "Enable Google Workspace Domain-wide Delegation"
5. Note the Client ID
6. In Google Workspace Admin Console:
   - Go to Security > API Controls > Domain-wide Delegation
   - Add new API client with the Client ID
   - OAuth scopes: `https://www.googleapis.com/auth/gmail.readonly`

---

## Phase 1: Data Ingestion Functions

### Step 1: Update Deployment Script

Edit `scripts/deploy_functions.ps1` and update:
- `$projectId = "YOUR_PROJECT_ID"`
- `$region = "YOUR_REGION"` (e.g., "us-central1")
- `$serviceAccount = "YOUR_SERVICE_ACCOUNT_EMAIL"`

### Step 2: Deploy Phase 1 Functions

```bash
# Navigate to project root
cd /path/to/SALES

# Run deployment script
.\scripts\deploy_functions.ps1

# Or deploy individually (see script for commands)
```

**Functions Deployed:**
1. `gmail-sync` - Syncs emails from Gmail
2. `salesforce-sync` - Syncs data from Salesforce
3. `dialpad-sync` - Syncs calls from Dialpad
4. `hubspot-sync` - Syncs sequences from HubSpot
5. `entity-resolution` - Matches emails/calls to accounts

### Step 3: Verify Deployment

```bash
# List deployed functions
gcloud functions list --gen2 --region=us-central1 --project=YOUR_PROJECT_ID

# Check specific function
gcloud functions describe gmail-sync --gen2 --region=us-central1 --project=YOUR_PROJECT_ID
```

---

## Phase 2: Intelligence & Automation Functions

### Step 1: Update Deployment Script

Edit `scripts/deploy_phase2_functions.ps1` and update:
- `$PROJECT_ID = "YOUR_PROJECT_ID"`
- `$REGION = "YOUR_REGION"`
- `$SERVICE_ACCOUNT = "YOUR_SERVICE_ACCOUNT_EMAIL"`

### Step 2: Deploy Phase 2 Functions

```bash
# Navigate to project root
cd /path/to/SALES

# Run deployment script
.\scripts\deploy_phase2_functions.ps1
```

**Functions Deployed:**
1. `generate-embeddings` - Generates vector embeddings
2. `account-scoring` - AI-powered account scoring
3. `nlp-query` - Natural language to SQL queries
4. `semantic-search` - Semantic search using vectors
5. `create-leads` - Creates Salesforce leads
6. `enroll-hubspot` - Enrolls contacts in HubSpot sequences
7. `get-hubspot-sequences` - Gets available HubSpot sequences
8. `generate-email-reply` - Generates AI email replies

### Step 3: Verify Deployment

```bash
# List all functions
gcloud run services list --region=us-central1 --project=YOUR_PROJECT_ID

# Test a function
gcloud functions call nlp-query `
  --gen2 `
  --region=us-central1 `
  --project=YOUR_PROJECT_ID `
  --data='{"query": "How many accounts do we have?"}'
```

---

## Web Application Deployment

### Option 1: Deploy to Cloud Run (Recommended)

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"
$REGION = "us-central1"

# Navigate to web app directory
cd web_app

# Deploy to Cloud Run
gcloud run deploy sales-intelligence-web `
  --source . `
  --platform managed `
  --region $REGION `
  --project $PROJECT_ID `
  --allow-unauthenticated `
  --memory 1Gi `
  --timeout 300 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION"

# Get the service URL
gcloud run services describe sales-intelligence-web `
  --region $REGION `
  --project $PROJECT_ID `
  --format="value(status.url)"
```

### Option 2: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt
pip install streamlit

# Set environment variables
$env:GCP_PROJECT_ID = "YOUR_PROJECT_ID"
$env:GCP_REGION = "us-central1"

# Run Streamlit app
cd web_app
streamlit run app.py
```

**Access the app**: http://localhost:8501

---

## Cloud Scheduler Setup

### Step 1: Create Scheduled Jobs

```bash
$PROJECT_ID = "YOUR_PROJECT_ID"
$REGION = "us-central1"
$SERVICE_ACCOUNT_EMAIL = "sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Get function URLs
$ACCOUNT_SCORING_URL = (gcloud functions describe account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
$GENERATE_EMBEDDINGS_URL = (gcloud functions describe generate-embeddings --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")

# Daily account scoring (7 AM)
gcloud scheduler jobs create http account-scoring-daily `
  --location=$REGION `
  --schedule="0 7 * * *" `
  --uri=$ACCOUNT_SCORING_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT_EMAIL `
  --oidc-token-audience=$ACCOUNT_SCORING_URL `
  --project=$PROJECT_ID

# Daily embeddings generation (8 AM)
gcloud scheduler jobs create http generate-embeddings-daily `
  --location=$REGION `
  --schedule="0 8 * * *" `
  --uri=$GENERATE_EMBEDDINGS_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT_EMAIL `
  --oidc-token-audience=$GENERATE_EMBEDDINGS_URL `
  --project=$PROJECT_ID

# Hourly Gmail sync
$GMAIL_SYNC_URL = (gcloud functions describe gmail-sync --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
gcloud scheduler jobs create http gmail-sync-hourly `
  --location=$REGION `
  --schedule="0 * * * *" `
  --uri=$GMAIL_SYNC_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT_EMAIL `
  --oidc-token-audience=$GMAIL_SYNC_URL `
  --project=$PROJECT_ID

# Daily Salesforce sync
$SF_SYNC_URL = (gcloud functions describe salesforce-sync --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
gcloud scheduler jobs create http salesforce-sync-daily `
  --location=$REGION `
  --schedule="0 2 * * *" `
  --uri=$SF_SYNC_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT_EMAIL `
  --oidc-token-audience=$SF_SYNC_URL `
  --project=$PROJECT_ID
```

### Step 2: Verify Scheduled Jobs

```bash
# List all scheduled jobs
gcloud scheduler jobs list --location=us-central1 --project=YOUR_PROJECT_ID

# Test a job manually
gcloud scheduler jobs run account-scoring-daily --location=us-central1 --project=YOUR_PROJECT_ID
```

---

## Testing & Verification

### Step 1: Test Data Ingestion

```bash
# Test Gmail sync
gcloud functions call gmail-sync --gen2 --region=us-central1 --project=YOUR_PROJECT_ID

# Test Salesforce sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 --project=YOUR_PROJECT_ID --data='{"object_type": "Account"}'

# Check BigQuery for data
bq query --use_legacy_sql=false --project_id=YOUR_PROJECT_ID "
SELECT COUNT(*) as total_accounts 
FROM \`YOUR_PROJECT_ID.sales_intelligence.sf_accounts\`
"
```

### Step 2: Test Intelligence Functions

```bash
# Test account scoring (with limit for testing)
gcloud functions call account-scoring `
  --gen2 `
  --region=us-central1 `
  --project=YOUR_PROJECT_ID `
  --data='{"limit": 10}'

# Test NLP query
gcloud functions call nlp-query `
  --gen2 `
  --region=us-central1 `
  --project=YOUR_PROJECT_ID `
  --data='{"query": "Show me top 10 accounts by revenue"}'

# Test semantic search
gcloud functions call semantic-search `
  --gen2 `
  --region=us-central1 `
  --project=YOUR_PROJECT_ID `
  --data='{"query": "budget discussions", "type": "accounts", "limit": 10}'
```

### Step 3: Verify BigQuery Data

```sql
-- Check account recommendations
SELECT COUNT(*) as total_scores, MAX(score_date) as latest_date
FROM `YOUR_PROJECT_ID.sales_intelligence.account_recommendations`;

-- Check email sync
SELECT COUNT(*) as total_emails, MAX(sent_at) as latest_email
FROM `YOUR_PROJECT_ID.sales_intelligence.gmail_messages`;

-- Check call sync
SELECT COUNT(*) as total_calls, MAX(call_time) as latest_call
FROM `YOUR_PROJECT_ID.sales_intelligence.dialpad_calls`;
```

### Step 4: Test Web Application

1. Access web app URL (from Cloud Run deployment or http://localhost:8501)
2. Login with your email
3. Test each feature:
   - Dashboard
   - Account Scoring
   - Natural Language Query
   - Semantic Search
   - Unmatched Emails

---

## Configuration Customization

### Update Configuration Files

**1. Update `config/config.py`:**
```python
# Change default project ID
gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")

# Update Gmail mailboxes
gmail_mailboxes: list[str] = [
    "sales-rep-1@yourcompany.com",
    "sales-rep-2@yourcompany.com",
    "sales-rep-3@yourcompany.com",
]

# Choose LLM provider
llm_provider: str = os.getenv("LLM_PROVIDER", "vertex_ai")  # or "anthropic"
```

**2. Update Deployment Scripts:**
- Replace all instances of `maharani-sales-hub-11-2025` with `YOUR_PROJECT_ID`
- Update service account name if different
- Update region if different

**3. Update BigQuery Queries:**
- Replace `maharani-sales-hub-11-2025` with `YOUR_PROJECT_ID` in all SQL files
- Update dataset name if different from `sales_intelligence`

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

**Error**: `Permission 'iam.serviceaccounts.actAs' denied`

**Solution**:
```bash
# Grant yourself Service Account User role
gcloud iam service-accounts add-iam-policy-binding YOUR_SERVICE_ACCOUNT_EMAIL `
  --member="user:YOUR_EMAIL" `
  --role="roles/iam.serviceAccountUser" `
  --project=YOUR_PROJECT_ID
```

#### 2. Secret Not Found

**Error**: `Secret 'xxx' not found in Secret Manager`

**Solution**:
- Verify secret exists: `gcloud secrets list --project=YOUR_PROJECT_ID`
- Verify service account has access: `gcloud secrets get-iam-policy SECRET_NAME --project=YOUR_PROJECT_ID`
- Grant access: `gcloud secrets add-iam-policy-binding SECRET_NAME --member="serviceAccount:YOUR_SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"`

#### 3. Function Deployment Fails

**Error**: `Source directory does not have file [main.py]`

**Solution**:
- Ensure you're running deployment script from project root
- Verify `main.py` exists in project root
- Check script path resolution

#### 4. Memory Limit Exceeded

**Error**: `Memory limit exceeded`

**Solution**:
- Increase memory allocation in deployment script
- For account-scoring, use 2048MB minimum
- Check function logs for memory usage

#### 5. API Not Enabled

**Error**: `API 'xxx.googleapis.com' is not enabled`

**Solution**:
```bash
# Enable the required API
gcloud services enable API_NAME --project=YOUR_PROJECT_ID
```

#### 6. BigQuery Table Not Found

**Error**: `Table 'xxx' not found`

**Solution**:
- Verify tables were created: `bq ls YOUR_PROJECT_ID:sales_intelligence`
- Re-run table creation SQL
- Check dataset name matches configuration

---

## Post-Deployment Checklist

- [ ] All Phase 1 functions deployed and tested
- [ ] All Phase 2 functions deployed and tested
- [ ] Web application accessible
- [ ] Data syncing from all sources (Gmail, Salesforce, Dialpad, HubSpot)
- [ ] Account scoring generating results
- [ ] BigQuery tables populated with data
- [ ] Cloud Scheduler jobs created and running
- [ ] Error notifications configured (Pub/Sub)
- [ ] Monitoring and logging working
- [ ] User access configured for web app

---

## Support & Maintenance

### Monitoring

- **Cloud Functions Logs**: `gcloud functions logs read FUNCTION_NAME --gen2 --region=REGION --limit=50`
- **BigQuery Usage**: Monitor in GCP Console > BigQuery > Usage
- **Cost Monitoring**: GCP Console > Billing

### Regular Maintenance

1. **Monitor Function Execution**: Check logs weekly
2. **Review Costs**: Monitor monthly spending
3. **Update Secrets**: Rotate API keys quarterly
4. **Review Data Quality**: Check match rates monthly
5. **Update Dependencies**: Review and update packages quarterly

---

## Security Best Practices

1. ✅ **Never commit secrets** to git
2. ✅ **Use Secret Manager** for all credentials
3. ✅ **Rotate API keys** regularly
4. ✅ **Use least-privilege** IAM roles
5. ✅ **Enable audit logging** for sensitive operations
6. ✅ **Review IAM policies** regularly
7. ✅ **Use service accounts** instead of user accounts for functions
8. ✅ **Enable VPC** if handling sensitive data

---

## Cost Estimation

### Monthly Costs (Approximate)

- **Cloud Functions**: $0.40 per million invocations + compute time
- **BigQuery**: $5 per TB queried (first 1 TB free)
- **Vertex AI**: 
  - Account Scoring: ~$0.50-2.00 per 100 accounts (daily)
  - Embeddings: ~$0.10 per 1M tokens
- **Cloud Run**: $0.40 per million requests + compute time
- **Secret Manager**: $0.06 per secret version per month
- **Cloud Scheduler**: $0.10 per job per month

**Estimated Total**: $50-200/month (depending on data volume)

---

## Next Steps

1. ✅ Complete all deployment steps above
2. ✅ Test all functions
3. ✅ Verify data is syncing correctly
4. ✅ Train users on web application
5. ✅ Set up monitoring alerts
6. ✅ Schedule regular maintenance

---

**📞 Support**: For issues or questions, refer to troubleshooting section or contact your implementation team.

**📚 Additional Documentation**:
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)

---

**Last Updated**: 2025-01-XX
**Version**: 1.0

