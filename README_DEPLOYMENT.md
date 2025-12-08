# Sales Intelligence Automation System - Deployment Guide

## 📋 Overview

This guide provides step-by-step instructions for deploying the complete Sales Intelligence Automation System to Google Cloud Platform. The system consists of:

- **Phase 1**: Data ingestion from Gmail, Salesforce, Dialpad, and HubSpot
- **Phase 2**: AI-powered intelligence (scoring, embeddings, NLP queries, semantic search)
- **Phase 3**: Web application dashboard

---

## 🎯 Quick Start

For experienced users, the deployment can be completed in 4 steps:

```powershell
# 1. Set environment variables
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_REGION = "us-central1"
$env:GCP_USER_EMAIL = "your-email@example.com"

# 2. Setup service account and APIs
.\scripts\setup_service_account.ps1

# 3. Create BigQuery dataset and tables
.\scripts\create_bigquery_datasets.ps1

# 4. Deploy all Cloud Functions
.\scripts\deploy_all.ps1
```

---

## 📚 Detailed Deployment Steps

### Prerequisites

#### Required Software
- **Google Cloud SDK** (`gcloud`) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PowerShell 5.1+** (Windows) or **Bash** (Linux/Mac)

#### Required Accounts & Access
- ✅ Google Cloud Platform account with billing enabled
- ✅ Owner or Editor role on GCP project
- ✅ Google Workspace Admin access (for Gmail integration)
- ✅ Salesforce Admin access
- ✅ Dialpad Admin access
- ✅ HubSpot Admin access

#### Verify Installation

```powershell
# Check gcloud
gcloud --version

# Check Python
python --version  # Should be 3.11 or higher

# Authenticate with GCP
gcloud auth login
gcloud auth application-default login
```

---

### Step 1: GCP Project Setup

#### 1.1 Create or Select Project

```powershell
# List existing projects
gcloud projects list

# Create new project (if needed)
gcloud projects create YOUR_PROJECT_ID --name="Sales Intelligence System"

# Set as default
gcloud config set project YOUR_PROJECT_ID
```

#### 1.2 Set Environment Variables

```powershell
# Windows PowerShell
$env:GCP_PROJECT_ID = "YOUR_PROJECT_ID"
$env:GCP_REGION = "us-central1"
$env:BIGQUERY_DATASET = "sales_intelligence"
$env:GCP_SERVICE_ACCOUNT_NAME = "sales-intelligence-sa"
$env:GCP_USER_EMAIL = "your-email@example.com"

# Linux/Mac
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
export GCP_REGION="us-central1"
export BIGQUERY_DATASET="sales_intelligence"
export GCP_SERVICE_ACCOUNT_NAME="sales-intelligence-sa"
export GCP_USER_EMAIL="your-email@example.com"
```

**⚠️ Important**: Replace `YOUR_PROJECT_ID` with your actual GCP project ID throughout this guide.

---

### Step 2: Service Account & IAM Setup

Run the automated setup script:

```powershell
.\scripts\setup_service_account.ps1
```

This script will:
- ✅ Create service account (`sales-intelligence-sa`)
- ✅ Grant all required IAM roles to service account
- ✅ Grant deployment permissions to your user account
- ✅ Enable all required GCP APIs

**Manual Setup** (if script fails):

```powershell
# Create service account
gcloud iam service-accounts create sales-intelligence-sa `
  --display-name="Sales Intelligence Service Account" `
  --project=$env:GCP_PROJECT_ID

# Grant roles to service account
$SERVICE_ACCOUNT = "sales-intelligence-sa@$env:GCP_PROJECT_ID.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/bigquery.dataEditor"

# ... (see script for full list of roles)
```

---

### Step 3: BigQuery Setup

#### 3.1 Create Dataset and Tables

Run the automated setup script:

```powershell
.\scripts\create_bigquery_datasets.ps1
```

This script will:
- ✅ Create BigQuery dataset (`sales_intelligence`)
- ✅ Create all required tables from SQL schema
- ✅ Verify table creation

**Manual Setup** (if script fails):

```powershell
# Create dataset
bq mk --dataset `
  --location=us-central1 `
  --description="Sales Intelligence data warehouse" `
  $env:GCP_PROJECT_ID:sales_intelligence

# Create tables (update project ID in SQL file first)
bq query --use_legacy_sql=false --project_id=$env:GCP_PROJECT_ID < bigquery\schemas\create_tables.sql
```

**⚠️ Important**: Before running the SQL file, replace all instances of `maharani-sales-hub-11-2025` with your project ID.

---

### Step 4: Secret Manager Configuration

All API credentials must be stored in Google Secret Manager.

#### 4.1 Create Secret Placeholders

```powershell
$PROJECT_ID = $env:GCP_PROJECT_ID

