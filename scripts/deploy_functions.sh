#!/bin/bash
# Deploy Cloud Functions to GCP

set -e

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"

echo "Deploying Cloud Functions to project: $PROJECT_ID"

# Deploy Gmail Sync Function
echo "Deploying Gmail Sync Function..."
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=cloud_functions/gmail_sync \
  --entry-point=gmail_sync \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --project=$PROJECT_ID

# Deploy Salesforce Sync Function
echo "Deploying Salesforce Sync Function..."
gcloud functions deploy salesforce-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=cloud_functions/salesforce_sync \
  --entry-point=salesforce_sync \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --project=$PROJECT_ID

echo "Deployment complete!"

