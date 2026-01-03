#!/bin/bash
# Update Salesforce from Sandbox to Production
# Client can run this themselves to switch to production

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Switching Salesforce to Production"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Update secrets (client will run these manually)
echo "Step 1: Update Salesforce Secrets"
echo "----------------------------------------"
echo "Run these commands to update secrets (replace with your production values):"
echo ""
echo "  echo -n 'YOUR_PRODUCTION_USERNAME' | gcloud secrets versions add salesforce-username --data-file=-"
echo "  echo -n 'YOUR_PRODUCTION_PASSWORD' | gcloud secrets versions add salesforce-password --data-file=-"
echo "  echo -n 'YOUR_PRODUCTION_SECURITY_TOKEN' | gcloud secrets versions add salesforce-security-token --data-file=-"
echo ""
read -p "Have you updated the secrets? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please update secrets first, then run this script again."
    exit 1
fi

# Step 2: Redeploy with production domain
echo ""
echo "Step 2: Redeploying Salesforce Sync with Production Domain..."
echo ""

gcloud functions deploy salesforce-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=salesforce_sync \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,SALESFORCE_DOMAIN=login" \
  --project=$PROJECT_ID

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy salesforce-sync function"
    exit 1
fi

echo ""
echo "✓ Salesforce sync deployed successfully with production domain (login)"
echo ""

# Step 3: Wait for deployment
echo "Step 3: Waiting for deployment to be ready..."
sleep 10

# Step 4: Test sync
echo ""
echo "Step 4: Testing Salesforce sync..."
echo ""

TOKEN=$(gcloud auth print-access-token)
FUNCTION_NAME="salesforce-sync"
URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "$URL" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"sync_type":"full"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status Code: $HTTP_CODE"
echo "Response: $BODY"
echo ""

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "202" ]; then
    echo "✓ Successfully triggered Salesforce sync (HTTP $HTTP_CODE)"
    echo ""
    echo "Waiting 30 seconds before checking logs..."
    sleep 30
    echo ""
    echo "Recent Salesforce sync logs:"
    echo "----------------------------------------"
    gcloud functions logs read salesforce-sync \
      --gen2 \
      --region=$REGION \
      --project=$PROJECT_ID \
      --limit=20
    echo "----------------------------------------"
    echo ""
    echo "=========================================="
    echo "Salesforce Production Switch Complete!"
    echo "=========================================="
    echo ""
    echo "Verify data in BigQuery:"
    echo "  bq query \"SELECT COUNT(*) FROM sales_intelligence.sf_accounts\""
    echo ""
else
    echo "✗ Failed to trigger Salesforce sync (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
    echo ""
    echo "Check the logs for details:"
    echo "  gcloud functions logs read salesforce-sync --gen2 --region=$REGION --project=$PROJECT_ID --limit=50"
    exit 1
fi