# Salesforce secrets
gcloud secrets create salesforce-client-id --project=$PROJECT_ID
gcloud secrets create salesforce-client-secret --project=$PROJECT_ID
gcloud secrets create salesforce-username --project=$PROJECT_ID
gcloud secrets create salesforce-password --project=$PROJECT_ID
gcloud secrets create salesforce-security-token --project=$PROJECT_ID
gcloud secrets create salesforce-refresh-token --project=$PROJECT_ID  # Optional (OAuth)
gcloud secrets create salesforce-instance-url --project=$PROJECT_ID  # Optional

# Dialpad secret
gcloud secrets create dialpad-api-key --project=$PROJECT_ID

# HubSpot secret
gcloud secrets create hubspot-api-key --project=$PROJECT_ID

# Vertex-only: no OpenAI/Anthropic secrets required (ADC)
```

#### 4.2 Add Secret Values

**⚠️ SECURITY WARNING**: Never commit these values to git. Only store in Secret Manager.

```powershell
# Add Salesforce credentials
echo -n "YOUR_SALESFORCE_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_USERNAME" | gcloud secrets versions add salesforce-username --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=- --project=$PROJECT_ID
echo -n "YOUR_SALESFORCE_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=- --project=$PROJECT_ID

# Add Dialpad API key
echo -n "YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=- --project=$PROJECT_ID

# Add HubSpot API key (Private App access token format: pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
echo -n "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" | gcloud secrets versions add hubspot-api-key --data-file=- --project=$PROJECT_ID
```

#### 4.3 Grant Service Account Access to Secrets

```powershell
$SERVICE_ACCOUNT = "sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com"
$secrets = @(
    "salesforce-client-id", "salesforce-client-secret", "salesforce-username",
    "salesforce-password", "salesforce-security-token", "salesforce-refresh-token",
    "salesforce-instance-url", "dialpad-api-key", "hubspot-api-key"
)

