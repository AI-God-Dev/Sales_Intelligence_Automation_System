#!/bin/bash
# View real-time logs for Gmail sync Cloud Function
# For Gen2 Cloud Functions (Cloud Run), use Cloud Run logging

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
FUNCTION_NAME="gmail-sync"

echo "Viewing real-time logs for: $FUNCTION_NAME"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "Press Ctrl+C to stop watching logs"
echo "----------------------------------------"
echo ""

# For Gen2 functions (Cloud Run), use Cloud Run service name
# Format: PROJECT_ID-REGION-FUNCTION_NAME
SERVICE_NAME="${PROJECT_ID}-${REGION}-${FUNCTION_NAME}"

# Real-time log streaming using Cloud Run logging
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=$FUNCTION_NAME" \
    --project=$PROJECT_ID \
    --format="table(timestamp,severity,textPayload)"

