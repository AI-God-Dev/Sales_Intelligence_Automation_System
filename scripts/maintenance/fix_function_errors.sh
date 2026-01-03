#!/bin/bash
# Fix Cloud Functions errors: environment variables, IAM permissions, and Secret Manager access
# Usage: ./scripts/fix_function_errors.sh

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
DATASET_NAME="${BQ_DATASET_NAME:-sales_intelligence}"

# Use the correct service account
SERVICE_ACCOUNT="sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

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
echo "Step 2: Checking service account..."
echo "  Function service account: $SERVICE_ACCOUNT"
# Check if service account exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Service account exists"
else
    echo "  ✗ Service account does not exist"
    echo "  Creating service account: $SERVICE_ACCOUNT"
    SA_NAME=$(echo "$SERVICE_ACCOUNT" | cut -d'@' -f1)
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="Sales Intelligence Service Account" \
        --project="$PROJECT_ID" \
        --quiet && echo "  ✓ Created service account" || echo "  ✗ Failed to create service account"
fi

echo ""
echo "Step 3: Granting IAM invoker permissions on Cloud Run services..."
# Get current user's email for invoker permission
CURRENT_USER=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -n "$CURRENT_USER" ]; then
    echo "  Current user: $CURRENT_USER"
fi

for func in "${FUNCTIONS[@]}"; do
    echo "  Granting invoker permission for $func..."
    # Get the Cloud Run service name for this Gen2 function
    SERVICE_NAME=$(gcloud functions describe "$func" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.service)" 2>/dev/null | sed 's/.*\///' || echo "")
    
    if [ -n "$SERVICE_NAME" ]; then
        # Grant permission to current user (for testing)
        if [ -n "$CURRENT_USER" ]; then
            gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
                --region="$REGION" \
                --member="user:$CURRENT_USER" \
                --role="roles/run.invoker" \
                --project="$PROJECT_ID" \
                --quiet && echo "    ✓ Granted invoker permission to user" || echo "    ⚠ Could not grant to user (may already have permission)"
        fi
        
        # Also grant to function's service account (for self-invocation if needed)
        gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
            --region="$REGION" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/run.invoker" \
            --project="$PROJECT_ID" \
            --quiet && echo "    ✓ Granted invoker permission to service account" || echo "    ⚠ Could not grant to service account (may already have permission)"
    else
        echo "    ✗ Could not find Cloud Run service for $func"
    fi
done

echo ""
echo "Step 4: Granting Secret Manager access to function service account..."
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet && echo "  ✓ Granted Secret Manager access" || echo "  ⚠ Could not grant (may already have permission)"
else
    echo "  ✗ Service account $SERVICE_ACCOUNT does not exist"
    echo "  Please create it or update functions to use an existing service account"
fi

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 1-2 minutes for updates to propagate"
echo "2. Run: ./scripts/test_functions.sh"
echo ""

