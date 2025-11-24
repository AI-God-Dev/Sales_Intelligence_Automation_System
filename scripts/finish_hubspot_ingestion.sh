#!/bin/bash
# Complete HubSpot ingestion: Redeploy with increased memory and trigger ingestion
# This script:
# 1. Redeploys HubSpot sync with 1GB memory
# 2. Waits for deployment to complete
# 3. Triggers HubSpot ingestion
# 4. Monitors logs for success/failure

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "HubSpot Ingestion - Complete Setup"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Step 1: Redeploy HubSpot sync with 1GB memory
echo "Step 1: Redeploying HubSpot sync with 1GB memory..."
echo ""

gcloud functions deploy hubspot-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=hubspot_sync \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=1024MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy HubSpot sync function"
    exit 1
fi

echo ""
echo "✓ HubSpot sync deployed successfully with 1GB memory"
echo ""

# Step 2: Wait for deployment to be ready
echo "Step 2: Waiting for deployment to be ready..."
sleep 10

# Verify deployment
echo "Verifying deployment status..."
DEPLOY_STATUS=$(gcloud functions describe hubspot-sync \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(state)" 2>/dev/null || echo "UNKNOWN")

echo "Deployment status: $DEPLOY_STATUS"
echo ""

# Step 3: Get access token for triggering
echo "Step 3: Preparing to trigger HubSpot ingestion..."
TOKEN=$(gcloud auth print-access-token)
if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get access token. Please run: gcloud auth login"
    exit 1
fi

# Step 4: Trigger HubSpot sync
echo "Step 4: Triggering HubSpot ingestion..."
echo ""

FUNCTION_NAME="hubspot-sync"
URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
DATA='{"sync_type":"full"}'

echo "URL: $URL"
echo "Payload: $DATA"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "$URL" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$DATA")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status Code: $HTTP_CODE"
echo "Response Body: $BODY"
echo ""

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "202" ]; then
    echo "✓ Successfully triggered HubSpot ingestion (HTTP $HTTP_CODE)"
    echo ""
    
    # Step 5: Monitor logs
    echo "Step 5: Monitoring ingestion progress..."
    echo "Waiting 30 seconds before checking logs..."
    sleep 30
    
    echo ""
    echo "Recent HubSpot sync logs:"
    echo "----------------------------------------"
    gcloud functions logs read hubspot-sync \
      --region=$REGION \
      --project=$PROJECT_ID \
      --limit=20 \
      --format="table(timestamp,severity,textPayload)" \
      2>/dev/null || gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=hubspot-sync" \
      --project=$PROJECT_ID \
      --limit=20 \
      --format="table(timestamp,severity,textPayload)" \
      2>/dev/null || echo "Could not retrieve logs. Check in Cloud Console."
    echo "----------------------------------------"
    echo ""
    
    echo "=========================================="
    echo "HubSpot Ingestion Setup Complete!"
    echo "=========================================="
    echo ""
    echo "To view detailed logs, run:"
    echo "  gcloud functions logs read hubspot-sync --region=$REGION --project=$PROJECT_ID --limit=50"
    echo ""
    echo "Or check in Cloud Console:"
    echo "  https://console.cloud.google.com/functions/details/$REGION/hubspot-sync?project=$PROJECT_ID"
    echo ""
    
else
    echo "✗ Failed to trigger HubSpot ingestion (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if you have invoke permissions:"
    echo "   bash scripts/grant_user_invoker_permission.sh"
    echo "2. Check function status:"
    echo "   gcloud functions describe hubspot-sync --region=$REGION --project=$PROJECT_ID"
    exit 1
fi





