# Deployment Guide

Complete guide for deploying the Sales Intelligence Automation System to Google Cloud Platform.

## Prerequisites

### Required Software
- Google Cloud SDK (`gcloud`) - [Install Guide](https://cloud.google.com/sdk/docs/install)
- Python 3.11+ - [Download](https://www.python.org/downloads/)
- PowerShell 5.1+ (Windows) or Bash (Linux/Mac)

### Required Access
- GCP project with billing enabled (Owner/Editor role)
- Google Workspace Admin access (for Gmail integration)
- Salesforce Admin access
- Dialpad Admin access
- HubSpot Admin access

### Verify Installation

```bash
gcloud --version
python --version  # Should be 3.11+
gcloud auth login
gcloud auth application-default login
```

---

## Quick Start (4 Steps)

```bash
# 1. Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# 2. Setup service account and APIs
./scripts/setup/setup_service_account.ps1

# 3. Create BigQuery dataset and tables
./scripts/setup/create_bigquery.ps1

# 4. Deploy all Cloud Functions
./scripts/deploy/deploy_all.ps1
```

---

## Detailed Steps

### Step 1: GCP Project Setup

```bash
# Set project
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  cloudscheduler.googleapis.com
```

### Step 2: Service Account Setup

```bash
# Create service account
gcloud iam service-accounts create sales-intelligence-sa \
  --display-name="Sales Intelligence Service Account"

# Grant required roles
SERVICE_ACCOUNT="sales-intelligence-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com"

for role in \
  roles/bigquery.dataEditor \
  roles/bigquery.jobUser \
  roles/secretmanager.secretAccessor \
  roles/aiplatform.user \
  roles/cloudfunctions.invoker
do
  gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="$role"
done
```

### Step 3: BigQuery Setup

```bash
# Create dataset
bq mk --dataset \
  --location=us-central1 \
  --description="Sales Intelligence data warehouse" \
  $GCP_PROJECT_ID:sales_intelligence

# Create tables (update project ID in SQL file first)
bq query --use_legacy_sql=false < bigquery/schemas/create_tables.sql
```

### Step 4: Secret Manager Setup

```bash
# Create secrets
for secret in \
  salesforce-client-id \
  salesforce-client-secret \
  salesforce-username \
  salesforce-password \
  salesforce-security-token \
  dialpad-api-key \
  hubspot-api-key
do
  gcloud secrets create $secret
done

# Add secret values (replace with actual values)
echo -n "YOUR_VALUE" | gcloud secrets versions add salesforce-client-id --data-file=-
# Repeat for each secret...

# Grant access to service account
for secret in salesforce-client-id salesforce-client-secret dialpad-api-key hubspot-api-key; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Step 5: Deploy Cloud Functions

```bash
# Deploy all functions
./scripts/deploy/deploy_all.ps1

# Or deploy individually
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=gmail_sync \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID"
```

### Step 6: Cloud Scheduler Setup

```bash
# Get function URLs
SCORING_URL=$(gcloud functions describe account-scoring --gen2 --region=$GCP_REGION --format="value(serviceConfig.uri)")

# Create scheduler job
gcloud scheduler jobs create http account-scoring-daily \
  --location=$GCP_REGION \
  --schedule="0 7 * * *" \
  --uri=$SCORING_URL \
  --http-method=POST \
  --oidc-service-account-email=$SERVICE_ACCOUNT \
  --oidc-token-audience=$SCORING_URL
```

### Step 7: Web Application Deployment

```bash
# Deploy to Cloud Run
cd web_app
gcloud run deploy sales-intelligence-web \
  --source . \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID"

# Or run locally
pip install -r requirements.txt
streamlit run app.py
```

---

## Verification

```bash
# List deployed functions
gcloud functions list --gen2 --region=$GCP_REGION

# Test a function
gcloud functions call gmail-sync --gen2 --region=$GCP_REGION

# Check BigQuery data
bq query --use_legacy_sql=false "
SELECT COUNT(*) FROM \`$GCP_PROJECT_ID.sales_intelligence.sf_accounts\`
"
```

---

## Post-Deployment Checklist

- [ ] All Cloud Functions deployed successfully
- [ ] Web application accessible
- [ ] Cloud Scheduler jobs created
- [ ] Data syncing from all sources
- [ ] Account scoring generating results
- [ ] Monitoring and logging working

---

## Cost Estimation

| Service | Estimated Monthly Cost |
|---------|----------------------|
| Cloud Functions | $10-50 |
| BigQuery | $5-20 (1 TB free) |
| Vertex AI | $20-100 |
| Cloud Run | $5-20 |
| Secret Manager | $1 |
| Cloud Scheduler | $1 |

**Total: $50-200/month** (depending on usage)

---

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Environment and secrets setup
- [Troubleshooting](../operations/TROUBLESHOOTING.md) - Common issues
- [Operations Runbook](../operations/RUNBOOK.md) - Day-to-day operations

