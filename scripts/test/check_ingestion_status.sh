#!/bin/bash
# Check if data ingestion was successful
# Verifies data in BigQuery tables and ETL run status

PROJECT_ID="${GCP_PROJECT_ID:-maharani-sales-hub-11-2025}"
DATASET_ID="sales_intelligence"
REGION="${GCP_REGION:-us-central1}"

echo "=========================================="
echo "Checking Ingestion Status"
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET_ID"
echo "=========================================="
echo ""

# Check ETL Runs Table (most reliable indicator)
echo "📊 Latest ETL Runs Status:"
echo "----------------------------------------"
bq query --use_legacy_sql=false --format=prettyjson \
    --project_id=$PROJECT_ID \
    "SELECT 
        source_system,
        job_type,
        status,
        rows_processed,
        rows_failed,
        started_at,
        completed_at,
        TIMESTAMP_DIFF(completed_at, started_at, SECOND) as duration_seconds
    FROM \`$PROJECT_ID.$DATASET_ID.etl_runs\`
    ORDER BY started_at DESC
    LIMIT 10" 2>/dev/null || echo "  ⚠️  ETL runs table not found or empty"

echo ""
echo "----------------------------------------"
echo ""

# Check Row Counts in Each Table
echo "📈 Data Row Counts by Source:"
echo "----------------------------------------"

# Gmail
GMAIL_COUNT=$(bq query --use_legacy_sql=false --format=csv --quiet \
    --project_id=$PROJECT_ID \
    "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.gmail_messages\`" 2>/dev/null | tail -n1)
echo "Gmail Messages: ${GMAIL_COUNT:-0}"

# Salesforce Accounts
SF_ACCOUNTS=$(bq query --use_legacy_sql=false --format=csv --quiet \
    --project_id=$PROJECT_ID \
    "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.sf_accounts\`" 2>/dev/null | tail -n1)
echo "Salesforce Accounts: ${SF_ACCOUNTS:-0}"

# Salesforce Contacts
SF_CONTACTS=$(bq query --use_legacy_sql=false --format=csv --quiet \
    --project_id=$PROJECT_ID \
    "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.sf_contacts\`" 2>/dev/null | tail -n1)
echo "Salesforce Contacts: ${SF_CONTACTS:-0}"

# Dialpad Calls
DIALPAD_COUNT=$(bq query --use_legacy_sql=false --format=csv --quiet \
    --project_id=$PROJECT_ID \
    "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.dialpad_calls\`" 2>/dev/null | tail -n1)
echo "Dialpad Calls: ${DIALPAD_COUNT:-0}"

# HubSpot Sequences
HUBSPOT_COUNT=$(bq query --use_legacy_sql=false --format=csv --quiet \
    --project_id=$PROJECT_ID \
    "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.hubspot_sequences\`" 2>/dev/null | tail -n1)
echo "HubSpot Sequences: ${HUBSPOT_COUNT:-0}"

echo ""
echo "----------------------------------------"
echo ""

# Check Recent Ingestion Timestamps
echo "⏰ Most Recent Data Ingestion Times:"
echo "----------------------------------------"
bq query --use_legacy_sql=false --format=prettyjson \
    --project_id=$PROJECT_ID \
    "SELECT 
        'gmail_messages' as table_name,
        MAX(ingested_at) as last_ingested,
        COUNT(*) as total_rows
    FROM \`$PROJECT_ID.$DATASET_ID.gmail_messages\`
    UNION ALL
    SELECT 
        'sf_accounts' as table_name,
        MAX(ingested_at) as last_ingested,
        COUNT(*) as total_rows
    FROM \`$PROJECT_ID.$DATASET_ID.sf_accounts\`
    UNION ALL
    SELECT 
        'sf_contacts' as table_name,
        MAX(ingested_at) as last_ingested,
        COUNT(*) as total_rows
    FROM \`$PROJECT_ID.$DATASET_ID.sf_contacts\`
    UNION ALL
    SELECT 
        'dialpad_calls' as table_name,
        MAX(ingested_at) as last_ingested,
        COUNT(*) as total_rows
    FROM \`$PROJECT_ID.$DATASET_ID.dialpad_calls\`
    ORDER BY last_ingested DESC" 2>/dev/null || echo "  ⚠️  Could not query recent ingestion times"

echo ""
echo "=========================================="
echo "✅ Status Check Complete!"
echo ""
echo "💡 Tips:"
echo "   - Check ETL runs table for job status"
echo "   - Row counts > 0 means data was ingested"
echo "   - Recent ingested_at timestamps show fresh data"
echo "=========================================="

