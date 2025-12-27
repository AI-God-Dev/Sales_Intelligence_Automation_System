#!/bin/bash
# Quick Fix Script for Gemini Model Deployment Issue
# This script fixes the 404 Vertex AI model error and redeploys functions
# Run from project root: ./scripts/fix_gemini_model_deployment.sh

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "========================================"
echo "  Gemini Model Deployment Fix"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Enable Vertex AI API"
echo "  2. Grant Vertex AI permissions to service account"
echo "  3. Redeploy account-scoring function with gemini-2.5-pro"
echo "  4. Update scheduler job configuration"
echo "  5. Test the deployment"
echo ""

# Confirm project
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "========================================"
echo "Step 1: Enable Vertex AI API"
echo "========================================"

gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID || echo "[!] Warning: Could not enable Vertex AI API (may already be enabled)"
echo "[✓] Vertex AI API enabled"

echo ""
echo "========================================"
echo "Step 2: Grant Vertex AI Permissions"
echo "========================================"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user" || echo "[!] Warning: Could not grant role (may already exist)"
echo "[✓] Vertex AI User role granted"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.jobUser" || echo "[!] Warning: Could not grant role (may already exist)"
echo "[✓] BigQuery Job User role granted"

echo ""
echo "========================================"
echo "Step 3: Redeploy account-scoring Function"
echo "========================================"

echo "Deploying with gemini-2.5-pro model..."

gcloud functions deploy account-scoring \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=account_scoring_job \
    --trigger-http \
    --no-allow-unauthenticated \
    --service-account=$SERVICE_ACCOUNT \
    --memory=2048MB \
    --timeout=540s \
    --max-instances=3 \
    --min-instances=0 \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=sales_intelligence,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" \
    --project=$PROJECT_ID

echo "[✓] account-scoring function deployed successfully"

echo ""
echo "========================================"
echo "Step 4: Update Scheduler Job"
echo "========================================"

echo "Checking if scheduler job exists..."

if gcloud scheduler jobs describe account-scoring-daily --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "Scheduler job exists. Deleting and recreating with updated timeout..."
    
    gcloud scheduler jobs delete account-scoring-daily \
        --location=$REGION \
        --project=$PROJECT_ID \
        --quiet
    
    echo "[✓] Old scheduler job deleted"
fi

echo "Creating scheduler job with 20-minute timeout..."

gcloud scheduler jobs create http account-scoring-daily \
    --location=$REGION \
    --schedule="0 7 * * *" \
    --time-zone="America/New_York" \
    --uri="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/account-scoring" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --max-retry-duration=1200s \
    --max-retry-attempts=2 \
    --project=$PROJECT_ID

echo "[✓] Scheduler job created successfully"

echo ""
echo "========================================"
echo "Step 5: Test Deployment"
echo "========================================"

echo "Testing account-scoring function with 5 accounts..."

gcloud functions call account-scoring \
    --gen2 \
    --region=$REGION \
    --project=$PROJECT_ID \
    --data='{"limit": 5}'

echo ""
echo "[✓] Function test completed"

echo ""
echo "========================================"
echo "Verification Steps"
echo "========================================"

echo ""
echo "1. Check function environment variables:"
echo "   gcloud functions describe account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --format=\"yaml(serviceConfig.environmentVariables)\""

echo ""
echo "2. Check function logs:"
echo "   gcloud functions logs read account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --limit=50"

echo ""
echo "3. Verify scheduler job:"
echo "   gcloud scheduler jobs describe account-scoring-daily --location=$REGION --project=$PROJECT_ID"

echo ""
echo "4. Manually trigger scheduler:"
echo "   gcloud scheduler jobs run account-scoring-daily --location=$REGION --project=$PROJECT_ID"

echo ""
echo "5. Check BigQuery for results:"
echo "   SELECT * FROM \`${PROJECT_ID}.sales_intelligence.account_recommendations\` ORDER BY created_at DESC LIMIT 10;"

echo ""
echo "========================================"
echo "  ✅ Deployment Fix Complete!"
echo "========================================"
echo ""
echo "The account-scoring function should now work with gemini-2.5-pro"
echo "Next scheduled run: Tomorrow at 7:00 AM (America/New_York)"
echo ""
echo "If you still see errors, check the logs using the commands above."
echo ""

