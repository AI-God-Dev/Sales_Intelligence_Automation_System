#!/bin/bash
# Update Salesforce domain to sandbox (test.salesforce.com)
# Run this to configure Cloud Function for Salesforce sandbox

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT_NAME="${GCP_SERVICE_ACCOUNT_NAME:-sales-intel-poc-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "Updating Salesforce Sync for Sandbox"
echo "Project: $PROJECT_ID"
echo "Domain: test.salesforce.com (sandbox)"
echo "=========================================="
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Redeploy Salesforce Sync with sandbox domain
echo "Redeploying Salesforce Sync Function with sandbox domain..."
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
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,SALESFORCE_DOMAIN=test" \
  --project=$PROJECT_ID

echo ""
echo "✅ Salesforce Sync updated to use sandbox domain (test.salesforce.com)!"
echo ""
echo "💡 To use production domain instead, set SALESFORCE_DOMAIN=login and redeploy"
echo "   Example: SALESFORCE_DOMAIN=login bash scripts/update_salesforce_domain.sh"
echo ""

