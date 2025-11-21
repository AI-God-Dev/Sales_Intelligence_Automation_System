#!/bin/bash
# Redeploy Gmail Sync Function with rate limiting fixes

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT_NAME="${GCP_SERVICE_ACCOUNT_NAME:-sales-intel-poc-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Redeploying Gmail Sync Function with rate limiting improvements..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Deploy Gmail Sync Function
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=gmail_sync \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

echo ""
echo "✅ Gmail Sync Function redeployed with rate limiting fixes!"
echo ""
echo "The function now includes:"
echo "  - Exponential backoff retry logic"
echo "  - Rate limiting (0.25s delay between requests)"
echo "  - Automatic retry on rate limit errors (up to 5 retries)"
echo "  - Better error handling for failed messages"
echo ""

