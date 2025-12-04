# Testing Account Scoring with Real Data

## Current Status

### ✅ Code Changes
- All code changes committed and pushed
- Enhanced error handling and edge cases
- Production-ready code

### ⚠️ Deployment Issue
- **Current Memory**: 512MB (insufficient)
- **Required Memory**: 2048MB (as per deployment script)
- **Error**: Function crashes with "Memory limit exceeded" (using 543-711 MiB)

### 🔧 Solution Required

The function needs to be redeployed with increased memory. However, there's a permission issue:

```
ERROR: Caller is missing permission 'iam.serviceaccounts.actAs' on service account
```

**Action Required**: Ask Anand to either:
1. Grant `roles/iam.serviceAccountUser` permission, OR
2. Redeploy the function with 2048MB memory using the deployment script

## Testing Steps (After Memory Fix)

### 1. Verify Deployment
```powershell
gcloud functions describe account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --format="value(serviceConfig.availableMemory)"
```
Should show: `2048M`

### 2. Test Function Call
```powershell
gcloud functions call account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025
```

Expected response:
```json
{
  "status": "success",
  "accounts_scored": <number>,
  "completed_at": "2025-..."
}
```

### 3. Check BigQuery Results
```sql
SELECT 
    COUNT(*) as total_scores,
    AVG(priority_score) as avg_priority,
    MAX(score_date) as latest_score_date
FROM `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations`
WHERE score_date = CURRENT_DATE()
```

### 4. Test in Web App
1. Start web app: `streamlit run web_app/app.py`
2. Navigate to Dashboard or Account Scoring page
3. Click "🔄 Refresh Account Scores"
4. Verify scores display correctly

### 5. Check Logs
```powershell
gcloud functions logs read account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --limit=50
```

## Current Memory Issue Details

**Logs show**:
```
Memory limit of 488 MiB exceeded with 543 MiB used
Memory limit of 488 MiB exceeded with 711 MiB used
```

**Root Cause**: 
- Function is processing accounts but running out of memory
- Current allocation: 512MB (default)
- Required: 2048MB (as specified in deployment script)

**Why it needs more memory**:
- LLM API calls (Vertex AI)
- BigQuery query results
- Multiple accounts processed
- Response caching

## Next Steps

1. **Immediate**: Contact Anand to increase memory allocation to 2048MB
2. **After fix**: Run test steps above
3. **Verify**: Check scores in BigQuery and web app

## Deployment Command (For Anand)

```powershell
gcloud functions deploy account-scoring `
  --gen2 `
  --runtime=python311 `
  --region=us-central1 `
  --source=. `
  --entry-point=account_scoring_job `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com `
  --memory=2048MB `
  --timeout=540s `
  --max-instances=3 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" `
  --project=maharani-sales-hub-11-2025
```

Or use the deployment script:
```powershell
.\scripts\deploy_phase2_functions.ps1
```

