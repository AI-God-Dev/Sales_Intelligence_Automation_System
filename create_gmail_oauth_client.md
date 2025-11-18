# Create Gmail OAuth Client ID for Domain-Wide Delegation

## Quick Steps

### Step 1: Create OAuth Client ID in GCP Console

1. **Go to GCP Console:**
   - URL: https://console.cloud.google.com/apis/credentials?project=maharani-sales-hub-11-2025
   - Make sure project `maharani-sales-hub-11-2025` is selected

2. **Configure OAuth Consent Screen (if not done):**
   - If prompted, click "Configure Consent Screen"
   - User Type: **Internal** (for Google Workspace)
   - App name: `Sales Intelligence System`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Click "Add or Remove Scopes"
     - Add: `https://www.googleapis.com/auth/gmail.readonly`
     - Add: `https://www.googleapis.com/auth/gmail.modify`
   - Click "Update" → "Save and Continue"
   - Test users: Skip (for internal apps)
   - Click "Back to Dashboard"

3. **Create OAuth Client ID:**
   - Click **"+ Create Credentials"** → **"OAuth client ID"**
   - Application type: **Web application**
   - Name: `Sales Intelligence Gmail Access`
   - Authorized redirect URIs:
     - For testing: `https://oauth.pstmn.io/v1/callback`
     - Click **"+ Add URI"** to add more if needed
   - Click **"Create"**

4. **Copy Credentials (shown only once!):**
   - **Client ID**: Copy this immediately (format: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)
   - **Client Secret**: Copy this immediately (format: `GOCSPX-...`)
   - ⚠️ **Important**: These are shown only once! Save them securely.

5. **Enable Domain-Wide Delegation:**
   - In the OAuth Client details page, find **"Domain-wide Delegation"** section
   - Check the box: **"Enable Google Workspace Domain-wide Delegation"**
   - Click **"Save"**

### Step 2: Save Credentials to Secret Manager

After creating the OAuth Client ID, save it to Secret Manager:

```powershell
# Update Client ID
$clientId = Read-Host "Enter Gmail OAuth Client ID"
$clientId | gcloud secrets versions add gmail-oauth-client-id --data-file=- --project=maharani-sales-hub-11-2025

# Update Client Secret (secure prompt)
$secret = Read-Host "Enter Gmail OAuth Client Secret" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
$plainSecret = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
$plainSecret | gcloud secrets versions add gmail-oauth-client-secret --data-file=- --project=maharani-sales-hub-11-2025
```

Or run the update script:
```powershell
.\update_secrets.ps1
```

### Step 3: Configure Domain-Wide Delegation in Google Workspace Admin

1. **Go to Google Workspace Admin Console:**
   - URL: https://admin.google.com/
   - Sign in as super admin

2. **Navigate to Domain-Wide Delegation:**
   - Security → API Controls → Domain-wide Delegation
   - Click **"Add new"**

3. **Enter Client Details:**
   - **Client ID**: Paste your OAuth Client ID (the numeric part before `.apps.googleusercontent.com`)
   - **OAuth Scopes** (one per line):
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```
   - Click **"Authorize"**

### Step 4: Verify Setup

```powershell
# Verify Client ID is in Secret Manager
gcloud secrets versions access latest --secret=gmail-oauth-client-id --project=maharani-sales-hub-11-2025

# Verify service account exists
gcloud iam service-accounts describe sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com --project=maharani-sales-hub-11-2025
```

## What You Need

- **Client ID**: `123456789-abcdefghijklmnop.apps.googleusercontent.com` (example)
- **Client Secret**: `GOCSPX-...` (example)
- **OAuth Scopes**:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.modify`

## Notes

- OAuth Client ID is required for Domain-Wide Delegation setup in Google Workspace Admin
- The actual Gmail API calls use service account credentials (not OAuth tokens)
- Domain-Wide Delegation allows the service account to impersonate users
- OAuth Client ID must match exactly in both GCP Console and Workspace Admin

## Troubleshooting

**Issue: "OAuth Consent Screen Required"**
- Configure the consent screen first (Step 1.2 above)
- For internal apps, you can use minimal configuration

**Issue: "Domain-wide Delegation Option Not Visible"**
- Make sure you're using OAuth 2.0 Client ID (not Service Account)
- Check that you're in the correct project
- The option appears after enabling it in OAuth Client settings

**Issue: "Client ID Not Found in Workspace Admin"**
- Double-check the Client ID is correct (no spaces, exact match)
- Wait a few minutes for changes to propagate
- Try creating a new OAuth Client ID if issues persist

