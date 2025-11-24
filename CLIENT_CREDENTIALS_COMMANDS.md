# Salesforce Client Credentials - Commands Only

## Step 1: Update Client ID
```bash
echo -n "YOUR_PRODUCTION_CLIENT_ID" | gcloud secrets versions add salesforce-client-id --data-file=-
```

## Step 2: Update Client Secret
```bash
echo -n "YOUR_PRODUCTION_CLIENT_SECRET" | gcloud secrets versions add salesforce-client-secret --data-file=-
```

## Step 3: Add Instance URL
```bash
echo -n "https://dc0000000qzo7mag.lightning.force.com/" | gcloud secrets versions add salesforce-instance-url --data-file=-
```

## Step 4: Redeploy Function
```bash
gcloud functions deploy salesforce-sync \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=salesforce_sync --trigger-http \
  --service-account=sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1,SALESFORCE_DOMAIN=login" \
  --project=maharani-sales-hub-11-2025
```

## Step 5: Test
```bash
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{}'
```

## Step 6: Verify
```bash
bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"
```

