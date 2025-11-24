# Salesforce Client Credentials Setup - Step by Step

## ✅ What You Need (Client Credentials Flow)

Only 3 secrets required:
1. `salesforce-client-id` - Consumer Key from Connected App
2. `salesforce-client-secret` - Consumer Secret from Connected App  
3. `salesforce-instance-url` - Production base URL (e.g., `https://dc0000000qzo7mag.lightning.force.com/`)

**Optional:**
- `salesforce-username` - Only for logging/metadata (no auth role)

---

## 📋 Step-by-Step Commands

### Step 1: Update Client ID

```bash
echo -n "YOUR_PRODUCTION_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=-
```

**What to replace:**
- `YOUR_PRODUCTION_CLIENT_ID` = Consumer Key from your Production Connected App

---

### Step 2: Update Client Secret

```bash
echo -n "YOUR_PRODUCTION_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=-
```

**What to replace:**
- `YOUR_PRODUCTION_CLIENT_SECRET` = Consumer Secret from your Production Connected App

---

### Step 3: Add Instance URL

```bash
echo -n "https://dc0000000qzo7mag.lightning.force.com/" | gcloud secrets versions add salesforce-instance-url --data-file=-
```

**What to replace:**
- `https://dc0000000qzo7mag.lightning.force.com/` = Your actual production instance URL

**How to find it:**
- Log into Salesforce production
- Look at the URL in your browser
- Copy the base URL (e.g., `https://yourinstance.salesforce.com` or `https://yourinstance.lightning.force.com`)

---

### Step 4: Verify Secrets

```bash
# Check Client ID
gcloud secrets versions access latest --secret="salesforce-client-id"

# Check Client Secret
gcloud secrets versions access latest --secret="salesforce-client-secret"

# Check Instance URL
gcloud secrets versions access latest --secret="salesforce-instance-url"
```

---

### Step 5: Redeploy Function with Production Domain

```bash
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

**Important:** `SALESFORCE_DOMAIN=login` means production

---

### Step 6: Test Sync

```bash
# Trigger sync
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"sync_type":"full"}'

# Check logs
gcloud functions logs read salesforce-sync --gen2 --region=us-central1 --limit=50
```

---

### Step 7: Verify Data

```bash
bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"
```

---

## ✅ Summary - What to Run

1. **Update 3 secrets:**
   ```bash
   echo -n "CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=-
   echo -n "CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=-
   echo -n "INSTANCE_URL" | gcloud secrets versions add salesforce-instance-url --data-file=-
   ```

2. **Redeploy:**
   ```bash
   gcloud functions deploy salesforce-sync --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=salesforce_sync --trigger-http --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=login" --project=maharani-sales-hub-11-2025
   ```

3. **Test:**
   ```bash
   gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{}'
   ```

**That's it!**

