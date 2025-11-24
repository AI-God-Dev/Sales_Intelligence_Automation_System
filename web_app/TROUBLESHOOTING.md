# Web Application Troubleshooting Guide

## Common Issues and Solutions

### 1. 404 Error: Cloud Function Not Found

**Error Message:**
```
404 Client Error: Not Found for url: https://us-central1-...cloudfunctions.net/account-scoring
```

**Cause:** The Cloud Function is not deployed yet.

**Solution:**
Deploy the Cloud Functions using the deployment scripts:

```bash
# Deploy all Phase 2 functions
./scripts/deploy_phase2_functions.sh

# Or deploy individually
gcloud functions deploy account-scoring \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./intelligence/scoring \
  --entry-point=account_scoring \
  --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

**For Windows PowerShell:**
```powershell
.\scripts\deploy_phase2_functions.ps1
```

### 2. BigQuery Client Not Available

**Error Message:**
```
BigQuery client not available. Account scores are generated daily at 7 AM.
```

**Cause:** GCP credentials are not configured or BigQuery client cannot be initialized.

**Solutions:**

1. **Set up Application Default Credentials:**
   ```bash
   gcloud auth application-default login
   ```

2. **Verify Service Account Access:**
   Ensure the service account has BigQuery access:
   ```bash
   gcloud projects add-iam-policy-binding maharani-sales-hub-11-2025 \
     --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataViewer"
   ```

3. **Check Environment Variables:**
   ```powershell
   $env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
   $env:GOOGLE_APPLICATION_CREDENTIALS = "path/to/service-account-key.json"
   ```

4. **Local Development:**
   The app will work in demo mode (showing 0s) until BigQuery is connected. This is normal for local development.

### 3. Connection Errors to Cloud Functions

**Error Message:**
```
Cannot connect to Cloud Function 'function-name'. It may not be deployed or the URL is incorrect.
```

**Solutions:**

1. **Check if function is deployed:**
   ```bash
   gcloud functions list --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025
   ```

2. **Verify the function URL:**
   The URL should be: `https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/{function-name}`

3. **Check function permissions:**
   Ensure the function allows unauthenticated invocations if needed:
   ```bash
   gcloud functions add-invoker-policy-binding account-scoring \
     --region=us-central1 \
     --member="allUsers" \
     --project=maharani-sales-hub-11-2025
   ```

### 4. Timeout Errors

**Error Message:**
```
Request to 'function-name' timed out. The function may be cold-starting or overloaded.
```

**Solutions:**

1. **Increase timeout in function deployment:**
   Add `--timeout=540s` to deployment command

2. **Check function logs:**
   ```bash
   gcloud functions logs read account-scoring --gen2 --region=us-central1 --limit=50
   ```

3. **Reduce request size** if querying large datasets

### 5. All Metrics Show 0

**Cause:** This is normal when:
- BigQuery client is not configured (demo mode)
- No data has been ingested yet
- Tables don't exist yet

**Solutions:**

1. **Ingest data first:**
   - Deploy Phase 1 Cloud Functions
   - Trigger data ingestion
   - Wait for data to be loaded

2. **Set up BigQuery:**
   - Create tables: `./scripts/setup_bigquery.sh`
   - Configure BigQuery client (see issue #2)

3. **Check data exists:**
   ```bash
   bq query --use_legacy_sql=false "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"
   ```

### 6. Port 8501 Already in Use

**Error:**
```
Port 8501 is already in use
```

**Solutions:**

1. **Use a different port:**
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **Kill the existing process:**
   ```powershell
   # Find the process
   netstat -ano | findstr :8501
   # Kill it (replace PID with actual process ID)
   taskkill /PID <PID> /F
   ```

### 7. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'module_name'
```

**Solution:**
Install missing dependencies:
```bash
pip install -r requirements.txt
pip install -r web_app/requirements.txt
```

## Development Mode vs Production

### Development Mode (Local)
- BigQuery may not be configured → Shows 0s or demo mode
- Cloud Functions may not be deployed → Shows deployment instructions
- This is **normal** and allows UI testing

### Production Mode (Deployed)
- All Cloud Functions deployed
- BigQuery fully configured
- Real data displayed
- Full functionality available

## Getting Help

1. Check deployment logs:
   ```bash
   gcloud functions logs read <function-name> --gen2 --region=us-central1
   ```

2. Check BigQuery access:
   ```bash
   bq ls sales_intelligence
   ```

3. Verify environment:
   ```bash
   echo $GCP_PROJECT_ID
   gcloud config get-value project
   ```

4. Check application logs in Cloud Run (if deployed)

## Quick Fixes Checklist

- [ ] Cloud Functions deployed? → Run deployment scripts
- [ ] BigQuery configured? → `gcloud auth application-default login`
- [ ] Environment variables set? → Check `GCP_PROJECT_ID`, `GCP_REGION`
- [ ] Dependencies installed? → `pip install -r requirements.txt`
- [ ] Port available? → Try different port or kill existing process
- [ ] Service account has permissions? → Check IAM roles

