# Milestone 2 & 3 Completion Status

## Current Status

### ✅ Completed
1. **GCP Credentials**: Application default credentials set up
2. **Web App**: Running locally at http://localhost:8501

### ⚠️ Requires Admin Permissions
The following steps require **project owner/admin** permissions on the GCP project:

1. **Enable Vertex AI API**
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025
   ```

2. **Grant Vertex AI User Role to Service Account**
   ```bash
   gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 \
     --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. **Set Quota Project for ADC**
   ```bash
   gcloud auth application-default set-quota-project maharani-sales-hub-11-2025
   ```

### 🔧 Deployment Issues to Fix

The deployment script needs to be updated because:
- Functions are in subdirectories (`intelligence/scoring/main.py`)
- Need to deploy from project root with proper entry points
- Source path needs to point to project root, not individual function directories

## What Needs to Be Done

### Option 1: Admin Completes Setup (Recommended)
Have a project admin run:
1. Enable Vertex AI API
2. Grant Vertex AI User role
3. Then we can deploy functions

### Option 2: Manual Deployment
Deploy each function individually with correct source paths.

## Next Steps

1. **Get Admin Access** or have admin run the permission commands above
2. **Fix Deployment Script** to use correct source paths
3. **Deploy Phase 2 Functions**:
   - account-scoring
   - generate-embeddings
   - nlp-query
   - create-leads
   - enroll-hubspot
   - get-hubspot-sequences
   - generate-email-reply
   - semantic-search

4. **Create Cloud Scheduler Jobs**:
   - Daily account scoring (7 AM)
   - Daily embeddings generation (8 AM)

5. **Test Functions**:
   - Trigger account scoring manually
   - Verify embeddings generation
   - Test NLP query

6. **Verify Web App**:
   - Should now show account scores
   - BigQuery access should work
   - All features functional

## Current Web App Status

- ✅ Running locally
- ⚠️ BigQuery client not available (needs credentials/quota project)
- ⚠️ Account scores not available (functions not deployed)

## Commands for Admin

```bash
# 1. Enable Vertex AI
gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025

# 2. Grant Vertex AI User role
gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 \
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 3. Verify service account has BigQuery access
gcloud projects get-iam-policy maharani-sales-hub-11-2025 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

