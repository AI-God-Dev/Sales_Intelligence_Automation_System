# Account Scoring Testing Status

## ✅ Code Status
- **Committed**: Yes (commit bc01e52)
- **Pushed**: Yes
- **Code Quality**: Production-ready with comprehensive error handling

## 📊 Data Status
- **Total Accounts**: 8,793 accounts available for scoring
- **Existing Scores**: Checking...

## ⚠️ Current Issue: Memory Limit

### Problem
The function is currently deployed with **512MB memory** but needs **2048MB** to process all accounts.

**Error from logs**:
```
Memory limit of 488 MiB exceeded with 543 MiB used
Memory limit of 488 MiB exceeded with 711 MiB used
```

### Why More Memory is Needed
- Processing 8,793 accounts
- LLM API calls (Vertex AI) for each account
- BigQuery query results cached in memory
- Response processing and JSON parsing

### Solution
The function needs to be redeployed with **2048MB memory** as specified in the deployment script.

## 🔧 Action Required

**Contact Anand** to redeploy with increased memory:

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

## 📋 Testing Plan (After Memory Fix)

### Step 1: Verify Deployment
```powershell
gcloud functions describe account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --format="value(serviceConfig.availableMemory)"
```
**Expected**: `2048M`

### Step 2: Test Function
```powershell
gcloud functions call account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025
```
**Expected**: 
```json
{
  "status": "success",
  "accounts_scored": 8793,
  "completed_at": "2025-..."
}
```

**Note**: This will take several minutes (9 minutes timeout) to process all 8,793 accounts.

### Step 3: Verify Results in BigQuery
```sql
SELECT 
    COUNT(*) as total_scores,
    COUNT(DISTINCT account_id) as unique_accounts,
    AVG(priority_score) as avg_priority,
    AVG(budget_likelihood) as avg_budget,
    AVG(engagement_score) as avg_engagement,
    MAX(score_date) as latest_score_date
FROM `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations`
WHERE score_date = CURRENT_DATE()
```

### Step 4: Test Web App
1. Start web app:
   ```powershell
   cd web_app
   streamlit run app.py
   ```

2. Navigate to **Dashboard** or **Account Scoring** page

3. Click **"🔄 Refresh Account Scores"** button

4. Verify:
   - Success message shows number of accounts scored
   - Top priority accounts table displays
   - Charts show score distributions
   - All account scores are visible

### Step 5: Check Logs
```powershell
gcloud functions logs read account-scoring --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --limit=50
```

**Look for**:
- ✅ "Starting daily account scoring job"
- ✅ "Scoring X accounts"
- ✅ "Processed X/Y accounts"
- ✅ "Completed scoring X accounts"
- ❌ No memory errors
- ❌ No LLM errors

## 🎯 Expected Results

### BigQuery Table
- **Rows**: ~8,793 (one per account)
- **Columns**: 
  - recommendation_id
  - account_id
  - score_date (today's date)
  - priority_score (0-100)
  - budget_likelihood (0-100)
  - engagement_score (0-100)
  - reasoning (text)
  - recommended_action (text)
  - key_signals (array)
  - last_interaction_date
  - created_at

### Web App Display
- **Dashboard**: Top 20 priority accounts
- **Account Scoring Page**: 
  - Score distribution charts
  - Budget likelihood chart
  - Complete list of all accounts with scores

## ⏱️ Estimated Time

- **Function Execution**: ~5-9 minutes (for 8,793 accounts)
- **LLM Calls**: ~1-2 seconds per account
- **Total Processing**: ~2.5-4.5 hours if processed sequentially
- **With Chunking**: ~5-9 minutes (parallel processing)

## 💰 Cost Estimate

- **Vertex AI**: ~$0.50-2.00 per 100 accounts = ~$44-176 for 8,793 accounts
- **BigQuery**: Minimal (reads and writes)
- **Cloud Run**: Based on execution time (~9 minutes)

## 📝 Notes

1. The function processes accounts in chunks of 50 to optimize memory
2. Individual account failures won't stop the batch
3. Progress is logged every 5 accounts
4. Results are inserted immediately to free memory
5. Garbage collection runs every 5 accounts

## ✅ Success Criteria

- [ ] Function executes without memory errors
- [ ] All 8,793 accounts are scored
- [ ] Scores appear in BigQuery `account_recommendations` table
- [ ] Web app displays scores correctly
- [ ] Charts render properly
- [ ] No errors in logs

---

**Status**: ⏳ Waiting for memory allocation increase
**Next Step**: Contact Anand to redeploy with 2048MB memory

