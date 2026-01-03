#!/bin/bash
# Run all data ingestion syncs in sequence
# Run this after Gmail sync completes

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "=========================================="
echo "Running All Data Ingestion Syncs"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=========================================="
echo ""

# Get identity token
TOKEN=$(gcloud auth print-identity-token)
if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get identity token. Please run: gcloud auth login"
    exit 1
fi

BASE_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net"

# Function to trigger a sync and check response
trigger_sync() {
    local FUNCTION_NAME=$1
    local DATA=$2
    local DESCRIPTION=$3
    
    echo "🔄 Triggering $DESCRIPTION..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "${BASE_URL}/${FUNCTION_NAME}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$DATA")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "202" ]; then
        echo "  ✅ Successfully triggered $FUNCTION_NAME (HTTP $HTTP_CODE)"
        echo "  Response: $BODY"
        return 0
    else
        echo "  ❌ Failed to trigger $FUNCTION_NAME (HTTP $HTTP_CODE)"
        echo "  Response: $BODY"
        return 1
    fi
    echo ""
}

# Step 1: Salesforce Sync (Accounts first, then other objects)
echo "📊 Step 1: Salesforce Sync"
echo "----------------------------------------"

# Sync Accounts
trigger_sync "salesforce-sync" '{"sync_type":"full","object_type":"Account"}' "Salesforce Accounts sync"
sleep 5

# Sync Contacts
trigger_sync "salesforce-sync" '{"sync_type":"full","object_type":"Contact"}' "Salesforce Contacts sync"
sleep 5

# Sync Leads
trigger_sync "salesforce-sync" '{"sync_type":"full","object_type":"Lead"}' "Salesforce Leads sync"
sleep 5

# Sync Opportunities
trigger_sync "salesforce-sync" '{"sync_type":"full","object_type":"Opportunity"}' "Salesforce Opportunities sync"
sleep 5

echo ""
echo "📞 Step 2: Dialpad Sync"
echo "----------------------------------------"
trigger_sync "dialpad-sync" '{"sync_type":"incremental"}' "Dialpad call logs sync"
sleep 5

echo ""
echo "📧 Step 3: HubSpot Sync"
echo "----------------------------------------"
trigger_sync "hubspot-sync" '{"sync_type":"full"}' "HubSpot sequences sync"
sleep 5

echo ""
echo "🔄 Step 4: Entity Resolution (optional - matches emails/phones to Salesforce)"
echo "----------------------------------------"
trigger_sync "entity-resolution" '{}' "Entity resolution and matching"

echo ""
echo "=========================================="
echo "✅ All syncs triggered!"
echo ""
echo "⏳ Waiting 2 minutes for initial processing..."
sleep 120

echo ""
echo "📊 Checking ingestion status..."
bash scripts/check_ingestion_status.sh

echo ""
echo "=========================================="
echo "✅ Complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Check BigQuery tables for data"
echo "   2. Verify ETL runs table for job status"
echo "   3. Check logs if any syncs failed"
echo "=========================================="

