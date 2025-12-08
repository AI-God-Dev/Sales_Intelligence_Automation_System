#!/bin/bash
# Fix Cloud Functions errors: environment variables, IAM permissions, and Secret Manager access
# Usage: ./scripts/fix_function_errors.sh

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-sales_intelligence}"
SERVICE_ACCOUNT="${SA_EMAIL:-sales-intelligence-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "=========================================="
echo "Fixing Cloud Functions Errors"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Dataset: $DATASET_NAME"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Functions to fix
FUNCTIONS=("gmail-sync" "salesforce-sync" "dialpad-sync" "hubspot-sync" "entity-resolution")

echo "Step 1: Updating environment variables..."
for func in "${FUNCTIONS[@]}"; do
    echo "  Updating $func..."
    # Get the Cloud Run service name for this Gen2 function
    SERVICE_NAME=$(gcloud functions describe "$func" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.service)" 2>/dev/null | sed 's/.*\///' || echo "")
    
    if [ -n "$SERVICE_NAME" ]; then
        # Update via Cloud Run service (faster)
        gcloud run services update "$SERVICE_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --update-env-vars="BQ_DATASET_NAME=$DATASET_NAME,GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
            --quiet && echo "    ✓ Updated via Cloud Run service" || {
            echo "    Trying function deploy method..."
            gcloud functions deploy "$func" \
                --gen2 \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --set-env-vars="BQ_DATASET_NAME=$DATASET_NAME,GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
                --quiet && echo "    ✓ Updated via function deploy" || echo "    ✗ Failed to update"
        }
    else
        # Fallback: Update via function deploy
        gcloud functions deploy "$func" \
            --gen2 \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --set-env-vars="BQ_DATASET_NAME=$DATASET_NAME,GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
            --quiet && echo "    ✓ Updated" || echo "    ✗ Failed to update"
    fi
done

echo ""
echo "Step 2: Granting IAM invoker permissions..."
for func in "${FUNCTIONS[@]}"; do
    echo "  Granting invoker permission for $func..."
    gcloud functions add-iam-policy-binding "$func" \
        --gen2 \
        --region="$REGION" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/cloudfunctions.invoker" \
        --project="$PROJECT_ID" \
        --quiet || echo "  Warning: Failed to grant permission for $func"
done

echo ""
echo "Step 3: Granting Secret Manager access..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet || echo "  Warning: Failed to grant Secret Manager access"

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 1-2 minutes for updates to propagate"
echo "2. Run: ./scripts/test_functions.sh"
echo ""

