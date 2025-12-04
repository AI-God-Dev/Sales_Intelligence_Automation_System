# Account Scoring - Complete Deployment & Integration Guide

This guide covers the complete setup from deployment to web app integration for the account-scoring feature.

## Overview

Account scoring is an AI-powered feature that:
- Analyzes account data (emails, calls, opportunities, activities)
- Generates priority scores, budget likelihood, and engagement scores
- Provides AI-generated recommendations and next actions
- Stores results in BigQuery `account_recommendations` table
- Runs daily at 7 AM via Cloud Scheduler (or manually via web app)

## Architecture

```
┌─────────────────┐
│  Cloud Scheduler│ (Daily 7 AM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ account-scoring │ (Cloud Function Gen2)
│   Cloud Run     │
└────────┬────────┘
         │
         ├──► BigQuery (account_recommendations table)
         │
         ▼
┌─────────────────┐
│   Web App       │ (Streamlit)
│  - Dashboard    │
│  - Account      │
│    Scoring Page │
└─────────────────┘
```

## Prerequisites

1. **GCP Project Setup**
   - Project: `maharani-sales-hub-11-2025`
   - Region: `us-central1`
   - Service Account: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`

2. **APIs Enabled**
   ```bash
   gcloud services enable cloudfunctions.googleapis.com --project=maharani-sales-hub-11-2025
   gcloud services enable run.googleapis.com --project=maharani-sales-hub-11-2025
   gcloud services enable aiplatform.googleapis.com --project=maharani-sales-hub-11-2025
   gcloud services enable bigquery.googleapis.com --project=maharani-sales-hub-11-2025
   ```

3. **Service Account Permissions**
   - BigQuery Data Editor
   - BigQuery Job User
   - Vertex AI User
   - Cloud Functions Invoker (for web app)

4. **BigQuery Table**
   - Table: `account_recommendations` must exist
   - Schema: See `bigquery/schemas/create_tables.sql`

## Deployment

### Option 1: Deploy All Phase 2 Functions (Recommended)

```powershell
# From project root
.\scripts\deploy_phase2_functions.ps1
```

This deploys all Phase 2 functions including account-scoring.

### Option 2: Deploy Account-Scoring Only

```powershell
$PROJECT_ID = "maharani-sales-hub-11-2025"
$REGION = "us-central1"
$SERVICE_ACCOUNT = "sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud functions deploy account-scoring `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=account_scoring_job `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=2048MB `
  --timeout=540s `
  --max-instances=3 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,LLM_PROVIDER=vertex_ai" `
  --project=$PROJECT_ID
```

### Grant Permissions

After deployment, grant invoker permission to the service account:

```powershell
gcloud functions add-iam-policy-binding account-scoring `
  --region=$REGION `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/cloudfunctions.invoker" `
  --project=$PROJECT_ID
```

For web app access (if using user authentication):

```powershell
# Grant to specific user (replace with actual user email)
gcloud functions add-iam-policy-binding account-scoring `
  --region=$REGION `
  --member="user:your-email@example.com" `
  --role="roles/run.invoker" `
  --project=$PROJECT_ID
```

## Cloud Scheduler Setup (Daily Execution)

Create a scheduled job to run account scoring daily at 7 AM:

```powershell
gcloud scheduler jobs create http account-scoring-daily `
  --location=$REGION `
  --schedule="0 7 * * *" `
  --uri="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring" `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience="https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring" `
  --project=$PROJECT_ID
```

## Testing

### Test via gcloud CLI

```powershell
gcloud functions call account-scoring `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025
```

Expected response:
```json
{
  "status": "success",
  "accounts_scored": 150,
  "completed_at": "2025-01-XX..."
}
```

### Test via Web App

1. Start the web app:
   ```powershell
   cd web_app
   streamlit run app.py
   ```

2. Navigate to **Dashboard** or **Account Scoring** page

3. Click **"Refresh Account Scores"** button

4. Verify:
   - Success message shows number of accounts scored
   - Top priority accounts table displays
   - Charts show score distributions

### Verify in BigQuery

```sql
SELECT 
  COUNT(*) as total_scores,
  AVG(priority_score) as avg_priority,
  MAX(score_date) as latest_score_date
