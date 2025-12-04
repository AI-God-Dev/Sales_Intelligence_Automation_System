# Natural Language Query - Authentication Fix

## Issue

When trying to use the Natural Language Query feature, you're getting this error:

```
Error: Could not authenticate with Cloud Run service. Primary method failed: Neither metadata server or valid service account credentials are found.
```

## Root Cause

The error occurs because:
1. **Application Default Credentials (ADC) are not set up** for ID token generation
2. The `nlp-query` function may not be deployed yet

## Solution

### Step 1: Set Up Application Default Credentials

Run this command in your terminal:

```powershell
gcloud auth application-default login
```

This will:
- Open a browser window for authentication
- Set up Application Default Credentials for local development
- Allow the web app to authenticate with Cloud Functions

### Step 2: Verify Function is Deployed

Check if `nlp-query` function is deployed:

```powershell
gcloud run services describe nlp-query --region=us-central1 --project=maharani-sales-hub-11-2025
```

If it's not deployed, ask Anand to deploy it:

```powershell
.\scripts\deploy_phase2_functions.ps1
```

### Step 3: Test the Function

After setting up ADC, try the Natural Language Query again in the web app.

## Alternative: Use gcloud Directly

If the web app still has issues, you can test the function directly:

```powershell
gcloud functions call nlp-query `
  --gen2 `
  --region=us-central1 `
  --project=maharani-sales-hub-11-2025 `
  --data='{"query": "Which accounts are discussing budget for 2026?"}'
```

## What I've Fixed

I've improved the error handling in the web app to:
1. ✅ Provide clearer error messages
2. ✅ Show specific instructions for fixing authentication
3. ✅ Detect if function is not deployed
4. ✅ Provide helpful suggestions based on error type

## After Fixing

Once you run `gcloud auth application-default login`:
1. Refresh the web app page
2. Try the Natural Language Query again
3. It should work now!

## If It Still Doesn't Work

1. **Check gcloud is installed and logged in**:
   ```powershell
   gcloud auth list
   ```

2. **Verify project is set**:
   ```powershell
   gcloud config get-value project
   ```
   Should show: `maharani-sales-hub-11-2025`

3. **Check function exists**:
   ```powershell
   gcloud run services list --region=us-central1 --project=maharani-sales-hub-11-2025
   ```

4. **Contact Anand** if the function needs to be deployed or if you need permissions

---

**Quick Fix Command**:
```powershell
gcloud auth application-default login
```

Then refresh the web app and try again!

