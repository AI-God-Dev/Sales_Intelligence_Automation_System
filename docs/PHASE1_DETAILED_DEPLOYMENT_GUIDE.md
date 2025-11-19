# Phase 1: Detailed Deployment Guide - Complete Step-by-Step Instructions

**Purpose:** This guide provides comprehensive, detailed instructions for deploying Phase 1 of the Sales Intelligence System from scratch, enabling complete independent deployment without external assistance.

**Target Audience:** Client/New Developer deploying the system for the first time

**Estimated Time:** 3-6 hours (depending on data volume and familiarity with GCP)

---

## 📋 Table of Contents

1. [Prerequisites & Preparation](#prerequisites--preparation)
2. [Step 1: GCP Project Setup](#step-1-gcp-project-setup)
3. [Step 2: Secrets Configuration](#step-2-secrets-configuration)
4. [Step 3: Gmail Domain-Wide Delegation Setup](#step-3-gmail-domain-wide-delegation-setup)
5. [Step 4: Infrastructure Deployment](#step-4-infrastructure-deployment)
6. [Step 5: BigQuery Schema Creation](#step-5-bigquery-schema-creation)
7. [Step 6: Cloud Functions Deployment](#step-6-cloud-functions-deployment)
8. [Step 7: Cloud Scheduler Configuration](#step-7-cloud-scheduler-configuration)
9. [Step 8: Initial Data Sync](#step-8-initial-data-sync)
10. [Step 9: Entity Resolution Setup](#step-9-entity-resolution-setup)
11. [Step 10: Verification & Testing](#step-10-verification--testing)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Preparation

### Required Tools & Access

Before starting, ensure you have:

- [ ] **GCP Account** with billing enabled
- [ ] **GCP SDK (`gcloud`)** installed and configured
  - Installation: https://cloud.google.com/sdk/docs/install
  - Verify: `gcloud --version`
- [ ] **Python 3.11+** installed
  - Verify: `python --version` or `python3 --version`
- [ ] **Terraform >= 1.0** (optional, for infrastructure as code)
  - Installation: https://www.terraform.io/downloads
  - Verify: `terraform --version`
- [ ] **BigQuery CLI (`bq`)** (optional, but recommended)
  - Part of GCP SDK, verify: `bq version`
- [ ] **PowerShell** (Windows) or **Bash** (Linux/Mac) for running scripts

### Required Access & Credentials

You need admin access to:

- [ ] **Google Workspace Admin Console** (for Gmail Domain-Wide Delegation)
- [ ] **Salesforce Admin** (for API credentials and Connected App creation)
- [ ] **Dialpad Admin** (for API key generation)
- [ ] **HubSpot Admin** (for Private App creation)

### Required Credentials to Gather

Before starting, collect:

- [ ] Salesforce Connected App credentials (Client ID, Client Secret)
- [ ] Salesforce integration user credentials (Username, Password, Security Token)
- [ ] Dialpad API key
- [ ] HubSpot Private App access token
- [ ] Gmail OAuth Client credentials (will be created during setup)

### Project Information

**Default Configuration:**
- **GCP Project ID:** `maharani-sales-hub-11-2025`
- **Service Account:** `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`
- **Region:** `us-central1`
- **BigQuery Dataset:** `sales_intelligence`
- **Gmail Mailboxes:** `anand@maharaniweddings.com` (and 2 additional mailboxes)

> **Note:** Replace these values with your own if deploying to a different project.

---

## Step 1: GCP Project Setup

### 1.1 Authenticate with GCP

```powershell
# Windows PowerShell
gcloud auth login
gcloud auth application-default login

# Linux/Mac
gcloud auth login
gcloud auth application-default login
```

### 1.2 Set Your GCP Project

```powershell
# Set the project
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
gcloud config set project $env:GCP_PROJECT_ID

# Verify
gcloud config get-value project
```

### 1.3 Enable Required APIs

**Option A: Using PowerShell Script (Recommended)**

```powershell
.\enable_apis.ps1
```

**Option B: Manual Enable**

```powershell
# Enable all required APIs
gcloud services enable cloudfunctions.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable cloudscheduler.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable bigquery.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable run.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable iam.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable gmail.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$env:GCP_PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$env:GCP_PROJECT_ID

# Verify APIs are enabled
gcloud services list --enabled --project=$env:GCP_PROJECT_ID
```

### 1.4 Verify Billing

```powershell
# Check billing account
gcloud billing accounts list

# Link billing account if needed
gcloud billing projects link $env:GCP_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

**✅ Verification:** All APIs enabled, project set, billing active

---

## Step 2: Secrets Configuration

### 2.1 Create Secret Placeholders

**Option A: Using PowerShell Script**

```powershell
.\create_secrets.ps1
```

**Option B: Manual Creation**

```powershell
# Create all secret placeholders
$secrets = @(
    "salesforce-client-id",
    "salesforce-client-secret",
    "salesforce-username",
    "salesforce-password",
    "salesforce-security-token",
    "salesforce-refresh-token",
    "dialpad-api-key",
    "hubspot-api-key",
    "gmail-oauth-client-id",
    "gmail-oauth-client-secret",
    "service-account-key-json",
    "openai-api-key",
    "anthropic-api-key"
)

foreach ($secret in $secrets) {
    echo "" | gcloud secrets create $secret --data-file=- --project=$env:GCP_PROJECT_ID 2>$null
    Write-Host "Created secret: $secret"
}
```

### 2.2 Add Salesforce Credentials

**Get Salesforce Credentials:**

1. **Create Connected App in Salesforce:**
   - Go to Setup → App Manager → New Connected App
   - Name: `Sales Intelligence System`
   - Enable OAuth Settings
   - Callback URL: `https://oauth.pstmn.io/v1/callback`
   - OAuth Scopes: `api`, `refresh_token`, `offline_access`, `id`, `profile`, `email`
   - Save and copy Consumer Key (Client ID) and Consumer Secret

2. **Create Integration User:**
   - Username: `integration@yourdomain.com`
   - Profile: System Administrator (or custom with API access)
   - Reset security token and save it

**Store in Secret Manager:**

```powershell
# Salesforce Client ID
echo -n "YOUR_SALESFORCE_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=- --project=$env:GCP_PROJECT_ID

# Salesforce Client Secret
echo -n "YOUR_SALESFORCE_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=- --project=$env:GCP_PROJECT_ID

# Salesforce Username
echo -n "integration@yourdomain.com" | gcloud secrets versions add salesforce-username --data-file=- --project=$env:GCP_PROJECT_ID

# Salesforce Password
echo -n "YOUR_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=- --project=$env:GCP_PROJECT_ID

# Salesforce Security Token
echo -n "YOUR_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=- --project=$env:GCP_PROJECT_ID
```

> **📖 Detailed Guide:** See `docs/SALESFORCE_SANDBOX_SETUP.md` for sandbox configuration

### 2.3 Add Dialpad API Key

**Get Dialpad API Key:**

1. Log in to Dialpad Admin
2. Go to Settings → Integrations → API
3. Generate API key
4. Copy the key

**Store in Secret Manager:**

```powershell
echo -n "YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=- --project=$env:GCP_PROJECT_ID
```

### 2.4 Add HubSpot API Key

**Get HubSpot Private App Token:**

1. Log in to HubSpot
2. Go to Settings → Integrations → Private Apps
3. Create a private app: `Sales Intelligence System`
4. Configure scopes: `contacts.read`, `companies.read`, `sequences.read`, `sequences.write`
5. Copy the access token (format: `pat-[region]-[random-string]`)
6. **⚠️ Important:** Token is only shown once - save it immediately!

**Store in Secret Manager:**

```powershell
echo -n "YOUR_HUBSPOT_ACCESS_TOKEN" | gcloud secrets versions add hubspot-api-key --data-file=- --project=$env:GCP_PROJECT_ID
```

> **📖 Detailed Guide:** See `docs/HUBSPOT_SETUP.md` for complete setup

### 2.5 Grant Service Account Access to Secrets

```powershell
$serviceAccount = "sales-intel-poc-sa@$env:GCP_PROJECT_ID.iam.gserviceaccount.com"

$secrets = @(
    "salesforce-client-id",
    "salesforce-client-secret",
    "salesforce-username",
    "salesforce-password",
    "salesforce-security-token",
    "salesforce-refresh-token",
    "dialpad-api-key",
    "hubspot-api-key",
    "gmail-oauth-client-id",
    "gmail-oauth-client-secret",
    "service-account-key-json"
)

foreach ($secret in $secrets) {
    gcloud secrets add-iam-policy-binding $secret `
        --member="serviceAccount:$serviceAccount" `
        --role="roles/secretmanager.secretAccessor" `
        --project=$env:GCP_PROJECT_ID
    Write-Host "Granted access to: $secret"
}
```

**✅ Verification:**

```powershell
# List all secrets
gcloud secrets list --project=$env:GCP_PROJECT_ID

# Verify a secret exists (don't show value)
gcloud secrets describe salesforce-username --project=$env:GCP_PROJECT_ID
```

---

## Step 3: Gmail Domain-Wide Delegation Setup

This is a critical step for Gmail access. Follow carefully.

### 3.1 Create OAuth 2.0 Client ID

1. **Go to GCP Console:**
   - URL: https://console.cloud.google.com/apis/credentials?project=maharani-sales-hub-11-2025

2. **Create OAuth Client ID:**
   - Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
   - If prompted, configure OAuth consent screen first
   - Application type: **Web application**
   - Name: **Sales Intelligence Gmail Access**
   - Enable **"Domain-wide Delegation"** checkbox
   - Click **"CREATE"**

3. **Copy Client ID:**
   - Format: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
   - Copy the entire Client ID

4. **Store in Secret Manager:**

```powershell
echo -n "YOUR_CLIENT_ID.apps.googleusercontent.com" | gcloud secrets versions add gmail-oauth-client-id --data-file=- --project=$env:GCP_PROJECT_ID
```

### 3.2 Download Service Account Key

1. **Go to Service Accounts:**
   - URL: https://console.cloud.google.com/iam-admin/serviceaccounts?project=maharani-sales-hub-11-2025

2. **Select Service Account:**
   - Click: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`

3. **Create Key:**
   - Go to **"KEYS"** tab
   - Click **"ADD KEY"** → **"Create new key"**
   - Select **"JSON"** format
   - Click **"CREATE"**
   - File downloads automatically

4. **Store Key in Secret Manager:**

**Option A: Using PowerShell Script**

```powershell
.\store_service_account_key.ps1
```

**Option B: Manual Storage**

```powershell
# Replace with your actual file path
$keyPath = "C:\Users\YourName\Downloads\maharani-sales-hub-11-2025-xxxxx.json"
Get-Content $keyPath | gcloud secrets create service-account-key-json --data-file=- --project=$env:GCP_PROJECT_ID

# Grant service account access
gcloud secrets add-iam-policy-binding service-account-key-json `
    --member="serviceAccount:sales-intel-poc-sa@$env:GCP_PROJECT_ID.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor" `
    --project=$env:GCP_PROJECT_ID
```

> **⚠️ Important:** Save the JSON file securely - you can't download it again!

### 3.3 Configure Domain-Wide Delegation in Google Workspace

1. **Go to Google Workspace Admin Console:**
   - URL: https://admin.google.com/
   - Sign in as **super admin**

2. **Navigate to Domain-Wide Delegation:**
   - Go to **Security** → **API Controls** → **Domain-wide Delegation**
   - (Or search for "Domain-wide Delegation")

3. **Add New Client:**
   - Click **"Add new"**

4. **Enter Client Details:**
   - **Client ID:** Enter the numeric Client ID from Step 3.1
     - From: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
     - Use: `123456789-abcdefghijklmnop` (everything before `.apps.googleusercontent.com`)
   - **OAuth Scopes** (one per line):
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```

5. **Authorize:**
   - Click **"Authorize"**

6. **Verify:**
   - Client ID should appear in the list
   - Scopes should be correct

**✅ Verification:**

```powershell
# Check OAuth Client ID exists
gcloud secrets versions access latest --secret="gmail-oauth-client-id" --project=$env:GCP_PROJECT_ID

# Check service account key exists
gcloud secrets describe service-account-key-json --project=$env:GCP_PROJECT_ID
```

> **📖 Detailed Guide:** See `COMPLETE_SETUP_GUIDE.md` for complete Gmail DWD setup

---

## Step 4: Infrastructure Deployment

### 4.1 Option A: Using Terraform (Recommended)

**Navigate to Infrastructure Directory:**

```powershell
cd infrastructure
```

**Create terraform.tfvars:**

```powershell
# Create terraform.tfvars file
@"
project_id  = "maharani-sales-hub-11-2025"
region      = "us-central1"
environment = "prod"
dataset_id  = "sales_intelligence"
"@ | Out-File -FilePath terraform.tfvars -Encoding utf8
```

**Initialize and Apply:**

```powershell
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Apply infrastructure
terraform apply
# Type 'yes' when prompted
```

**Verify Outputs:**

```powershell
# View outputs
terraform output

# Verify BigQuery dataset
bq ls $env:GCP_PROJECT_ID:sales_intelligence
```

### 4.2 Option B: Manual Infrastructure Setup

**Create BigQuery Dataset:**

```powershell
bq mk --dataset --location=US $env:GCP_PROJECT_ID:sales_intelligence
```

**Create Service Account (if not exists):**

```powershell
# Create service account
gcloud iam service-accounts create sales-intel-poc-sa `
    --display-name="Sales Intelligence POC Service Account" `
    --project=$env:GCP_PROJECT_ID

# Grant required roles
$serviceAccount = "sales-intel-poc-sa@$env:GCP_PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/pubsub.publisher"
```

**Create Pub/Sub Topics:**

```powershell
# Error notification topic
gcloud pubsub topics create etl-errors --project=$env:GCP_PROJECT_ID

# Grant publish permission
gcloud pubsub topics add-iam-policy-binding etl-errors `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/pubsub.publisher" `
    --project=$env:GCP_PROJECT_ID
```

**✅ Verification:**

```powershell
# Verify dataset
bq ls $env:GCP_PROJECT_ID:sales_intelligence

# Verify service account
gcloud iam service-accounts describe $serviceAccount --project=$env:GCP_PROJECT_ID

# Verify Pub/Sub topic
gcloud pubsub topics list --project=$env:GCP_PROJECT_ID
```

---

## Step 5: BigQuery Schema Creation

### 5.1 Create Tables

**Option A: Using PowerShell Script**

```powershell
.\scripts\setup_bigquery.ps1
```

**Option B: Manual Creation**

```powershell
# Update project_id in SQL file
$sqlContent = Get-Content "bigquery\schemas\create_tables.sql" -Raw
$sqlContent = $sqlContent -replace '\{project_id\}', $env:GCP_PROJECT_ID
$sqlContent | Out-File -FilePath "create_tables_updated.sql" -Encoding utf8

# Create tables
bq query --use_legacy_sql=false --project_id=$env:GCP_PROJECT_ID < create_tables_updated.sql

# Clean up
Remove-Item create_tables_updated.sql
```

### 5.2 Verify Tables Created

```powershell
# List all tables
bq ls $env:GCP_PROJECT_ID:sales_intelligence

# Expected tables (13 total):
# 1. gmail_messages
# 2. gmail_participants
# 3. gmail_sync_state
# 4. sf_accounts
# 5. sf_contacts
# 6. sf_leads
# 7. sf_opportunities
# 8. sf_activities
# 9. dialpad_calls
# 10. hubspot_sequences
# 11. account_recommendations
# 12. etl_runs
# 13. manual_mappings

# Verify table structure
bq show $env:GCP_PROJECT_ID:sales_intelligence.gmail_messages
```

**✅ Verification:** All 13 tables exist with correct schemas

---

## Step 6: Cloud Functions Deployment

### 6.1 Important Deployment Notes

**⚠️ Critical:** Cloud Functions MUST be deployed from the project root directory to include shared modules (`utils`, `config`, `entity_resolution`).

**Entry Point Format:** `cloud_functions.{function_name}.main.{entry_point}`

### 6.2 Deploy All Functions

**Option A: Using PowerShell Script (Recommended)**

```powershell
# Make sure you're in project root
cd C:\Users\Administrator\Desktop\SALES

.\scripts\deploy_functions.ps1
```

**Option B: Manual Deployment**

```powershell
# Set variables
$projectId = $env:GCP_PROJECT_ID
$region = "us-central1"
$serviceAccount = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"

# Deploy Gmail Sync
gcloud functions deploy gmail-sync `
    --gen2 `
    --runtime=python311 `
    --region=$region `
    --source=. `
    --entry-point=cloud_functions.gmail_sync.main.gmail_sync `
    --trigger-http `
    --service-account=$serviceAccount `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10 `
    --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
    --project=$projectId

# Deploy Salesforce Sync
gcloud functions deploy salesforce-sync `
    --gen2 `
    --runtime=python311 `
    --region=$region `
    --source=. `
    --entry-point=cloud_functions.salesforce_sync.main.salesforce_sync `
    --trigger-http `
    --service-account=$serviceAccount `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10 `
    --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
    --project=$projectId

# Deploy Dialpad Sync
gcloud functions deploy dialpad-sync `
    --gen2 `
    --runtime=python311 `
    --region=$region `
    --source=. `
    --entry-point=cloud_functions.dialpad_sync.main.dialpad_sync `
    --trigger-http `
    --service-account=$serviceAccount `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10 `
    --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
    --project=$projectId

# Deploy HubSpot Sync
gcloud functions deploy hubspot-sync `
    --gen2 `
    --runtime=python311 `
    --region=$region `
    --source=. `
    --entry-point=cloud_functions.hubspot_sync.main.hubspot_sync `
    --trigger-http `
    --service-account=$serviceAccount `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10 `
    --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
    --project=$projectId

# Deploy Entity Resolution
gcloud functions deploy entity-resolution `
    --gen2 `
    --runtime=python311 `
    --region=$region `
    --source=. `
    --entry-point=cloud_functions.entity_resolution.main.entity_resolution `
    --trigger-http `
    --service-account=$serviceAccount `
    --memory=512MB `
    --timeout=540s `
    --max-instances=10 `
    --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
    --project=$projectId
```

### 6.3 Verify Functions Deployed

```powershell
# List all functions
gcloud functions list --gen2 --region=$region --project=$projectId

# Check function status
gcloud functions describe gmail-sync --gen2 --region=$region --project=$projectId --format="get(state,updateTime)"

# Get function URL
gcloud functions describe gmail-sync --gen2 --region=$region --project=$projectId --format="get(serviceConfig.uri)"
```

**✅ Verification:** All 5 functions deployed and in ACTIVE state

---

## Step 7: Cloud Scheduler Configuration

### 7.1 Create Scheduler Jobs

**Option A: Using PowerShell Script**

```powershell
.\scripts\create_scheduler_jobs.ps1
```

**Option B: Manual Creation**

```powershell
$projectId = $env:GCP_PROJECT_ID
$region = "us-central1"
$serviceAccount = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"

# Gmail Incremental Sync (every hour)
gcloud scheduler jobs create http gmail-incremental-sync `
    --location=$region `
    --schedule="0 * * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/gmail-sync" `
    --http-method=POST `
    --message-body='{"mailbox_email":"anand@maharaniweddings.com","sync_type":"incremental"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# Gmail Full Sync (daily at 2 AM)
gcloud scheduler jobs create http gmail-full-sync `
    --location=$region `
    --schedule="0 2 * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/gmail-sync" `
    --http-method=POST `
    --message-body='{"mailbox_email":"anand@maharaniweddings.com","sync_type":"full"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# Salesforce Incremental Sync (every 6 hours)
gcloud scheduler jobs create http salesforce-incremental-sync `
    --location=$region `
    --schedule="0 */6 * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/salesforce-sync" `
    --http-method=POST `
    --message-body='{"object_type":"Account","sync_type":"incremental"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# Salesforce Full Sync (weekly Sunday 3 AM)
gcloud scheduler jobs create http salesforce-full-sync `
    --location=$region `
    --schedule="0 3 * * 0" `
    --uri="https://$region-$projectId.cloudfunctions.net/salesforce-sync" `
    --http-method=POST `
    --message-body='{"object_type":"Account","sync_type":"full"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# Dialpad Sync (daily at 1 AM)
gcloud scheduler jobs create http dialpad-sync `
    --location=$region `
    --schedule="0 1 * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/dialpad-sync" `
    --http-method=POST `
    --message-body='{"sync_type":"incremental"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# HubSpot Sync (daily at 4 AM)
gcloud scheduler jobs create http hubspot-sync `
    --location=$region `
    --schedule="0 4 * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/hubspot-sync" `
    --http-method=POST `
    --message-body='{"sync_type":"incremental"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId

# Entity Resolution (every 4 hours)
gcloud scheduler jobs create http entity-resolution `
    --location=$region `
    --schedule="0 */4 * * *" `
    --uri="https://$region-$projectId.cloudfunctions.net/entity-resolution" `
    --http-method=POST `
    --message-body='{"sync_type":"incremental"}' `
    --oidc-service-account-email=$serviceAccount `
    --project=$projectId
```

### 7.2 Verify Scheduler Jobs

```powershell
# List all scheduler jobs
gcloud scheduler jobs list --location=$region --project=$projectId

# Test a job manually
gcloud scheduler jobs run gmail-incremental-sync --location=$region --project=$projectId
```

**✅ Verification:** All 7 scheduler jobs created and can be triggered manually

---

## Step 8: Initial Data Sync

### 8.1 Run Gmail Full Sync

```powershell
$projectId = $env:GCP_PROJECT_ID
$region = "us-central1"

# Get access token
$token = gcloud auth print-access-token

# Sync first mailbox
$body = @{
    mailbox_email = "anand@maharaniweddings.com"
    sync_type = "full"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$region-$projectId.cloudfunctions.net/gmail-sync" `
    -Method POST `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $body

# Repeat for other mailboxes
# $body.mailbox_email = "email2@maharaniweddings.com"
# ... (repeat for each mailbox)
```

### 8.2 Run Salesforce Full Sync

```powershell
# Sync all Salesforce objects
$objects = @("Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage")

foreach ($object in $objects) {
    $body = @{
        object_type = $object
        sync_type = "full"
    } | ConvertTo-Json

    Invoke-RestMethod -Uri "https://$region-$projectId.cloudfunctions.net/salesforce-sync" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $body

    Write-Host "Synced: $object"
    Start-Sleep -Seconds 5  # Rate limiting
}
```

### 8.3 Run Dialpad Sync

```powershell
$body = @{
    sync_type = "full"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$region-$projectId.cloudfunctions.net/dialpad-sync" `
    -Method POST `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $body
```

### 8.4 Run HubSpot Sync

```powershell
$body = @{
    sync_type = "full"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$region-$projectId.cloudfunctions.net/hubspot-sync" `
    -Method POST `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $body
```

### 8.5 Verify Data in BigQuery

```powershell
# Check Gmail messages
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT COUNT(*) as message_count FROM \`$projectId.sales_intelligence.gmail_messages\`"

# Check Salesforce accounts
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT COUNT(*) as account_count FROM \`$projectId.sales_intelligence.sf_accounts\`"

# Check ETL runs
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT function_name, status, COUNT(*) as run_count FROM \`$projectId.sales_intelligence.etl_runs\` GROUP BY function_name, status"
```

**✅ Verification:** Data appears in BigQuery tables, ETL runs show successful status

---

## Step 9: Entity Resolution Setup

### 9.1 Run Entity Resolution

```powershell
$body = @{
    sync_type = "full"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://$region-$projectId.cloudfunctions.net/entity-resolution" `
    -Method POST `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $body
```

### 9.2 Verify Entity Resolution Results

```powershell
# Check manual mappings
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT COUNT(*) as mapping_count FROM \`$projectId.sales_intelligence.manual_mappings\`"

# Check entity resolution ETL runs
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT * FROM \`$projectId.sales_intelligence.etl_runs\` WHERE function_name = 'entity-resolution' ORDER BY run_time DESC LIMIT 5"
```

**✅ Verification:** Entity resolution runs successfully, matches are created

---

## Step 10: Verification & Testing

### 10.1 Run Automated Tests

```powershell
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

**Expected:** 45 tests passing, 100% pass rate

### 10.2 Check Function Logs

```powershell
# Check Gmail sync logs
gcloud functions logs read gmail-sync --gen2 --region=$region --project=$projectId --limit=50

# Check for errors
gcloud functions logs read gmail-sync --gen2 --region=$region --project=$projectId --limit=100 | Select-String "ERROR"
```

### 10.3 Verify Cloud Scheduler Execution

```powershell
# Check scheduler job execution history
gcloud scheduler jobs describe gmail-incremental-sync --location=$region --project=$projectId

# Manually trigger a job
gcloud scheduler jobs run gmail-incremental-sync --location=$region --project=$projectId

# Check logs after trigger
Start-Sleep -Seconds 30
gcloud functions logs read gmail-sync --gen2 --region=$region --project=$projectId --limit=20
```

### 10.4 Verify Data Quality

```powershell
# Check data freshness
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT 
        'gmail_messages' as table_name,
        COUNT(*) as row_count,
        MAX(ingested_at) as latest_ingestion
    FROM \`$projectId.sales_intelligence.gmail_messages\`
    UNION ALL
    SELECT 
        'sf_accounts' as table_name,
        COUNT(*) as row_count,
        MAX(ingested_at) as latest_ingestion
    FROM \`$projectId.sales_intelligence.sf_accounts\`"

# Check ETL run success rate
bq query --use_legacy_sql=false --project_id=$projectId `
    "SELECT 
        function_name,
        status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY function_name), 2) as percentage
    FROM \`$projectId.sales_intelligence.etl_runs\`
    GROUP BY function_name, status
    ORDER BY function_name, status"
```

### 10.5 Final Checklist

- [ ] All 5 Cloud Functions deployed and active
- [ ] All 7 Cloud Scheduler jobs created
- [ ] All 13 BigQuery tables created
- [ ] Initial data sync completed
- [ ] Entity resolution running
- [ ] ETL runs showing successful status
- [ ] No critical errors in logs
- [ ] Service account has all required permissions
- [ ] All secrets stored and accessible

**✅ Verification:** System fully operational, data flowing, automation working

---

## Troubleshooting

### Common Issues

#### Issue: "Permission denied" when accessing secrets

**Solution:**
```powershell
# Verify service account has access
gcloud secrets get-iam-policy SECRET_NAME --project=$projectId

# Grant access
gcloud secrets add-iam-policy-binding SECRET_NAME `
    --member="serviceAccount:$serviceAccount" `
    --role="roles/secretmanager.secretAccessor" `
    --project=$projectId
```

#### Issue: "Function deployment failed" - missing modules

**Solution:**
- Ensure deployment is from project root: `--source=.`
- Verify entry point format: `cloud_functions.{module}.main.{function}`
- Check `.gcloudignore` doesn't exclude required files

#### Issue: "Gmail API 403 Forbidden"

**Solution:**
- Verify Domain-Wide Delegation is configured in Google Workspace Admin
- Check OAuth Client ID matches exactly (numeric part only)
- Ensure OAuth scopes are correct
- Verify service account key is stored correctly

#### Issue: "BigQuery table not found"

**Solution:**
```powershell
# Verify dataset exists
bq ls $projectId:sales_intelligence

# Recreate tables if needed
.\scripts\setup_bigquery.ps1
```

#### Issue: "Scheduler job not triggering"

**Solution:**
```powershell
# Check job status
gcloud scheduler jobs describe JOB_NAME --location=$region --project=$projectId

# Test manually
gcloud scheduler jobs run JOB_NAME --location=$region --project=$projectId

# Check service account permissions
gcloud projects get-iam-policy $projectId --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$serviceAccount"
```

### Getting Help

1. **Check Logs:**
   ```powershell
   gcloud functions logs read FUNCTION_NAME --gen2 --region=$region --project=$projectId --limit=100
   ```

2. **Review Documentation:**
   - `docs/TROUBLESHOOTING.md` - Common issues and solutions
   - `docs/PHASE1_HANDOFF.md` - Technical details
   - `COMPLETE_SETUP_GUIDE.md` - Gmail DWD setup

3. **Verify Configuration:**
   ```powershell
   # Check all secrets exist
   gcloud secrets list --project=$projectId
   
   # Check function configuration
   gcloud functions describe FUNCTION_NAME --gen2 --region=$region --project=$projectId
   ```

---

## Next Steps After Deployment

1. **Monitor System:**
   - Set up Cloud Monitoring alerts
   - Review ETL runs regularly
   - Check error notifications in Pub/Sub

2. **Optimize Performance:**
   - Adjust Cloud Scheduler frequencies if needed
   - Scale Cloud Function instances based on load
   - Optimize BigQuery queries

3. **Data Quality:**
   - Review entity resolution matches
   - Add manual mappings as needed
   - Monitor data freshness

4. **Phase 2 Preparation:**
   - Review Phase 2 requirements
   - Plan for embeddings and vector search
   - Prepare for AI features

---

## Summary

This guide provides complete step-by-step instructions for deploying Phase 1 of the Sales Intelligence System. Following these steps in order will result in a fully operational system that:

- ✅ Ingests data from Gmail, Salesforce, Dialpad, and HubSpot
- ✅ Stores data in BigQuery with proper schema
- ✅ Resolves entities automatically
- ✅ Runs on automated schedules
- ✅ Monitors and reports errors
- ✅ Is ready for Phase 2 enhancements

**Estimated Total Time:** 3-6 hours (depending on data volume)

**Status After Completion:** ✅ Phase 1 Production-Ready

---

**Last Updated:** December 2024  
**Version:** 1.0  
**Maintained By:** Sales Intelligence System Team

