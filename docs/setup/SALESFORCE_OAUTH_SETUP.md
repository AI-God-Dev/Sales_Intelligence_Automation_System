# Salesforce OAuth 2.0 Setup Guide

## Overview

The system now supports **OAuth 2.0** for Salesforce authentication (more secure than username/password).

**Required Secrets:**
- `salesforce-client-id` - Connected App Consumer Key
- `salesforce-client-secret` - Connected App Consumer Secret  
- `salesforce-refresh-token` - OAuth refresh token
- `SALESFORCE_DOMAIN` environment variable - `test` for sandbox, `login` for production

---

## Step 1: Create Salesforce Connected App

1. **Login to Salesforce:**
   - Production: https://login.salesforce.com
   - Sandbox: https://test.salesforce.com

2. **Go to Setup:**
   - Click gear icon → Setup
   - Navigate to: **App Manager** → **New Connected App**

3. **Fill in Connected App Details:**
   - **Connected App Name:** Sales Intelligence System
   - **API Name:** Sales_Intelligence_System
   - **Contact Email:** your-email@example.com
   - **Enable OAuth Settings:** Check this box

4. **Configure OAuth Settings:**
   - **Callback URL:** `http://localhost:8080/callback` (can be any valid URL)
   - **Selected OAuth Scopes:**
     - ✅ "Access and manage your data (api)"
     - ✅ "Perform requests on your behalf at any time (refresh_token, offline_access)"
     - ✅ "Access your basic information (id, profile, email, address, phone)"
   - Click **Save**

5. **Get Credentials:**
   - After saving, click **Manage Consumer Details**
   - **Consumer Key** = Client ID (save this)
   - **Consumer Secret** = Client Secret (click to reveal, save this)

---

## Step 2: Get Refresh Token

**Option A: Using Salesforce Workbench (Easiest)**

1. Go to: https://workbench.developerforce.com/login.php
2. Login with Salesforce credentials
3. Go to: **Utilities** → **REST Explorer**
4. Click **Authorize** → Login → Allow
5. In the response, find `refresh_token` value
6. Save the refresh token

**Option B: Manual OAuth Flow**

1. Construct authorization URL:
   ```
   https://test.salesforce.com/services/oauth2/authorize?
     response_type=code&
     client_id=YOUR_CLIENT_ID&
     redirect_uri=http://localhost:8080/callback&
     scope=api refresh_token offline_access
   ```

2. Open URL in browser → Login → Allow
3. Copy `code` from redirect URL
4. Exchange code for refresh token:
   ```bash
   curl -X POST https://test.salesforce.com/services/oauth2/token \
     -d "grant_type=authorization_code" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=http://localhost:8080/callback" \
     -d "code=AUTHORIZATION_CODE"
   ```

5. Save `refresh_token` from response

---

## Step 3: Add Secrets to Secret Manager

**Using the script:**
```bash
bash scripts/add_salesforce_oauth_secrets.sh
```

**Or manually:**
```bash
PROJECT_ID="maharani-sales-hub-11-2025"

# Client ID
echo -n "YOUR_CLIENT_ID" | gcloud secrets versions add salesforce-client-id \
  --data-file=- --project=$PROJECT_ID

# Client Secret
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret \
  --data-file=- --project=$PROJECT_ID

# Refresh Token
echo -n "YOUR_REFRESH_TOKEN" | gcloud secrets versions add salesforce-refresh-token \
  --data-file=- --project=$PROJECT_ID
```

---

## Step 4: Deploy with Domain Setting

**Redeploy Salesforce sync with domain:**
```bash
bash scripts/redeploy_salesforce_sync.sh
```

Or set domain manually:
```bash
gcloud functions deploy salesforce-sync \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=salesforce_sync \
  --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=test" \
  --project=maharani-sales-hub-11-2025
```

**Domain values:**
- `SALESFORCE_DOMAIN=test` → Sandbox (`test.salesforce.com`)
- `SALESFORCE_DOMAIN=login` → Production (`login.salesforce.com`)

---

## How It Works

1. Function uses **refresh token** to get **access token**
2. Access token is used to authenticate API requests
3. No password or security token needed
4. More secure and follows OAuth 2.0 best practices

---

## Fallback to Username/Password

If OAuth secrets are not found, the system falls back to username/password authentication (legacy method).

---

## Troubleshooting

**Error: "Invalid client_id or client_secret"**
- Verify Client ID and Client Secret are correct
- Make sure Connected App is active

**Error: "Invalid refresh token"**
- Refresh token may have expired
- Get a new refresh token from OAuth flow

**Error: "INVALID_LOGIN"**
- Check domain setting (`test` for sandbox, `login` for production)
- Verify refresh token is for the correct environment

