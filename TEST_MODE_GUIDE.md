# Account Scoring Test Mode Guide

## ✅ New Feature: Test Mode

I've added a **Test Mode** feature that allows you to test account scoring with just **10 accounts** instead of all 8,793 accounts. This helps:

- ✅ Test functionality quickly
- ✅ Avoid memory issues during testing
- ✅ Verify the system works before full deployment
- ✅ Reduce costs during testing

## 🚀 How to Use Test Mode

### Option 1: Web App (Recommended)

1. **Start the web app**:
   ```powershell
   cd web_app
   streamlit run app.py
   ```

2. **Navigate to Account Scoring page** (or Dashboard)

3. **Enable Test Mode**:
   - Check the **"🧪 Test Mode (10 accounts)"** checkbox
   - This will limit scoring to only 10 accounts

4. **Click "🔄 Refresh Account Scores"**

5. **Wait for results** (should take ~30-60 seconds instead of 5-9 minutes)

### Option 2: Direct API Call

```powershell
# Test with 10 accounts
gcloud functions call account-scoring `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025 `
  --data='{"limit": 10}'
```

Or using curl (after getting auth token):
```bash
curl -X POST \
  https://account-scoring-z455yfejea-uc.a.run.app \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

## 📋 Testing Steps

### Step 1: Deploy Updated Code

**Note**: The function needs to be redeployed with the new code that supports the `limit` parameter.

**Contact Anand** to redeploy:
```powershell
gcloud functions deploy account-scoring `
  --gen2 --runtime=python311 --region=us-central1 `
  --source=. --entry-point=account_scoring_job `
  --trigger-http --no-allow-unauthenticated `
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com `
  --memory=2048MB --timeout=540s `
  --max-instances=3 --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,LLM_PROVIDER=vertex_ai" `
  --project=maharani-sales-hub-11-2025
```

### Step 2: Test with 10 Accounts

1. Open web app
2. Enable Test Mode checkbox
3. Click "Refresh Account Scores"
4. Wait ~30-60 seconds

**Expected Result**:
```json
{
  "status": "success",
  "accounts_scored": 10,
  "completed_at": "2025-..."
}
```

### Step 3: Verify Results in BigQuery

```sql
SELECT 
    COUNT(*) as total_scores,
    AVG(priority_score) as avg_priority,
    MAX(score_date) as latest_score_date
FROM `maharani-sales-hub-11-2025.sales_intelligence.account_recommendations`
WHERE score_date = CURRENT_DATE()
ORDER BY priority_score DESC
LIMIT 10
```

**Expected**: 10 rows with scores

### Step 4: Verify in Web App

- Check Dashboard: Should show top 10 accounts
- Check Account Scoring page: Should show 10 accounts with scores
- Charts should display data

### Step 5: Test Full Run (Optional)

Once test mode works, you can run full scoring:
- **Uncheck** Test Mode checkbox
- Click "Refresh Account Scores"
- This will process all 8,793 accounts (~5-9 minutes)

## 🎯 Benefits of Test Mode

1. **Fast Testing**: 30-60 seconds vs 5-9 minutes
2. **Lower Memory**: Only processes 10 accounts
3. **Cost Effective**: ~$0.05-0.20 vs $44-176
4. **Quick Validation**: Verify system works before full run
5. **Debugging**: Easier to debug with fewer accounts

## 📊 Comparison

| Mode | Accounts | Time | Memory | Cost |
|------|----------|------|--------|------|
| **Test Mode** | 10 | ~30-60s | Low | ~$0.05-0.20 |
| **Full Mode** | 8,793 | ~5-9 min | High | ~$44-176 |

## 🔧 Technical Details

### Request Format

```json
{
  "limit": 10  // Optional: number of accounts to score
}
```

If `limit` is not provided or is 0/null, all accounts are scored.

### Code Changes

- `score_all_accounts(limit=None)`: Added optional limit parameter
- `account_scoring_job(request)`: Parses limit from request body
- Web app: Added Test Mode checkbox

## ⚠️ Current Status

- ✅ Code committed and pushed
- ⏳ **Waiting for deployment** with new code
- ⏳ **Waiting for memory increase** to 2048MB

## 🎉 Next Steps

1. **Deploy updated code** (with limit support)
2. **Increase memory** to 2048MB
3. **Test with 10 accounts** using Test Mode
4. **Verify results** in BigQuery and web app
5. **Run full scoring** once test passes

---

**Status**: ✅ Code ready, ⏳ Waiting for deployment

