# Quick Start - Testing Guide

## Prerequisites Checklist

Before testing, ensure you have:

### 1. ✅ Set GCP Project ID

**Windows PowerShell:**
```powershell
$env:GCP_PROJECT_ID = "your-project-id"
```

**Windows CMD:**
```cmd
set GCP_PROJECT_ID=your-project-id
```

**Linux/Mac:**
```bash
export GCP_PROJECT_ID=your-project-id
```

### 2. ✅ Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install just the essential packages:
```bash
pip install google-cloud-secret-manager google-cloud-bigquery google-cloud-pubsub google-api-python-client google-auth-oauthlib requests
```

### 3. ✅ Authenticate with GCP

**Option A: Using gcloud CLI (recommended)**
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**Option B: Using service account key file**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 4. ✅ Create Secrets in Secret Manager

Create all required secrets in Google Cloud Secret Manager:

```bash
# HubSpot
echo -n "your-hubspot-token" | gcloud secrets create hubspot_access_token --data-file=-

# Gmail - Anand
echo -n "your-client-id" | gcloud secrets create gmail_oauth_client_id_anand --data-file=-
echo -n "your-client-secret" | gcloud secrets create gmail_oauth_client_secret_anand --data-file=-
echo -n "your-refresh-token" | gcloud secrets create gmail_oauth_refresh_token_anand --data-file=-

# Gmail - Larnie
echo -n "your-client-id" | gcloud secrets create gmail_oauth_client_id_larnie --data-file=-
echo -n "your-client-secret" | gcloud secrets create gmail_oauth_client_secret_larnie --data-file=-
echo -n "your-refresh-token" | gcloud secrets create gmail_oauth_refresh_token_larnie --data-file=-

# Gmail - Lia
echo -n "your-client-id" | gcloud secrets create gmail_oauth_client_id_lia --data-file=-
echo -n "your-client-secret" | gcloud secrets create gmail_oauth_client_secret_lia --data-file=-
echo -n "your-refresh-token" | gcloud secrets create gmail_oauth_refresh_token_lia --data-file=-

# Salesforce
echo -n "your-client-id" | gcloud secrets create salesforce_client_id --data-file=-
echo -n "your-client-secret" | gcloud secrets create salesforce_client_secret --data-file=-
echo -n "your-refresh-token" | gcloud secrets create salesforce_refresh_token --data-file=-

# Dialpad
echo -n "your-api-key" | gcloud secrets create dialpad_api_key --data-file=-
```

**Required Secrets List:**
- `hubspot_access_token`
- `gmail_oauth_client_id_anand`
- `gmail_oauth_client_secret_anand`
- `gmail_oauth_refresh_token_anand`
- `gmail_oauth_client_id_larnie`
- `gmail_oauth_client_secret_larnie`
- `gmail_oauth_refresh_token_larnie`
- `gmail_oauth_client_id_lia`
- `gmail_oauth_client_secret_lia`
- `gmail_oauth_refresh_token_lia`
- `salesforce_client_id`
- `salesforce_client_secret`
- `salesforce_refresh_token`
- `dialpad_api_key`

### 5. ✅ Verify Readiness

Run the readiness check:
```bash
python scripts/check_readiness.py
```

This will verify:
- ✅ Project ID is set
- ✅ Python packages are installed
- ✅ GCP authentication is working
- ✅ Service account exists
- ✅ All secrets exist in Secret Manager
- ✅ BigQuery dataset exists (optional)

## Testing Steps

Once readiness check passes:

### Step 1: Test Secret Manager Integration

```bash
python -c "from utils.secret_manager import get_hubspot_access_token; print('Secret Manager works!')"
```

### Step 2: Test Individual Integrations

**Gmail:**
```bash
python integrations/gmail_oauth.py
```

**HubSpot:**
```bash
python integrations/hubspot_api.py
```

**Salesforce:**
```bash
python integrations/salesforce_oauth.py
```

**Dialpad:**
```bash
python integrations/dialpad_api.py
```

### Step 3: Run All Examples

```bash
python examples/integration_examples.py
```

### Step 4: Set Up Infrastructure (Optional)

```bash
# Check IAM permissions
python scripts/check_iam_permissions.py

# Set up Pub/Sub topics
python scripts/setup_pubsub.py

# Set up BigQuery tables
python scripts/setup_bigquery.py

# Deploy Cloud Functions
python scripts/setup_cloud_functions.py

# Set up Cloud Scheduler
python scripts/setup_cloud_scheduler.py
```

## Troubleshooting

### Issue: "GCP_PROJECT_ID environment variable is not set"
**Solution:** Set the environment variable (see step 1 above)

### Issue: "Missing Python packages"
**Solution:** Run `pip install -r requirements.txt`

### Issue: "Permission denied" or "Not authenticated"
**Solution:** Run `gcloud auth application-default login`

### Issue: "Secret not found"
**Solution:** Create the missing secret in Secret Manager (see step 4 above)

### Issue: "Service account does not exist"
**Solution:** Create the service account:
```bash
gcloud iam service-accounts create sales-intel-poc-sa \
    --display-name="Sales Intelligence POC Service Account"
```

## Quick Test Command

After setup, run this to test everything:
```bash
python scripts/check_readiness.py && python examples/integration_examples.py
```

## Need Help?

- Check `docs/INTEGRATION_GUIDE.md` for detailed documentation
- Review `INTEGRATION_MODULES_README.md` for implementation details
- Check Cloud Logging for error messages

