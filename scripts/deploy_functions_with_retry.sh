#!/bin/bash
# Deploy Cloud Functions with retry logic for 409 conflicts
# IMPORTANT: Deploys from project root to include shared modules (utils, config, entity_resolution)

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT="sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com"
MAX_RETRIES=3
RETRY_DELAY=30

echo "Deploying Cloud Functions to project: $PROJECT_ID"
echo "Using service account: $SERVICE_ACCOUNT"
echo "Note: Deploying from project root to include shared modules"
echo ""

# Get project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Function to deploy a single Cloud Function with retry logic
deploy_function() {
    local function_name=$1
    local entry_point=$2
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        echo "Deploying $function_name (attempt $((retry_count + 1))/$MAX_RETRIES)..."
        
        if gcloud functions deploy "$function_name" \
            --gen2 \
            --runtime=python311 \
            --region=$REGION \
            --source=. \
            --entry-point="$entry_point" \
            --trigger-http \
            --service-account=$SERVICE_ACCOUNT \
            --memory=512MB \
            --timeout=540s \
            --max-instances=10 \
            --min-instances=0 \
            --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
            --project=$PROJECT_ID 2>&1; then
            
            echo "✓ Successfully deployed $function_name"
            return 0
        else
            local exit_code=$?
            if [ $exit_code -ne 0 ]; then
                # Check if it's a 409 error
                if gcloud functions describe "$function_name" --region=$REGION --project=$PROJECT_ID --gen2 >/dev/null 2>&1; then
                    echo "⚠ Function $function_name exists but deployment failed."
                    echo "Checking if there's an active deployment..."
                    
                    # Wait for active builds to complete
                    local active_builds=$(gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=1 --format="value(id)" 2>/dev/null | wc -l)
                    if [ "$active_builds" -gt 0 ]; then
                        echo "Active deployment in progress. Waiting $RETRY_DELAY seconds..."
                        sleep $RETRY_DELAY
                        retry_count=$((retry_count + 1))
                        continue
                    else
                        echo "⚠ No active builds found. Trying to continue with other functions..."
                        return 1
                    fi
                else
                    echo "✗ Failed to deploy $function_name (exit code: $exit_code)"
                    if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
                        echo "Waiting $RETRY_DELAY seconds before retry..."
                        sleep $RETRY_DELAY
                    fi
                    retry_count=$((retry_count + 1))
                fi
            fi
        fi
    done
    
    echo "✗ Failed to deploy $function_name after $MAX_RETRIES attempts"
    return 1
}

# Check for active deployments first
echo "Checking for active deployments..."
ACTIVE_BUILDS=$(gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=1 --format="value(id)" 2>/dev/null | wc -l)

if [ "$ACTIVE_BUILDS" -gt 0 ]; then
    echo "⚠ Warning: Active Cloud Build operations detected!"
    echo "Please wait for current deployments to complete before proceeding."
    echo ""
    echo "To check status, run:"
    echo "  bash scripts/check_deployment_status.sh"
    echo ""
    echo "Or wait and retry this script later."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

echo ""

# Deploy Gmail Sync Function
if ! deploy_function "gmail-sync" "cloud_functions.gmail_sync.main.gmail_sync"; then
    echo "⚠ Gmail sync deployment failed, continuing with other functions..."
fi

# Deploy Salesforce Sync Function
if ! deploy_function "salesforce-sync" "cloud_functions.salesforce_sync.main.salesforce_sync"; then
    echo "⚠ Salesforce sync deployment failed, continuing with other functions..."
fi

# Deploy Dialpad Sync Function
if ! deploy_function "dialpad-sync" "cloud_functions.dialpad_sync.main.dialpad_sync"; then
    echo "⚠ Dialpad sync deployment failed, continuing with other functions..."
fi

# Deploy HubSpot Sync Function
if ! deploy_function "hubspot-sync" "cloud_functions.hubspot_sync.main.hubspot_sync"; then
    echo "⚠ HubSpot sync deployment failed, continuing with other functions..."
fi

# Deploy Entity Resolution Function
if ! deploy_function "entity-resolution" "cloud_functions.entity_resolution.main.entity_resolution"; then
    echo "⚠ Entity resolution deployment failed"
fi

echo ""
echo "Granting Cloud Scheduler permission to invoke functions..."
gcloud functions add-iam-policy-binding gmail-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠ Could not update IAM policy for gmail-sync"

gcloud functions add-iam-policy-binding salesforce-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠ Could not update IAM policy for salesforce-sync"

gcloud functions add-iam-policy-binding dialpad-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠ Could not update IAM policy for dialpad-sync"

gcloud functions add-iam-policy-binding hubspot-sync \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠ Could not update IAM policy for hubspot-sync"

gcloud functions add-iam-policy-binding entity-resolution \
  --region=$REGION \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.invoker" \
  --project=$PROJECT_ID 2>/dev/null || echo "⚠ Could not update IAM policy for entity-resolution"

echo ""
echo "Deployment process complete!"
echo ""
echo "To check deployment status, run:"
echo "  bash scripts/check_deployment_status.sh"
