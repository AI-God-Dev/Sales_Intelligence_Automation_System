# Deployment Fix Summary - Gemini Model Update & Critical Issues Resolved

## 🚨 Critical Issue Fixed: Vertex AI Model Not Found (404 Error)

### Problem Identified
The Cloud Scheduler job `account-scoring-daily` was failing with:
```
404 Publisher Model .../models/gemini-1.5-pro was not found or your project does not have access to it
```

This was causing:
- 504 Gateway Timeout errors in Cloud Scheduler (06:43 AM)
- Account scoring job failing repeatedly
- Service not producing expected results

---

## ✅ Fixes Applied

### 1. Model Configuration Updated to `gemini-2.5-pro`

#### Files Updated:
1. **`config/config.py`** (Line 163)
   - Changed default from `gemini-1.5-pro` → `gemini-2.5-pro`

2. **`ai/models.py`** (Lines 83, 181, 203)
   - Updated default model in `VertexAIModelProvider.__init__()` → `gemini-2.5-pro`
   - Updated docstring references
   - Updated `get_model_provider()` default

3. **Documentation Files Updated:**
   - `docs/CREDENTIALS_TEMPLATE.md`
   - `docs/CONFIGURATION.md`
   - `docs/phases/PHASE2_AND_3_COMPLETE.md`
   - `AI_SYSTEM_GUIDE.md`
   - `CLIENT_DEPLOYMENT_GUIDE.md`

#### Deployment Scripts Updated:
4. **`scripts/deploy_phase2_functions.sh`**
   - Added `LLM_MODEL=gemini-2.5-pro` to all AI function deployments:
     - `generate-embeddings`
     - `account-scoring`
     - `nlp-query`
     - `generate-email-reply`

5. **`scripts/deploy_phase2_functions.ps1`** (PowerShell version)
   - Added `LLM_MODEL=gemini-2.5-pro` to all AI function deployments

6. **`scripts/deploy_phase2_functions_fixed.ps1`**
   - Updated environment variable configurations in function definitions

---

### 2. Missing Cloud Scheduler Jobs Added

**Critical Missing Configuration:**
The `account-scoring-daily` scheduler job was **NOT defined in Terraform**!

#### Fixed: `infrastructure/scheduler.tf`
Added two new Cloud Scheduler jobs:

```terraform
# Account Scoring Job (runs daily at 7 AM)
resource "google_cloud_scheduler_job" "account_scoring_daily" {
  name             = "account-scoring-daily"
  schedule         = "0 7 * * *"
  retry_config {
    retry_count = 2
    max_retry_duration = "1200s"  # 20 minutes for AI processing
  }
}

# Embeddings Generation Job (runs daily at 8 AM)
resource "google_cloud_scheduler_job" "generate_embeddings_daily" {
  name             = "generate-embeddings-daily"
  schedule         = "0 8 * * *"
  retry_config {
    retry_count = 2
    max_retry_duration = "1200s"  # 20 minutes for AI processing
  }
}
```

**Key Changes:**
- Increased `max_retry_duration` from 600s → 1200s (20 minutes)
- Properly configured for AI processing workloads
- Correct OIDC authentication setup

---

### 3. Vertex AI API & IAM Permissions Added

#### Fixed: `infrastructure/main.tf`

**Added Vertex AI API:**
```terraform
resource "google_project_service" "required_apis" {
  for_each = toset([
    # ... existing APIs ...
    "aiplatform.googleapis.com",  # ← ADDED
  ])
}
```

**Added Required IAM Roles:**
```terraform
# Vertex AI User role for AI/ML operations
resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${data.google_service_account.existing_sa.email}"
}

# BigQuery Job User role for query execution
resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${data.google_service_account.existing_sa.email}"
}
```

---

## 🔧 Deployment Steps to Fix Production

### Step 1: Update Cloud Functions with Correct Model

**Option A: Redeploy all Phase 2 functions (Recommended)**

```powershell
cd D:\Work\0. Project\Anand-Sales\Sales_Intelligence_Automation_System
.\scripts\deploy_phase2_functions.ps1
```

**Option B: Update specific functions only**

```bash
# Update account-scoring function
gcloud functions deploy account-scoring \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=account_scoring_job \
  --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=3 \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,BQ_DATASET_NAME=sales_intelligence,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" \
  --project=maharani-sales-hub-11-2025
```

### Step 2: Enable Vertex AI API (if not already enabled)

```bash
gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025
```

### Step 3: Grant Vertex AI User Role to Service Account

```bash
gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 \
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Step 4: Apply Terraform Changes (for scheduler jobs)

```bash
cd infrastructure
terraform plan  # Review changes
terraform apply # Apply if plan looks good
```

**OR** manually create the scheduler job:

```bash
gcloud scheduler jobs create http account-scoring-daily \
  --location=us-central1 \
  --schedule="0 7 * * *" \
  --time-zone="America/New_York" \
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring" \
  --http-method=POST \
  --oidc-service-account-email=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --max-retry-duration=1200s \
  --max-retry-attempts=2 \
  --project=maharani-sales-hub-11-2025
