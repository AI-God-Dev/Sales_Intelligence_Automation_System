# Cloud Run Authentication Issue

## Problem
The web app is getting a **401 Unauthorized** error when trying to call Cloud Run services (Gen2 Cloud Functions). This is because Cloud Run services require **identity tokens** with the correct audience (service URL), not access tokens.

## Root Cause
For Cloud Run services with `--no-allow-unauthenticated`, we need identity tokens. User credentials from Application Default Credentials (ADC) don't support generating identity tokens directly for Cloud Run services.

## Solution Options

### Option 1: Grant Service Account Impersonation Permission (Recommended)
Grant the user permission to impersonate the service account, which will allow generating identity tokens:

```bash
gcloud iam service-accounts add-iam-policy-binding sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --member='user:atajanbaratov360@gmail.com' \
  --role='roles/iam.serviceAccountTokenCreator' \
  --project=maharani-sales-hub-11-2025
```

This will allow the web app to use:
```bash
gcloud auth print-identity-token --impersonate-service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
```

### Option 2: Use Cloud Run Client Library
We could refactor the web app to use the `google-cloud-run` client library, which handles authentication automatically. However, this requires more code changes.

### Option 3: Allow Unauthenticated Access (Not Recommended)
Deploy functions with `--allow-unauthenticated`, but this is less secure and you mentioned you don't want this.

## Current Status
- ✅ `account-scoring` function has `run.invoker` permission granted
- ❌ Cannot generate identity tokens for Cloud Run services
- ❌ Getting 401 Unauthorized errors

## Next Steps
Please grant the `roles/iam.serviceAccountTokenCreator` role on the service account to `atajanbaratov360@gmail.com` so the web app can generate identity tokens for Cloud Run authentication.

## Testing
After granting the permission, the web app should be able to:
1. Generate identity tokens using service account impersonation
2. Successfully call Cloud Run services (Gen2 Cloud Functions)
3. Test all features with real data