FROM `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations`
WHERE score_date = CURRENT_DATE()
```

## Web App Integration

### Dashboard Page

The Dashboard page shows:
- Top 20 priority accounts (sorted by priority_score)
- Quick refresh button to trigger scoring
- Real-time display of scores from BigQuery

**Location**: `web_app/app.py` (lines ~1129-1204)

### Account Scoring Page

The Account Scoring page provides:
- Score distribution charts (Priority, Budget Likelihood, Engagement)
- Complete list of all account scores
- Detailed view with reasoning and recommended actions
- Filtering and sorting capabilities

**Location**: `web_app/app.py` (lines ~1206-1313)

### Function Call Implementation

The web app uses `call_function()` to invoke account-scoring:

```python
result = call_function("account-scoring", {})
```

This function:
1. Gets the Cloud Function URL
2. Authenticates using Application Default Credentials
3. Makes HTTP POST request with ID token
4. Handles errors and retries
5. Returns parsed JSON response

**Location**: `web_app/app.py` (lines ~578-800)

## Troubleshooting

### Function Not Deployed

**Error**: `Cloud Function 'account-scoring' is not deployed yet`

**Solution**: Deploy using the deployment script or manual command above.

### Authentication Errors

**Error**: `403 Forbidden` or `401 Unauthorized`

**Solutions**:
1. Ensure service account has `run.invoker` permission
2. For local dev, run `gcloud auth login`
3. Verify Application Default Credentials: `gcloud auth application-default login`

### 503 Service Unavailable

**Error**: `503 Service Unavailable`

**Solutions**:
1. Wait 1-2 minutes (cold start)
2. Check Cloud Run service status in GCP Console
3. Verify function is deployed and active
4. Check logs: `gcloud functions logs read account-scoring --gen2 --region=us-central1 --limit=50`

### No Scores in BigQuery

**Possible Causes**:
1. Function hasn't run yet
2. No accounts in `sf_accounts` table
3. Function failed silently

**Check**:
```sql
-- Check ETL runs
SELECT * 
FROM `maharani-sales-hub-11-2025.sales_intelligence.etl_runs`
WHERE source_system = 'account_scoring'
ORDER BY started_at DESC
LIMIT 5;
```

### LLM Errors

**Error**: `Vertex AI API error` or `Anthropic API error`

**Solutions**:
1. Verify Vertex AI API is enabled
2. Check service account has `Vertex AI User` role
3. Verify API quotas haven't been exceeded
4. Check LLM_PROVIDER environment variable

## Monitoring

### View Logs

```powershell
gcloud functions logs read account-scoring `
  --gen2 `
  --region=us-central1 `
  --limit=50 `
  --project=maharani-sales-hub-11-2025
```

### Check ETL Runs

```sql
SELECT 
  source_system,
  job_type,
  status,
  rows_processed,
  started_at,
  completed_at,
  TIMESTAMP_DIFF(completed_at, started_at, SECOND) as duration_seconds
FROM `maharani-sales-hub-11-2025.sales_intelligence.etl_runs`
WHERE source_system = 'account_scoring'
ORDER BY started_at DESC
LIMIT 10;
```

### Monitor Costs

Account scoring uses:
- **Vertex AI**: ~$0.50-2.00 per 100 accounts (daily)
- **BigQuery**: Minimal (reads and writes)
- **Cloud Run**: Based on execution time and memory

## File Structure

```
intelligence/scoring/
├── __init__.py
├── main.py                    # Cloud Function entry point
├── account_scorer.py          # Core scoring logic
└── requirements.txt           # Dependencies

web_app/
└── app.py                     # Web app with account scoring UI

scripts/
└── deploy_phase2_functions.ps1  # Deployment script
```

## Key Components

### 1. Entry Point (`intelligence/scoring/main.py`)

- Function: `account_scoring_job(request)`
- Decorator: `@functions_framework.http`
- Returns: JSON with status and accounts_scored count

### 2. Account Scorer (`intelligence/scoring/account_scorer.py`)

- Class: `AccountScorer`
- Method: `score_all_accounts()` - Processes all accounts
- Method: `score_account(account_id)` - Scores single account
- Uses LLM to generate scores and recommendations

### 3. Web App Integration (`web_app/app.py`)

- Function: `call_function()` - Invokes Cloud Function
- Dashboard: Displays top priority accounts
- Account Scoring Page: Full scoring interface with charts

## Next Steps After Deployment

1. ✅ Verify deployment: Test function manually
2. ✅ Set up Cloud Scheduler: Daily execution at 7 AM
3. ✅ Test web app: Verify UI displays scores correctly
4. ✅ Monitor first run: Check logs and BigQuery results
5. ✅ Review scores: Validate AI recommendations make sense
6. ✅ Adjust scoring: Fine-tune LLM prompts if needed

## Support

For issues:
1. Check logs: `gcloud functions logs read account-scoring --gen2 --region=us-central1`
2. Verify permissions: Service account roles
3. Test manually: Use gcloud CLI
4. Check BigQuery: Verify data exists

---

**Status**: ✅ Complete - Ready for production use

