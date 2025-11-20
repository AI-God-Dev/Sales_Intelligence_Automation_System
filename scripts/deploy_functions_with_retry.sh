#!/bin/bash
# Deploy Cloud Functions with retry logic for 409 conflicts
# IMPORTANT: Deploys from project root to include shared modules (utils, config, entity_resolution)

# Don't use set -e here, we need to handle errors manually for retries

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
    local deploy_output
    local exit_code
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        echo "Deploying $function_name (attempt $((retry_count + 1))/$MAX_RETRIES)..."
        
        # Capture output and exit code
        deploy_output=$(gcloud functions deploy "$function_name" \
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
            --project=$PROJECT_ID 2>&1)
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "✓ Successfully deployed $function_name"
            return 0
        else
            # Check if it's a 409 conflict error
            if echo "$deploy_output" | grep -q "409\|unable to queue\|already exists"; then
                echo "⚠ Conflict detected (409 error). Function may already exist or deployment in progress."
                
                # Check if function exists
                if gcloud functions describe "$function_name" --region=$REGION --project=$PROJECT_ID --gen2 >/dev/null 2>&1; then
                    echo "Function $function_name exists. Checking for active deployments..."
                    
                    # Wait for active builds to complete
                    local build_output
                    build_output=$(gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=1 --format="value(id)" 2>/dev/null)
                    local active_builds=$(echo "$build_output" | grep -v "^$" | wc -l)
                    
                    if [ "$active_builds" -gt 0 ]; then
                        echo "Active deployment in progress. Waiting $RETRY_DELAY seconds..."
                        sleep $RETRY_DELAY
                        retry_count=$((retry_count + 1))
                        continue
                    else
                        echo "⚠ No active builds found. This might be a temporary conflict."
                        if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
                            echo "Waiting $RETRY_DELAY seconds before retry..."
                            sleep $RETRY_DELAY
                            retry_count=$((retry_count + 1))
                            continue
                        else
                            echo "✗ Max retries reached for $function_name"
                            return 1
                        fi
                    fi
                else
                    echo "⚠ Function doesn't exist but deployment failed."
                    if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
                        echo "Waiting $RETRY_DELAY seconds before retry..."
                        sleep $RETRY_DELAY
                        retry_count=$((retry_count + 1))
                        continue
                    else
                        echo "✗ Failed to deploy $function_name after $MAX_RETRIES attempts"
                        echo "Error output: $deploy_output"
                        return 1
                    fi
                fi
            else
                echo "✗ Failed to deploy $function_name (exit code: $exit_code)"
                echo "Error: $deploy_output"
                if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
                    echo "Waiting $RETRY_DELAY seconds before retry..."
                    sleep $RETRY_DELAY
                    retry_count=$((retry_count + 1))
                    continue
                else
                    return 1
                fi
            fi
        fi
    done
    
    echo "✗ Failed to deploy $function_name after $MAX_RETRIES attempts"
    return 1
}

# Check for active deployments first
echo "Checking for active deployments..."
build_list_output=$(gcloud builds list --ongoing --project=$PROJECT_ID --region=$REGION --limit=1 --format="value(id)" 2>/dev/null || true)
ACTIVE_BUILDS=$(echo "$build_list_output" | grep -v "^$" | wc -l)

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
if ! deploy_function "gmail-sync" "gmail_sync"; then
    echo "⚠ Gmail sync deployment failed, continuing with other functions..."
fi

# Deploy Salesforce Sync Function
if ! deploy_function "salesforce-sync" "salesforce_sync"; then
    echo "⚠ Salesforce sync deployment failed, continuing with other functions..."
fi

# Deploy Dialpad Sync Function
if ! deploy_function "dialpad-sync" "dialpad_sync"; then
    echo "⚠ Dialpad sync deployment failed, continuing with other functions..."
fi

# Deploy HubSpot Sync Function
if ! deploy_function "hubspot-sync" "hubspot_sync"; then
    echo "⚠ HubSpot sync deployment failed, continuing with other functions..."
fi

# Deploy Entity Resolution Function
if ! deploy_function "entity-resolution" "entity_resolution"; then
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
