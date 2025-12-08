#!/bin/bash
# Standalone script to deploy gmail-sync with 2GB memory
# Usage: ./scripts/deploy_gmail_sync_2gb.sh

set -e

# Configuration from environment variables
PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-${BIGQUERY_DATASET:-sales_intelligence}}"
SERVICE_ACCOUNT_NAME="${GCP_SERVICE_ACCOUNT_NAME:-sales-intel-poc-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Validate required variables
if [ "$PROJECT_ID" = "YOUR_PROJECT_ID" ] || [ -z "$PROJECT_ID" ]; then
    echo "[ERROR] GCP_PROJECT_ID not set!"
    echo "Set it with: export GCP_PROJECT_ID='your-project-id'"
    exit 1
fi

echo "========================================"
echo "Deploying Gmail Sync with 2GB Memory"
echo "========================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Dataset: $DATASET_NAME"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Ensure we're in project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "main.py" ]; then
    echo "[ERROR] Not in project root! Expected to find main.py"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Deploy gmail-sync with 2GB memory
echo "Deploying gmail-sync function..."
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region="$REGION" \
  --source=. \
  --entry-point=gmail_sync \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account="$SERVICE_ACCOUNT" \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_REGION=$GCP_REGION,BQ_DATASET_NAME=$DATASET_NAME" \
  --project="$PROJECT_ID"

echo ""
echo "✅ Gmail Sync function deployed successfully with 2GB memory!"
echo ""
