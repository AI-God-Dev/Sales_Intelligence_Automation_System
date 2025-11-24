# Client Self-Service Guide - Update Credentials & Test

## ✅ You Can Do This Yourself - No Need to Share Credentials!

Follow these steps to update credentials and test ingestion on your side.

---

## 📋 Step 1: Update Salesforce Production Credentials

### Update Secrets in Secret Manager

**For Linux/Mac:**
```bash
# Update Salesforce username
echo -n "YOUR_PRODUCTION_USERNAME" | gcloud secrets versions add salesforce-username --data-file=-

# Update Salesforce password
echo -n "YOUR_PRODUCTION_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=-

# Update security token
echo -n "YOUR_PRODUCTION_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=-
```

**For Windows PowerShell:**
```powershell
# Update Salesforce username
"YOUR_PRODUCTION_USERNAME" | gcloud secrets versions add salesforce-username --data-file=-

# Update Salesforce password
"YOUR_PRODUCTION_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=-

# Update security token
"YOUR_PRODUCTION_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=-
```

### Switch from Sandbox to Production

**Step 1: Redeploy Salesforce Sync Function with Production Domain**

**For Linux/Mac:**
```bash
# Set production domain
export SALESFORCE_DOMAIN=login

# Redeploy function
gcloud functions deploy salesforce-sync \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=salesforce_sync \
  --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --memory=512MB \
  --timeout=540s \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=login" \
  --project=maharani-sales-hub-11-2025
```

**For Windows PowerShell:**
```powershell
# Set production domain
$env:SALESFORCE_DOMAIN = "login"

# Redeploy function
gcloud functions deploy salesforce-sync `
  --gen2 `
  --runtime=python311 `
  --region=us-central1 `
  --source=. `
  --entry-point=salesforce_sync `
  --trigger-http `
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com `
  --memory=512MB `
  --timeout=540s `
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=login" `
  --project=maharani-sales-hub-11-2025
```

**Step 2: Test Salesforce Sync**
```bash
# Trigger sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"sync_type":"full"}'

# Check logs
gcloud functions logs read salesforce-sync --gen2 --region=us-central1 --limit=50
```

---

## 📋 Step 2: Fix HubSpot Ingestion

**Run the complete HubSpot setup script:**

**For Linux/Mac:**
```bash
bash scripts/finish_hubspot_ingestion.sh
```

**For Windows PowerShell:**
```powershell
# Run the script (or use WSL/Git Bash)
bash scripts/finish_hubspot_ingestion.sh
```

This will:
- Redeploy HubSpot sync with 1GB memory
- Fix the 404 error
- Trigger ingestion
- Show logs

---

## 📋 Step 3: Test Dialpad Sync

### Check if Dialpad API Key is Set
```bash
gcloud secrets versions access latest --secret="dialpad-api-key"
```

### If not set, add it:
```bash
# Linux/Mac
echo -n "YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=-

# Windows PowerShell
"YOUR_DIALPAD_API_KEY" | gcloud secrets versions add dialpad-api-key --data-file=-
```

### Test Dialpad Sync
```bash
# Trigger sync
gcloud functions call dialpad-sync --gen2 --region=us-central1 --data '{"sync_type":"full"}'

# Check logs
gcloud functions logs read dialpad-sync --gen2 --region=us-central1 --limit=50
```

---

## 📋 Step 4: Verify All Ingestion

**Check data in BigQuery:**

```bash
# Gmail (should have data)
bq query "SELECT COUNT(*) FROM sales_intelligence.gmail_messages"

# Salesforce (should have data after production switch)
bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"

# Dialpad (check if data exists)
bq query "SELECT COUNT(*) FROM sales_intelligence.dialpad_calls"

# HubSpot (should work after redeploy)
bq query "SELECT COUNT(*) FROM sales_intelligence.hubspot_sequences"
```

---

## 📋 Quick Command Reference

### Update Any Secret
```bash
echo -n "SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Redeploy Function
```bash
gcloud functions deploy FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=ENTRY_POINT \
  --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

### Trigger Sync
```bash
gcloud functions call FUNCTION_NAME --gen2 --region=us-central1 --data '{}'
```

### View Logs
```bash
gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1 --limit=50
```

---

## ✅ What You'll Do

1. ✅ Update Salesforce secrets → Production credentials
2. ✅ Redeploy salesforce-sync → With `SALESFORCE_DOMAIN=login`
3. ✅ Run finish_hubspot_ingestion.sh → Fix HubSpot 404
4. ✅ Test Dialpad sync → Verify API key and trigger
5. ✅ Verify all counts → Check BigQuery tables

**All steps can be done on your side without sharing credentials!**

