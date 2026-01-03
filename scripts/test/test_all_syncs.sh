#!/bin/bash
# Comprehensive test script to verify all syncs work with real-world data

set -e

PROJECT_ID="maharani-sales-hub-11-2025"
REGION="us-central1"

echo "========================================"
echo "Comprehensive Sync Verification Test"
echo "========================================"
echo ""

# Get auth token
echo "Getting authentication token..."
TOKEN=$(gcloud auth print-identity-token)
echo "✓ Token obtained"
echo ""

# Test 1: Salesforce Sync
echo "========================================"
echo "Test 1: Salesforce Sync"
echo "========================================"

SF_OBJECTS=("Account" "Contact" "Lead" "Opportunity")

for obj in "${SF_OBJECTS[@]}"; do
    echo ""
    echo "Syncing Salesforce $obj..."
    RESPONSE=$(curl -s -X POST "https://salesforce-sync-z455yfejea-uc.a.run.app" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"object_type\":\"$obj\",\"sync_type\":\"full\"}")
    
    STATUS=$(echo $RESPONSE | jq -r '.status // "unknown"')
    ROWS=$(echo $RESPONSE | jq -r '.rows_synced // 0')
    ERRORS=$(echo $RESPONSE | jq -r '.errors // 0')
    
    if [ "$STATUS" != "unknown" ]; then
        echo "✓ $obj sync completed"
        echo "  Status: $STATUS"
        echo "  Rows synced: $ROWS"
        if [ "$ERRORS" -gt 0 ]; then
            echo "  Errors: $ERRORS"
        fi
    else
        echo "✗ $obj sync failed"
        echo "$RESPONSE" | jq '.'
    fi
    
    sleep 2
done

# Test 2: Dialpad Sync
echo ""
echo "========================================"
echo "Test 2: Dialpad Sync"
echo "========================================"
echo ""

echo "Syncing Dialpad calls..."
RESPONSE=$(curl -s -X POST "https://dialpad-sync-z455yfejea-uc.a.run.app" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"sync_type":"full"}')

STATUS=$(echo $RESPONSE | jq -r '.status // "unknown"')
ROWS=$(echo $RESPONSE | jq -r '.rows_synced // 0')
ERRORS=$(echo $RESPONSE | jq -r '.errors // 0')

if [ "$STATUS" != "unknown" ]; then
    echo "✓ Dialpad sync completed"
    echo "  Status: $STATUS"
    echo "  Rows synced: $ROWS"
    if [ "$ERRORS" -gt 0 ]; then
        echo "  Errors: $ERRORS"
    fi
else
    echo "✗ Dialpad sync failed"
    echo "$RESPONSE" | jq '.'
fi

sleep 2

# Test 3: HubSpot Sync
echo ""
echo "========================================"
echo "Test 3: HubSpot Sync"
echo "========================================"
echo ""

echo "Syncing HubSpot sequences..."
RESPONSE=$(curl -s -X POST "https://hubspot-sync-z455yfejea-uc.a.run.app" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"sync_type":"full"}')

STATUS=$(echo $RESPONSE | jq -r '.status // "unknown"')
ROWS=$(echo $RESPONSE | jq -r '.rows_synced // 0')
ERRORS=$(echo $RESPONSE | jq -r '.errors // 0')

if [ "$STATUS" != "unknown" ]; then
    echo "✓ HubSpot sync completed"
    echo "  Status: $STATUS"
    echo "  Rows synced: $ROWS"
    if [ "$ERRORS" -gt 0 ]; then
        echo "  Errors: $ERRORS"
    fi
else
    echo "✗ HubSpot sync failed"
    echo "$RESPONSE" | jq '.'
fi

sleep 3

# Test 4: Verify BigQuery Data
echo ""
echo "========================================"
echo "Test 4: BigQuery Data Verification"
echo "========================================"
echo ""

declare -a TABLES=(
    "salesforce_accounts:Salesforce Accounts"
    "salesforce_contacts:Salesforce Contacts"
    "salesforce_leads:Salesforce Leads"
    "salesforce_opportunities:Salesforce Opportunities"
    "dialpad_calls:Dialpad Calls"
    "hubspot_sequences:HubSpot Sequences"
)

for table_info in "${TABLES[@]}"; do
    IFS=':' read -r table_name table_desc <<< "$table_info"
    echo "Checking $table_desc..."
    
    QUERY="SELECT COUNT(*) as total FROM \`$PROJECT_ID.sales_intelligence.$table_name\`"
    RESULT=$(bq query --use_legacy_sql=false --format=json "$QUERY" 2>&1)
    
    if [ $? -eq 0 ]; then
        COUNT=$(echo $RESULT | jq -r '.[0].total // 0')
        if [ "$COUNT" -gt 0 ]; then
            echo "✓ $table_desc: $COUNT rows"
        else
            echo "⚠ $table_desc: 0 rows (no data yet)"
        fi
    else
        echo "✗ Failed to query $table_name"
        echo "$RESULT"
    fi
done

echo ""
echo "========================================"
echo "Test Complete"
echo "========================================"

