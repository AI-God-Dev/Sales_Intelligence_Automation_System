#!/bin/bash
# Deploy Cloud Functions to GCP using service account impersonation

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"

echo "Deploying Cloud Functions to project: $PROJECT_ID"
echo "Using service account: $SERVICE_ACCOUNT"

# Deploy Gmail Sync Function
echo "Deploying Gmail Sync Function..."
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=cloud_functions/gmail_sync \
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
  --source=cloud_functions/salesforce_sync \
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
  --source=cloud_functions/dialpad_sync \
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
  --source=cloud_functions/hubspot_sync \
  --entry-point=hubspot_sync \
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

echo "Deployment complete!"