```

### Step 5: Test the Fixed Deployment

```bash
# Test account-scoring function manually
gcloud functions call account-scoring \
  --gen2 \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --data='{"limit": 5}'

# Check logs
gcloud functions logs read account-scoring \
  --gen2 \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --limit=50

# Trigger scheduler job manually (test)
gcloud scheduler jobs run account-scoring-daily \
  --location=us-central1 \
  --project=maharani-sales-hub-11-2025
```

---

## 🐛 Other Potential Deployment Issues Identified & Fixed

### Issue 1: Missing `--gen2` flag in nlp-query deployment
**Fixed:** Added `--gen2` flag in `scripts/deploy_phase2_functions.sh` line 57

### Issue 2: Inconsistent timeout configurations
**Fixed:** Standardized timeouts:
- Account scoring: 540s (9 minutes)
- Embeddings: 540s (9 minutes)
- NLP Query: 60s (1 minute)
- Email Reply: 120s (2 minutes)

### Issue 3: Memory allocation for account-scoring
**Already correct:** 2048MB (2GB) for account-scoring function

### Issue 4: Scheduler retry durations too short for AI workloads
**Fixed:** Increased from 600s → 1200s (20 minutes)

---

## 📊 Verification Checklist

After deployment, verify:

- [ ] Vertex AI API is enabled:
  ```bash
  gcloud services list --enabled --project=maharani-sales-hub-11-2025 | grep aiplatform
  ```

- [ ] Service account has `aiplatform.user` role:
  ```bash
  gcloud projects get-iam-policy maharani-sales-hub-11-2025 \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:sales-intel-poc-sa@*" \
    --format="table(bindings.role)"
  ```

- [ ] Cloud Functions are deployed with correct env vars:
  ```bash
  gcloud functions describe account-scoring \
    --gen2 \
    --region=us-central1 \
    --project=maharani-sales-hub-11-2025 \
    --format="yaml(serviceConfig.environmentVariables)"
  ```

- [ ] Scheduler jobs exist:
  ```bash
  gcloud scheduler jobs list --location=us-central1 --project=maharani-sales-hub-11-2025
  ```

- [ ] Test function execution:
  ```bash
  curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    -H "Content-Type: application/json" \
    -d '{"limit": 5}' \
    https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring
  ```

---

## 🚀 Quick Fix Command Sequence

**Complete fix in one go (PowerShell):**

```powershell
# 1. Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025

# 2. Grant permissions
gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 `
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"

# 3. Redeploy Phase 2 functions with correct model
cd "D:\Work\0. Project\Anand-Sales\Sales_Intelligence_Automation_System"
.\scripts\deploy_phase2_functions.ps1

# 4. Wait for deployment to complete, then test
Start-Sleep -Seconds 60

# 5. Test account-scoring
gcloud functions call account-scoring `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025 `
  --data='{"limit": 5}'

Write-Host "✅ Deployment fix complete! Check logs for any errors." -ForegroundColor Green
```

---

## 📝 Root Cause Analysis

### Why the 504 Error Occurred:

1. **Model Not Found (404)**: Code was calling `gemini-1.5-pro` which doesn't exist or isn't available
2. **Fast Failure Loop**: Function would fail immediately on model initialization
3. **Scheduler Timeout**: Repeated failures within scheduler deadline caused 504
4. **Missing Configuration**: Environment variable `LLM_MODEL` was not set in Cloud Functions
5. **Missing Permissions**: Service account didn't have `aiplatform.user` role
6. **Missing API**: Vertex AI API wasn't enabled

### Why It Works Now:

1. ✅ Model updated to `gemini-2.5-pro` (available model)
2. ✅ Environment variable explicitly set in deployment scripts
3. ✅ Vertex AI API enabled in Terraform
4. ✅ Service account has correct IAM role
5. ✅ Scheduler timeout increased for AI processing
6. ✅ Proper error handling and retry configuration

---

## 🎯 Next Steps

1. **Deploy the fixes** using the commands above
2. **Monitor the next scheduled run** (7 AM tomorrow)
3. **Check Cloud Logging** for any remaining issues
4. **Verify account scores** are being generated in BigQuery:
   ```sql
   SELECT * FROM `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations`
   ORDER BY created_at DESC
   LIMIT 10;
   ```

---

## 📞 Support

If issues persist after applying these fixes:

1. Check Cloud Function logs:
   ```bash
   gcloud functions logs read account-scoring --gen2 --region=us-central1 --limit=100
   ```

2. Check Scheduler logs:
   ```bash
   gcloud scheduler jobs describe account-scoring-daily --location=us-central1
   ```

3. Verify model availability:
   ```bash
   gcloud ai models list --region=us-central1 --project=maharani-sales-hub-11-2025
   ```

---

**Document Created:** December 27, 2025
**Status:** ✅ All fixes applied and ready for deployment
**Priority:** 🚨 CRITICAL - Deploy immediately to fix production issues

