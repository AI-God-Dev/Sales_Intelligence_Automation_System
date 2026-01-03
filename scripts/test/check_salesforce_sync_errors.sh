#!/bin/bash
# Check Salesforce sync logs for errors

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "Checking Salesforce sync logs for errors..."
echo "Project: $PROJECT_ID"
echo ""

# Check recent logs
echo "Recent logs (last 50):"
echo "----------------------------------------"
gcloud functions logs read salesforce-sync \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=50

echo ""
echo "----------------------------------------"
echo ""

# Check for errors only
echo "Errors only:"
echo "----------------------------------------"
gcloud functions logs read salesforce-sync \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=100 | grep -i "error\|exception\|failed\|traceback" || echo "No errors found in recent logs"

echo ""
echo "----------------------------------------"
echo ""
echo "For real-time logs, use:"
echo "gcloud logging tail \"resource.type=cloud_run_revision AND resource.labels.service_name=salesforce-sync\" --project=$PROJECT_ID"

