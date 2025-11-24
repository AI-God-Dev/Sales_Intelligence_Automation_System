# 📋 Client Self-Service: Update Credentials & Test

## ✅ You Can Do This Yourself - No Credentials Need to Be Shared!

Follow these scripts step-by-step to update credentials and test everything.

---

## 🔧 Step 1: Update Salesforce to Production

### Option A: Use the Automated Script (Recommended)

**Linux/Mac:**
```bash
bash scripts/update_salesforce_to_production.sh
```

**Windows PowerShell:**
```powershell
.\scripts\update_salesforce_to_production.ps1
```

The script will:
1. Prompt you to update secrets first
2. Redeploy salesforce-sync with production domain
3. Test the sync
4. Show logs

### Option B: Manual Steps

**1. Update Secrets:**
```bash
# Update username
echo -n "YOUR_PRODUCTION_USERNAME" | gcloud secrets versions add salesforce-username --data-file=-

# Update password
echo -n "YOUR_PRODUCTION_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=-

# Update security token
echo -n "YOUR_PRODUCTION_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=-
```

**2. Redeploy Function:**
```bash
gcloud functions deploy salesforce-sync \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=salesforce_sync --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=login" \
  --project=maharani-sales-hub-11-2025
```

---

## 🔧 Step 2: Fix HubSpot (404 Error)

**Run:**
```bash
bash scripts/finish_hubspot_ingestion.sh
```

This will:
- Redeploy with fix
- Trigger ingestion
- Show logs

---

## 🔧 Step 3: Test All Ingestion

**Run the test script:**
```bash
bash scripts/test_all_ingestion.sh
```

Or manually test each:
```bash
# Gmail
gcloud functions call gmail-sync --gen2 --region=us-central1 --data '{}'

# Salesforce
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{}'

# Dialpad
gcloud functions call dialpad-sync --gen2 --region=us-central1 --data '{}'

# HubSpot
gcloud functions call hubspot-sync --gen2 --region=us-central1 --data '{}'
```

---

## ✅ Step 4: Verify Data in BigQuery

```bash
# Check counts
bq query "SELECT COUNT(*) FROM sales_intelligence.gmail_messages"
bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"
bq query "SELECT COUNT(*) FROM sales_intelligence.dialpad_calls"
bq query "SELECT COUNT(*) FROM sales_intelligence.hubspot_sequences"
```

---

## 📝 Quick Reference Commands

### Update Any Secret
```bash
echo -n "SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### View Secret (verify)
```bash
gcloud secrets versions access latest --secret="SECRET_NAME"
```

### Redeploy Function
```bash
gcloud functions deploy FUNCTION_NAME \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=ENTRY_POINT --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --project=maharani-sales-hub-11-2025
```

### View Logs
```bash
gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1 --limit=50
```

---

## 🎯 Summary - What to Run

1. **Update Salesforce secrets** → Use commands above
2. **Run:** `bash scripts/update_salesforce_to_production.sh`
3. **Run:** `bash scripts/finish_hubspot_ingestion.sh`
4. **Run:** `bash scripts/test_all_ingestion.sh`
5. **Verify:** Check BigQuery counts

**All can be done on your side!**

