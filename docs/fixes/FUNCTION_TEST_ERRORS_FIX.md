# Cloud Functions Test Errors - Fix Guide

## Issues Identified

1. **gmail-sync**: ReadTimeout (read timeout=300)
2. **salesforce-sync**: 500 Server Error
3. **dialpad-sync**: 500 Server Error (and 403 Forbidden)
4. **entity-resolution**: 500 Server Error
5. **hubspot-sync**: SUCCESS ✓

## Root Causes

### 1. Authentication Issues (403 Forbidden)
- Functions are deployed with `--no-allow-unauthenticated`
- Test script may not be properly authenticating
- Service account may lack invoker permissions

### 2. Function Crashes (500 Server Error)
- Functions may be crashing during execution
- Missing environment variables or secrets
- Import errors or initialization failures
- Runtime errors not properly caught

### 3. Timeout Issues (ReadTimeout)
- Functions taking longer than 300 seconds (gcloud default timeout)
- gmail-sync needs async invocation for long-running operations

## Fixes Applied

### 1. Improved Test Script (`scripts/test_functions.sh`)
- Better error detection and parsing
- Improved timeout handling
- Async invocation for gmail-sync
- Better log checking on failures
- Authentication error detection

### 2. Error Checking Script (`scripts/check_function_errors.sh`)
- Checks IAM permissions
- Verifies function deployment status
- Checks configuration (env vars, service account)
- Reviews error logs
- Attempts to fix IAM permissions automatically

## How to Fix

### Step 1: Check Function Health

Run the error checker script:

```bash
./scripts/check_function_errors.sh
```

Or check a specific function:

```bash
./scripts/check_function_errors.sh gmail-sync
```

### Step 2: Fix IAM Permissions

If authentication errors are found, grant invoker permissions:

```bash
PROJECT_ID="maharani-sales-hub-11-2025"
REGION="us-central1"
SERVICE_ACCOUNT="sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com"

for func in gmail-sync salesforce-sync dialpad-sync hubspot-sync entity-resolution; do
  gcloud functions add-iam-policy-binding $func \
    --gen2 \
    --region=$REGION \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudfunctions.invoker" \
    --project=$PROJECT_ID
done
```

### Step 3: Check Function Logs

View detailed logs for a failing function:

```bash
# View recent logs
gcloud functions logs read gmail-sync \
  --gen2 \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --limit=50

# View error logs only
gcloud logging read \
  "resource.type=cloud_function AND resource.labels.function_name=gmail-sync AND severity>=ERROR" \
  --project=maharani-sales-hub-11-2025 \
  --limit=20
```

### Step 4: Verify Function Configuration

Check if functions have required environment variables:

```bash
gcloud functions describe gmail-sync \
  --gen2 \
  --region=us-central1 \
  --project=maharani-sales-hub-11-2025 \
  --format="value(serviceConfig.environmentVariables)"
```

Required environment variables:
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `BQ_DATASET_NAME`

### Step 5: Test Functions Again

Run the improved test script:

```bash
./scripts/test_functions.sh
```

Or test a specific function:

```bash
./scripts/test_functions.sh gmail-sync
```

## Common Issues and Solutions

### Issue: 403 Forbidden
**Solution**: Grant invoker permission to service account (see Step 2)

### Issue: 500 Internal Server Error
**Possible causes**:
1. Missing secrets in Secret Manager
2. Missing environment variables
3. Import errors (check logs)
4. BigQuery table doesn't exist
5. API credentials invalid

**Solution**: Check logs to identify the specific error, then fix the root cause.

### Issue: ReadTimeout
**Solution**: 
- For gmail-sync: Already using async invocation
- For other functions: Increase timeout or optimize function performance
- Check if function is stuck in an infinite loop

### Issue: Function Not Found
**Solution**: Redeploy the function using the deployment scripts.

## Debugging Tips

1. **Check deployment status**:
   ```bash
   gcloud functions describe FUNCTION_NAME --gen2 --region=REGION --project=PROJECT_ID
   ```

2. **View real-time logs**:
   ```bash
   gcloud functions logs tail FUNCTION_NAME --gen2 --region=REGION --project=PROJECT_ID
   ```

3. **Test function locally** (if possible):
   ```bash
   functions-framework --target=FUNCTION_NAME --debug
   ```

4. **Check service account permissions**:
   ```bash
   gcloud projects get-iam-policy PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:SERVICE_ACCOUNT"
   ```

## Next Steps

1. Run `./scripts/check_function_errors.sh` to identify all issues
2. Fix IAM permissions if needed
3. Check logs for specific error messages
4. Fix configuration issues (env vars, secrets)
5. Re-test using `./scripts/test_functions.sh`

## Notes

- The test script now has better error handling and will show more detailed error messages
- The error checker script can automatically fix IAM permission issues
- All functions should return proper HTTP responses even on errors
- Check Cloud Run logs (not just Cloud Functions logs) for Gen2 functions

