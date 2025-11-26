# Salesforce OAuth Authentication Fix

## Current Status

✅ **Refresh Token**: Updated and correct  
✅ **Client ID (Consumer Key)**: Correct  
❌ **Client Secret (Consumer Secret)**: **INVALID** - doesn't match the Client ID

## The Problem

The OAuth authentication is failing with:
```
{"error":"invalid_client","error_description":"invalid client credentials"}
```

This means the **Consumer Secret** in Secret Manager doesn't match the **Consumer Key**.

## Solution

You need to get the correct Consumer Secret from Salesforce and update it in Secret Manager.

### Step 1: Get Consumer Secret from Salesforce

1. Log in to Salesforce (production org)
2. Go to **Setup** → **App Manager** → **Connected Apps**
3. Find the Connected App with this Consumer Key:
   ```
   3MVG9zeKbAVObYjM65A.dgSIEzWjIj_uEfDAIIVaIYPUrfhrbUgQELxoawtB0urECFyRya5sEDe97_FHgolsJ
   ```
4. Click **View** → **Manage Consumer Details**
5. Click **Reveal** next to "Consumer Secret" (if it's hidden)
6. **Copy the Consumer Secret** (it's a long string, usually 64+ characters)

### Step 2: Update Secret Manager

**Option A: Using PowerShell Script (Recommended)**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/update_salesforce_client_secret.ps1 -ConsumerSecret "YOUR_CONSUMER_SECRET_HERE"
```

**Option B: Using gcloud Command**
```powershell
echo -n "YOUR_CONSUMER_SECRET_HERE" | gcloud secrets versions add salesforce-client-secret --data-file=- --project=maharani-sales-hub-11-2025
```

**Option C: Interactive Script**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/fix_salesforce_oauth.ps1
```

### Step 3: Verify

After updating, the script will automatically test OAuth authentication. If successful, you'll see:
```
✓ OAuth Authentication SUCCESSFUL!
Instance URL: https://dc0000000qzo7mag.my.salesforce.com
```

## About Security Token

**You do NOT need the `salesforce-security-token` when using OAuth.**

The security token is only needed for username/password authentication. Since we're using OAuth (refresh token flow), you can ignore it.

## Testing the Sync

Once OAuth is working, test the sync:
```powershell
$token = gcloud auth print-identity-token
Invoke-RestMethod -Uri "https://salesforce-sync-z455yfejea-uc.a.run.app" `
  -Method Post `
  -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} `
  -Body '{"object_type":"Account","sync_type":"full"}'
```

## Troubleshooting

If you still get "invalid_client" after updating:
1. Verify the Consumer Secret is from the **same Connected App** as the Consumer Key
2. Make sure there are no extra spaces or newlines in the secret
3. Check that you're using the **production** Connected App (not sandbox)
4. Verify the Connected App has the correct OAuth settings:
   - OAuth Scopes: `Full access (full)`, `Perform requests on your behalf at any time (refresh_token, offline_access)`, `Access and manage your data (api)`
   - Callback URL: `https://login.salesforce.com/services/oauth2/success`

