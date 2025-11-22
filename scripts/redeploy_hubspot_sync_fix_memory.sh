#!/bin/bash
# Redeploy HubSpot sync with increased memory to fix memory limit exceeded error

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Redeploying HubSpot sync with increased memory (1GB)..."

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

echo "HubSpot sync redeployed with 1GB memory"

