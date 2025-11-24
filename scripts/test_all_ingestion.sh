#!/bin/bash
# Test all ingestion sources
# Quick verification script for client

set -e

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
REGION="${GCP_REGION:-us-central1}"

echo "=========================================="
echo "Testing All Ingestion Sources"
echo "=========================================="
echo ""

# Function to trigger and check
test_sync() {
    local function_name=$1
    local display_name=$2
    
    echo "Testing $display_name..."
    echo "----------------------------------------"
    
    TOKEN=$(gcloud auth print-access-token)
    URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${function_name}"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "$URL" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"sync_type":"full"}' 2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "202" ]; then
        echo "✓ $display_name triggered successfully (HTTP $HTTP_CODE)"
    else
        echo "✗ $display_name failed (HTTP $HTTP_CODE)"
        echo "Response: $(echo "$RESPONSE" | sed '$d')"
    fi
    echo ""
}

# Test each sync
test_sync "gmail-sync" "Gmail Sync"
test_sync "salesforce-sync" "Salesforce Sync"
test_sync "dialpad-sync" "Dialpad Sync"
test_sync "hubspot-sync" "HubSpot Sync"

echo "=========================================="
echo "Check BigQuery for data:"
echo "=========================================="
echo ""
echo "bq query \"SELECT COUNT(*) FROM sales_intelligence.gmail_messages\""
echo "bq query \"SELECT COUNT(*) FROM sales_intelligence.sf_accounts\""
echo "bq query \"SELECT COUNT(*) FROM sales_intelligence.dialpad_calls\""
echo "bq query \"SELECT COUNT(*) FROM sales_intelligence.hubspot_sequences\""
echo ""

