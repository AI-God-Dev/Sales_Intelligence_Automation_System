# Refined Deployment Guide - All Functions

## ✅ Pre-Deployment Checklist

### 1. Verify Prerequisites
```powershell
# Check gcloud is installed and configured
gcloud --version
gcloud config get-value project
gcloud auth list

# Should show: maharani-sales-hub-11-2025
```

### 2. Enable Required APIs
```powershell
$PROJECT_ID = "maharani-sales-hub-11-2025"

gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
```

### 3. Verify Service Account Permissions
```powershell
$SERVICE_ACCOUNT = "sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

# Check service account exists
gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID

# Verify roles (should have):
# - roles/bigquery.dataEditor
# - roles/bigquery.jobUser
# - roles/aiplatform.user
# - roles/secretmanager.secretAccessor
```

### 4. Verify Secrets Exist
```powershell
# Check required secrets
gcloud secrets list --project=$PROJECT_ID

# Required secrets:
# - hubspot-api-key
# - salesforce-username
# - salesforce-password
# - salesforce-security-token
# - dialpad-api-key
# - gmail-service-account-key (if using service account)
```

---

## 🚀 Deployment Steps

### Step 1: Deploy Phase 2 Functions

```powershell
# Navigate to project root
cd C:\Users\Administrator\Desktop\Projects\SALES

# Run deployment script
.\scripts\deploy_phase2_functions.ps1
```

**Expected Output**: All 8 functions should deploy successfully.

### Step 2: Verify Deployments

```powershell
# List all deployed functions
gcloud run services list --region=us-central1 --project=maharani-sales-hub-11-2025

# Check specific function
gcloud functions describe account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025
```

### Step 3: Test Functions

```powershell
# Test account-scoring (with limit for testing)
gcloud functions call account-scoring `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025 `
  --data='{"limit": 10}'

# Test nlp-query
gcloud functions call nlp-query `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025 `
  --data='{"query": "How many accounts do we have?"}'
```

---

## 📋 Complete Function List

### Phase 1: Data Ingestion (✅ Already Deployed)
1. ✅ gmail-sync
2. ✅ salesforce-sync
3. ✅ dialpad-sync
4. ✅ hubspot-sync
5. ✅ entity-resolution

### Phase 2: Intelligence & Automation (⏳ Deploy Now)
1. ⏳ **generate-embeddings** - Entry: `generate_embeddings`
2. ⏳ **account-scoring** - Entry: `account_scoring_job` (needs 2048MB)
3. ⏳ **nlp-query** - Entry: `nlp_query`
4. ⏳ **semantic-search** - Entry: `semantic_search`
5. ⏳ **create-leads** - Entry: `create_leads`
6. ⏳ **enroll-hubspot** - Entry: `enroll_hubspot`
7. ⏳ **get-hubspot-sequences** - Entry: `get_hubspot_sequences`
8. ⏳ **generate-email-reply** - Entry: `generate_email_reply`

---

## 🔧 Code Refinements Made

### 1. Fixed Deployment Script
- ✅ Added `nlp-query` to IAM binding list
- ✅ All entry points verified
- ✅ Memory allocations correct
- ✅ Environment variables set

### 2. Verified Requirements Files
- ✅ All functions have `functions-framework>=3.5.0`
- ✅ All functions have `google-cloud-bigquery>=3.13.0`
- ✅ LLM functions have `vertexai>=1.38.0`
- ✅ Added missing `functions-framework` to embeddings

### 3. Verified Entry Points
All entry points match between:
- `main.py` (root-level exports)
- Function `main.py` files
- Deployment script

### 4. Memory Allocations
- ✅ account-scoring: 2048MB (fixed from 512MB)
- ✅ generate-embeddings: 1024MB
- ✅ nlp-query: 1024MB
- ✅ semantic-search: 1024MB
- ✅ generate-email-reply: 1024MB
- ✅ Others: 512MB

---

## ⚠️ Common Issues & Solutions

### Issue 1: Permission Denied
**Error**: `Permission 'iam.serviceaccounts.actAs' denied`

**Solution**: Ask Anand to grant:
```powershell
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT `
  --member="user:YOUR_EMAIL@example.com" `
  --role="roles/iam.serviceAccountUser" `
  --project=$PROJECT_ID
```

### Issue 2: Memory Limit Exceeded
**Error**: `Memory limit exceeded`

**Solution**: Verify memory allocation in deployment script matches requirements.

### Issue 3: Function Not Found
**Error**: `Resource '.../functions/function-name' was not found`

**Solution**: Function needs to be deployed. Run deployment script.

### Issue 4: Import Errors
**Error**: `ModuleNotFoundError`

**Solution**: Ensure deploying from project root (`.`) to include shared modules.

---

## ✅ Post-Deployment Verification

### 1. Check Function Status
```powershell
$functions = @(
    "generate-embeddings",
    "account-scoring",
    "nlp-query",
    "semantic-search",
    "create-leads",
    "enroll-hubspot",
    "get-hubspot-sequences",
    "generate-email-reply"
)

foreach ($func in $functions) {
    Write-Host "Checking $func..." -ForegroundColor Yellow
    gcloud functions describe $func --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --format="value(state,serviceConfig.availableMemory)"
}
```

### 2. Test Each Function
```powershell
# Test embeddings
gcloud functions call generate-embeddings --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --data='{"type": "emails", "limit": 10}'

# Test account scoring (with limit)
gcloud functions call account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --data='{"limit": 10}'

# Test NLP query
gcloud functions call nlp-query --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --data='{"query": "Show me top 5 accounts"}'

# Test semantic search
gcloud functions call semantic-search --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --data='{"query": "budget discussions", "type": "accounts", "limit": 10}'
```

### 3. Check Logs
```powershell
# View recent logs for a function
gcloud functions logs read account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --limit=20
```

---

## 📊 Deployment Summary

| Function | Status | Memory | Entry Point | Notes |
|----------|--------|--------|-------------|-------|
| generate-embeddings | ⏳ | 1024MB | `generate_embeddings` | Ready |
| account-scoring | ⚠️ | 2048MB | `account_scoring_job` | Needs redeploy |
| nlp-query | ⏳ | 1024MB | `nlp_query` | Ready |
| semantic-search | ⏳ | 1024MB | `semantic_search` | Ready |
| create-leads | ⏳ | 512MB | `create_leads` | Ready |
| enroll-hubspot | ⏳ | 512MB | `enroll_hubspot` | Ready |
| get-hubspot-sequences | ⏳ | 512MB | `get_hubspot_sequences` | Ready |
| generate-email-reply | ⏳ | 1024MB | `generate_email_reply` | Ready |

---

## 🎯 Next Steps After Deployment

1. ✅ Verify all functions are deployed
2. ✅ Test each function individually
3. ✅ Set up Cloud Scheduler jobs
4. ✅ Test web app integration
5. ✅ Monitor logs for errors

---

**Status**: ✅ All code refined and ready for deployment
**Action**: Run `.\scripts\deploy_phase2_functions.ps1`

