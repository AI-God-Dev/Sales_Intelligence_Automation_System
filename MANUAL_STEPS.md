# Manual Steps Required Before Automated Setup

This document lists the **only manual steps** you must perform before running the automated setup scripts. These steps require creating credentials in third-party platforms (Gmail, Salesforce, Dialpad, HubSpot) and cannot be automated.

## Prerequisites

1. **Google Cloud SDK Installed**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Verify: `gcloud --version` and `bq --version`

2. **Authenticated gcloud CLI**
   ```powershell
   gcloud auth login
   gcloud config set project maharani-sales-hub-11-2025
   ```

3. **Python 3.11+ Installed** (for local testing)
   - Verify: `python --version`

## Manual Steps

### 1. Gmail OAuth Client ID & Domain-Wide Delegation

**Purpose:** Allow the system to access Gmail mailboxes using Domain-Wide Delegation.

**Steps:**

1. **Create OAuth 2.0 Client ID:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app" or "Web application"
   - Name: "Sales Intelligence Gmail Access"
   - Click "Create"
   - **Save the Client ID and Client Secret** (you'll need these for Secret Manager)

2. **Enable Domain-Wide Delegation:**
   - In the OAuth client details, check "Enable Google Workspace Domain-wide Delegation"
   - Note the Client ID (you'll need this for step 3)

3. **Configure Domain-Wide Delegation in Google Workspace Admin:**
   - Go to: https://admin.google.com
   - Navigate to: Security → API Controls → Domain-wide Delegation
   - Click "Add new"
   - Enter the Client ID from step 2
   - Add these OAuth scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     https://www.googleapis.com/auth/userinfo.email
     ```
   - Click "Authorize"

4. **Store Credentials in Secret Manager:**
   - When running `create_secrets.ps1`, you'll be prompted to enter:
     - `gmail-oauth-client-id`: The Client ID from step 1
     - `gmail-oauth-client-secret`: The Client Secret from step 1

**Required Information:**
- Gmail OAuth Client ID
- Gmail OAuth Client Secret

---

### 2. Salesforce Connected App

**Purpose:** Allow the system to authenticate with Salesforce and access data.

**Steps:**

1. **Create Connected App:**
   - Log into Salesforce: https://login.salesforce.com (or https://test.salesforce.com for sandbox)
   - Go to: Setup → App Manager → New Connected App
   - Fill in:
     - Connected App Name: "Sales Intelligence System"
     - API Name: "Sales_Intelligence_System"
     - Contact Email: Your email
   - Enable OAuth Settings:
     - Callback URL: `http://localhost:8080/callback` (or any valid URL)
     - Selected OAuth Scopes:
       - "Access and manage your data (api)"
       - "Perform requests on your behalf at any time (refresh_token, offline_access)"
       - "Access your basic information (id, profile, email, address, phone)"
   - Click "Save"

2. **Get Credentials:**
   - After saving, click "Manage Consumer Details"
   - **Save the Consumer Key (Client ID)** and **Consumer Secret (Client Secret)**

3. **Get Security Token:**
   - Go to: Setup → My Personal Information → Reset My Security Token
   - Click "Reset Security Token"
   - Check your email for the security token

4. **Get Username and Password:**
   - Your Salesforce username (email)
   - Your Salesforce password

5. **Store Credentials in Secret Manager:**
   - When running `create_secrets.ps1`, you'll be prompted to enter:
     - `salesforce-client-id`: Consumer Key from step 2
     - `salesforce-client-secret`: Consumer Secret from step 2
     - `salesforce-username`: Your Salesforce username
     - `salesforce-password`: Your Salesforce password
     - `salesforce-security-token`: Security token from step 3
     - `salesforce-refresh-token`: (Leave empty initially, will be generated on first connection)

**Required Information:**
- Salesforce Consumer Key (Client ID)
- Salesforce Consumer Secret (Client Secret)
- Salesforce Username
- Salesforce Password
- Salesforce Security Token

---

### 3. Dialpad API Key

**Purpose:** Allow the system to access Dialpad call logs and transcripts.

**Steps:**

1. **Log into Dialpad:**
   - Go to: https://dialpad.com
   - Log in with your admin account

2. **Generate API Key:**
   - Go to: Settings → Integrations → API
   - Click "Create API Key" or "Generate New Key"
   - **Save the API Key** (you may only see it once)

3. **Store Credential in Secret Manager:**
   - When running `create_secrets.ps1`, you'll be prompted to enter:
     - `dialpad-api-key`: The API key from step 2

**Required Information:**
- Dialpad API Key

---

### 4. HubSpot Private App Access Token

**Purpose:** Allow the system to access HubSpot sequences and contact data.

**Steps:**

1. **Log into HubSpot:**
   - Go to: https://app.hubspot.com
   - Log in with your admin account

2. **Create Private App:**
   - Go to: Settings → Integrations → Private Apps
   - Click "Create a private app"
   - Name: "Sales Intelligence System"
   - Click "Create app"

3. **Configure Scopes:**
   - Under "Scopes", select:
     - `crm.objects.contacts.read`
     - `crm.objects.contacts.write`
     - `sequences.read`
     - `sequences.write`
     - `crm.objects.companies.read`
   - Click "Save"

4. **Get Access Token:**
   - After saving, go to the "Auth" tab
   - **Copy the Private App Access Token**

5. **Store Credential in Secret Manager:**
   - When running `create_secrets.ps1`, you'll be prompted to enter:
     - `hubspot-api-key`: The Private App Access Token from step 4

**Required Information:**
- HubSpot Private App Access Token

---

## Summary Checklist

Before running `setup_complete.ps1`, ensure you have:

- [ ] Gmail OAuth Client ID
- [ ] Gmail OAuth Client Secret
- [ ] Gmail Domain-Wide Delegation configured
- [ ] Salesforce Consumer Key (Client ID)
- [ ] Salesforce Consumer Secret (Client Secret)
- [ ] Salesforce Username
- [ ] Salesforce Password
- [ ] Salesforce Security Token
- [ ] Dialpad API Key
- [ ] HubSpot Private App Access Token
- [ ] Google Cloud SDK installed and authenticated
- [ ] Project set: `gcloud config set project maharani-sales-hub-11-2025`

## Next Steps

Once you have all the credentials above:

1. Run `.\setup_complete.ps1` (this will prompt you to enter each secret value)
2. Or run individual setup scripts in order:
   - `.\enable_apis.ps1`
   - `.\create_secrets.ps1` (enter all credentials here)
   - `.\scripts\setup_bigquery.ps1`
   - `.\scripts\create_pubsub_topic.ps1`
   - `.\scripts\deploy_functions.ps1`
   - `.\scripts\create_scheduler_jobs.ps1`
   - `.\scripts\verify_deployment.ps1`

## Troubleshooting

If you encounter issues:

1. **Gmail Access Denied:**
   - Verify Domain-Wide Delegation is enabled
   - Check that the Client ID matches in both places
   - Verify OAuth scopes are correct

2. **Salesforce Authentication Failed:**
   - Verify username/password are correct
   - Check that security token is current (reset if needed)
   - Ensure Connected App is active

3. **Dialpad/HubSpot API Errors:**
   - Verify API keys are correct and not expired
   - Check that required scopes/permissions are granted

For more help, see `docs/PHASE1_HANDOFF.md`.