foreach ($secret in $secrets) {
    gcloud secrets add-iam-policy-binding $secret `
      --member="serviceAccount:$SERVICE_ACCOUNT" `
      --role="roles/secretmanager.secretAccessor" `
      --project=$PROJECT_ID
}
```

#### 4.4 Gmail OAuth Setup

Gmail integration requires OAuth 2.0 credentials (stored as environment variables, not secrets).

1. **Create OAuth Credentials**:
   - Go to [GCP Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Authorized redirect URIs: `http://localhost:8080` (for local testing)

2. **Set Environment Variables**:
   ```powershell
   $env:GMAIL_OAUTH_CLIENT_ID = "YOUR_GMAIL_CLIENT_ID"
   $env:GMAIL_OAUTH_CLIENT_SECRET = "YOUR_GMAIL_CLIENT_SECRET"
   ```

3. **Configure Domain-Wide Delegation** (for Gmail API):
   - Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Select your service account
   - Click "Show Domain-Wide Delegation"
   - Enable "Enable Google Workspace Domain-wide Delegation"
   - Note the Client ID
   - In Google Workspace Admin Console:
     - Go to Security > API Controls > Domain-wide Delegation
     - Add new API client with the Client ID
     - OAuth scopes: `https://www.googleapis.com/auth/gmail.readonly`

---

### Step 5: Deploy Cloud Functions

#### 5.1 Deploy All Functions

Run the master deployment script:

```powershell
.\scripts\deploy_all.ps1
```

This script deploys all 13 Cloud Functions:
- **Phase 1** (5 functions): gmail-sync, salesforce-sync, dialpad-sync, hubspot-sync, entity-resolution
- **Phase 2** (8 functions): generate-embeddings, account-scoring, nlp-query, semantic-search, create-leads, enroll-hubspot, get-hubspot-sequences, generate-email-reply

**Deployment Time**: ~15-20 minutes for all functions

#### 5.2 Verify Deployment

```powershell
# List all deployed functions
gcloud functions list --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# Check specific function
gcloud functions describe gmail-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# View function logs
gcloud functions logs read gmail-sync --gen2 --region=us-central1 --limit=50
```

#### 5.3 Test Functions

```powershell
# Test Gmail sync
gcloud functions call gmail-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# Test Salesforce sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"object_type": "Account"}'

# Test account scoring (with limit for testing)
gcloud functions call account-scoring --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"limit": 10}'
```

---

### Step 6: Cloud Scheduler Setup

Create scheduled jobs to run functions automatically.

#### 6.1 Get Function URLs

```powershell
$REGION = $env:GCP_REGION
$PROJECT_ID = $env:GCP_PROJECT_ID
$SERVICE_ACCOUNT = "sales-intelligence-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Get function URLs
$GMAIL_SYNC_URL = (gcloud functions describe gmail-sync --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
$SF_SYNC_URL = (gcloud functions describe salesforce-sync --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
$ACCOUNT_SCORING_URL = (gcloud functions describe account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
$EMBEDDINGS_URL = (gcloud functions describe generate-embeddings --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
```

#### 6.2 Create Scheduled Jobs

```powershell
# Daily account scoring (7 AM)
gcloud scheduler jobs create http account-scoring-daily `
  --location=$REGION `
  --schedule="0 7 * * *" `
  --uri=$ACCOUNT_SCORING_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$ACCOUNT_SCORING_URL `
  --project=$PROJECT_ID

# Daily embeddings generation (8 AM)
gcloud scheduler jobs create http generate-embeddings-daily `
  --location=$REGION `
  --schedule="0 8 * * *" `
  --uri=$EMBEDDINGS_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$EMBEDDINGS_URL `
  --project=$PROJECT_ID

# Hourly Gmail sync
gcloud scheduler jobs create http gmail-sync-hourly `
  --location=$REGION `
  --schedule="0 * * * *" `
  --uri=$GMAIL_SYNC_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$GMAIL_SYNC_URL `
  --project=$PROJECT_ID

# Daily Salesforce sync (2 AM)
gcloud scheduler jobs create http salesforce-sync-daily `
  --location=$REGION `
  --schedule="0 2 * * *" `
  --uri=$SF_SYNC_URL `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$SF_SYNC_URL `
  --project=$PROJECT_ID
```

#### 6.3 Verify Scheduled Jobs

```powershell
# List all scheduled jobs
gcloud scheduler jobs list --location=us-central1 --project=$env:GCP_PROJECT_ID

# Test a job manually
gcloud scheduler jobs run account-scoring-daily --location=us-central1 --project=$env:GCP_PROJECT_ID
```

---

### Step 7: Web Application Deployment

#### Option 1: Deploy to Cloud Run (Recommended)

```powershell
$PROJECT_ID = $env:GCP_PROJECT_ID
$REGION = $env:GCP_REGION

cd web_app

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

#### Option 2: Run Locally

```powershell
# Install dependencies
pip install -r web_app/requirements.txt
pip install streamlit

# Set environment variables
$env:GCP_PROJECT_ID = "YOUR_PROJECT_ID"
$env:GCP_REGION = "us-central1"

# Run Streamlit app
cd web_app
streamlit run app.py
```

Access the app at: http://localhost:8501

---

## ✅ Post-Deployment Checklist

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

## 🔍 Verification & Testing

### Test Data Ingestion

```powershell
# Test Gmail sync
gcloud functions call gmail-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID

# Test Salesforce sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"object_type": "Account"}'

# Check BigQuery for data
bq query --use_legacy_sql=false --project_id=$env:GCP_PROJECT_ID "
SELECT COUNT(*) as total_accounts 
FROM \`$env:GCP_PROJECT_ID.sales_intelligence.sf_accounts\`
"
```

### Test Intelligence Functions

```powershell
# Test account scoring
gcloud functions call account-scoring --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"limit": 10}'

# Test NLP query
gcloud functions call nlp-query --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"query": "Show me top 10 accounts by revenue"}'

# Test semantic search
gcloud functions call semantic-search --gen2 --region=us-central1 --project=$env:GCP_PROJECT_ID --data='{"query": "budget discussions", "type": "accounts", "limit": 10}'
```

### Verify BigQuery Data

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

---

## 🛠️ Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

Common issues:
- Permission denied errors
- Secret not found errors
- Function deployment failures
- Entry point mismatches
- Memory limit exceeded
- API not enabled errors

---

## 📊 Cost Estimation

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

## 🔐 Security Best Practices

1. ✅ **Never commit secrets** to git
2. ✅ **Use Secret Manager** for all credentials
3. ✅ **Rotate API keys** regularly
4. ✅ **Use least-privilege** IAM roles
5. ✅ **Enable audit logging** for sensitive operations
6. ✅ **Review IAM policies** regularly
7. ✅ **Use service accounts** instead of user accounts for functions
8. ✅ **Enable VPC** if handling sensitive data

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review Cloud Functions logs
3. Check BigQuery for data issues
4. Verify IAM permissions

---

## 📚 Additional Documentation

- [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md) - Detailed deployment guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and fixes
- [CLIENT_DEPLOYMENT_CHECKLIST.md](CLIENT_DEPLOYMENT_CHECKLIST.md) - Deployment checklist

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0
