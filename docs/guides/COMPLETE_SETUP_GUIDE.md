# Complete Setup Guide: Get Anand's Emails

This guide will help you complete the two critical steps needed to fetch emails from Anand's Gmail account.

---

## PART 1: Store Service Account Key in Secret Manager

### Step 1: Download the Service Account Key

1. **Go to GCP Console:**
   - URL: https://console.cloud.google.com/iam-admin/serviceaccounts?project=maharani-sales-hub-11-2025
   - Sign in with your GCP account

2. **Find and Click on the Service Account:**
   - Click on: `sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`

3. **Create a New Key:**
   - Go to **"KEYS"** tab
   - Click **"ADD KEY"** → **"Create new key"**
   - Select **"JSON"** format
   - Click **"CREATE"**
   - The JSON file will download automatically

4. **Save the File Securely:**
   - ⚠️ **Important:** Save this file - you can't download it again!
   - The file is usually named: `maharani-sales-hub-11-2025-xxxxx.json`
   - Usually in your Downloads folder

### Step 2: Store the Key in Secret Manager

**Option A: Using PowerShell Script (Recommended)**
```powershell
.\store_service_account_key.ps1
```

**Option B: Manual Storage**
```powershell
# Replace path with your actual file path
$keyPath = "C:\Users\YourName\Downloads\maharani-sales-hub-11-2025-xxxxx.json"
cat $keyPath | gcloud secrets create service-account-key-json --data-file=- --project=maharani-sales-hub-11-2025

# Grant service account access
gcloud secrets add-iam-policy-binding service-account-key-json `
  --member="serviceAccount:sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" `
  --project=maharani-sales-hub-11-2025
```

**Verify:**
```powershell
gcloud secrets describe service-account-key-json --project=maharani-sales-hub-11-2025
```

---

## PART 2: Configure Domain-Wide Delegation in Google Workspace Admin

### Prerequisites

- **Google Workspace Admin** access (super admin)
- **OAuth Client ID** from Secret Manager (we'll get this below)

### Step 1: Get the OAuth Client ID

**Check if OAuth Client ID exists:**
```powershell
gcloud secrets versions access latest --secret="gmail-oauth-client-id" --project=maharani-sales-hub-11-2025
```

**If not found, create it:**
1. Go to: https://console.cloud.google.com/apis/credentials?project=maharani-sales-hub-11-2025
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **Web application**
4. Name: **Sales Intelligence Gmail Access**
5. Enable **"Domain-wide Delegation"** checkbox
6. Click **"CREATE"**
7. Copy the **Client ID** (format: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)
8. Save to Secret Manager:
   ```powershell
   echo "YOUR_CLIENT_ID.apps.googleusercontent.com" | gcloud secrets versions add gmail-oauth-client-id --data-file=- --project=maharani-sales-hub-11-2025
   ```

### Step 2: Extract Numeric Client ID

From the Client ID (`123456789-abcdefghijklmnop.apps.googleusercontent.com`), extract the numeric part:
- **Numeric Client ID:** `123456789-abcdefghijklmnop` (everything before `.apps.googleusercontent.com`)

### Step 3: Configure in Google Workspace Admin

1. **Go to Google Workspace Admin Console:**
   - URL: https://admin.google.com/
   - Sign in as **super admin**

2. **Navigate to Domain-Wide Delegation:**
   - Go to **Security** → **API Controls** → **Domain-wide Delegation**
   - (Or search for "Domain-wide Delegation")

3. **Add New Client:**
   - Click **"Add new"**

4. **Enter Client Details:**
   - **Client ID:** Enter the numeric Client ID (e.g., `123456789-abcdefghijklmnop`)
   - **OAuth Scopes** (one per line):
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```

5. **Authorize:**
   - Click **"Authorize"**

6. **Verify:**
   - The Client ID should appear in the list
   - Make sure the scopes are correct

---

## PART 3: Test the Setup

### Step 1: Verify Everything is Ready

```powershell
# Check function status
gcloud functions describe gmail-sync --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --format="get(state)"

# Check service account key exists
gcloud secrets describe service-account-key-json --project=maharani-sales-hub-11-2025

# Check OAuth Client ID exists
gcloud secrets versions access latest --secret="gmail-oauth-client-id" --project=maharani-sales-hub-11-2025
```

### Step 2: Test gmail-sync Function

```powershell
# Test for Anand's mailbox
$jsonBody = '{\"sync_type\":\"incremental\",\"mailbox_email\":\"anand@maharaniweddings.com\"}'
gcloud functions call gmail-sync --gen2 --region=us-central1 --data=$jsonBody --project=maharani-sales-hub-11-2025
```

### Step 3: Check the Results in BigQuery

```powershell
# Check if emails were synced
bq query --use_legacy_sql=false --project_id=maharani-sales-hub-11-2025 `
  "SELECT COUNT(*) as message_count FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\` WHERE mailbox_email = 'anand@maharaniweddings.com'"

# View recent emails
bq query --use_legacy_sql=false --project_id=maharani-sales-hub-11-2025 `
  "SELECT message_id, subject, from_email, sent_at FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\` WHERE mailbox_email = 'anand@maharaniweddings.com' ORDER BY sent_at DESC LIMIT 10"
```

---

## Quick Reference

### Service Account Email
```
sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com
```

### Mailbox Email
```
anand@maharaniweddings.com
```

### Project ID
```
maharani-sales-hub-11-2025
```

### Required Secrets
- `service-account-key-json` - Service account private key JSON
- `gmail-oauth-client-id` - Gmail OAuth Client ID for DWD

### Required OAuth Scopes
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
```

---

## Troubleshooting

### Error: "Service account key not found"
- Make sure you stored the key: `gcloud secrets describe service-account-key-json`
- Verify the service account has access: Check IAM permissions

### Error: "Domain-Wide Delegation not configured"
- Verify DWD is set up in Google Workspace Admin
- Check that the Client ID matches exactly (numeric part only)
- Ensure OAuth scopes are correct

### Error: "403 Forbidden" when accessing Gmail
- Check DWD is properly configured
- Verify service account email matches
- Ensure OAuth scopes include both readonly and modify

---

## Next Steps After Setup

1. ✅ Store service account key → Done
2. ✅ Configure Domain-Wide Delegation → Done
3. ✅ Test gmail-sync function
4. ✅ Verify emails in BigQuery
5. ✅ Set up Cloud Scheduler for automated sync (optional)

---

**Need Help?** Check the logs:
```powershell
gcloud functions logs read gmail-sync --gen2 --region=us-central1 --project=maharani-sales-hub-11-2025 --limit=50
```

