#!/bin/bash
# Manually trigger Cloud Functions with proper authentication
# This script uses your user account to invoke the functions

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "Triggering initial full syncs..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Get access token for current user
TOKEN=$(gcloud auth print-access-token)
if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get access token. Please run: gcloud auth login"
    exit 1
fi

# Function to trigger a Cloud Function
trigger_function() {
    local FUNCTION_NAME=$1
    local DATA=$2
    local DESCRIPTION=$3
    
    echo "Triggering $DESCRIPTION..."
    
    # Use Cloud Run format for Gen2 functions
    # Gen2 functions are actually Cloud Run services
    local URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
    
    local RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "$URL" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$DATA")
    
    local HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    local BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "202" ]; then
        echo "  ✓ Successfully triggered $FUNCTION_NAME (HTTP $HTTP_CODE)"
        echo "  Response: $BODY"
    else
        echo "  ✗ Failed to trigger $FUNCTION_NAME (HTTP $HTTP_CODE)"
        echo "  Response: $BODY"
    fi
    echo ""
}

# Trigger Gmail Full Sync
trigger_function "gmail-sync" '{"sync_type":"full"}' "Gmail full sync"

# Trigger Salesforce Full Sync
trigger_function "salesforce-sync" '{"sync_type":"full","object_type":"Account"}' "Salesforce full sync"

# Trigger Dialpad Sync
trigger_function "dialpad-sync" '{"sync_type":"incremental"}' "Dialpad sync"

# Trigger HubSpot Sync
trigger_function "hubspot-sync" '{"sync_type":"full"}' "HubSpot sync"

echo "All syncs triggered. Waiting 2 minutes for processing..."
sleep 120

echo "Done!"

