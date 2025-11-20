#!/bin/bash
# Deploy Cloud Functions to GCP using service account impersonation
# IMPORTANT: Deploys from project root to include shared modules (utils, config, entity_resolution)

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

echo "Deploying Cloud Functions to project: $PROJECT_ID"
echo "Using service account: $SERVICE_ACCOUNT"
echo "Note: Deploying from project root to include shared modules"

# Get project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Deploy Gmail Sync Function
echo "Deploying Gmail Sync Function..."
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

# Deploy Salesforce Sync Function
echo "Deploying Salesforce Sync Function..."
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
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

# Deploy Dialpad Sync Function
echo "Deploying Dialpad Sync Function..."
gcloud functions deploy dialpad-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=dialpad_sync \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

# Deploy HubSpot Sync Function
echo "Deploying HubSpot Sync Function..."
gcloud functions deploy hubspot-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=hubspot_sync \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

# Deploy Entity Resolution Function
echo "Deploying Entity Resolution Function..."
gcloud functions deploy entity-resolution \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=entity_resolution \
  --trigger-http \
  --service-account=$SERVICE_ACCOUNT \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --min-instances=0 \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --project=$PROJECT_ID

# Grant Cloud Scheduler permission to invoke functions
echo "Granting Cloud Scheduler permission to invoke functions..."
gcloud functions add-iam-policy-binding gmail-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID

gcloud functions add-iam-policy-binding salesforce-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID

gcloud functions add-iam-policy-binding dialpad-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID

gcloud functions add-iam-policy-binding hubspot-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID

gcloud functions add-iam-policy-binding entity-resolution \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID

echo "Deployment complete!"

