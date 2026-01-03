#!/bin/bash
# Deploy HubSpot sync function with correct environment variables
# This script uses an env vars file to avoid comma-separated parsing issues

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-${BIGQUERY_DATASET:-sales_intelligence}}"
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Deploying HubSpot Sync Function..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Create temporary env vars file
ENV_VARS_FILE=$(mktemp)
cat > "$ENV_VARS_FILE" <<EOF
GCP_PROJECT_ID: $PROJECT_ID
GCP_REGION: $REGION
BQ_DATASET_NAME: $DATASET_NAME
EOF

# Deploy function
gcloud functions deploy hubspot-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=hubspot_sync \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SERVICE_ACCOUNT \
  --memory=2048MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --env-vars-file="$ENV_VARS_FILE" \
  --project=$PROJECT_ID

# Clean up
rm -f "$ENV_VARS_FILE"

echo ""
echo "✓ HubSpot sync deployed successfully!"




























