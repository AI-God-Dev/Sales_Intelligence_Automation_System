# Check if data ingestion was successful
# PowerShell version

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$DATASET_ID = "sales_intelligence"
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Checking Ingestion Status" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Dataset: $DATASET_ID" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check ETL Runs Table
Write-Host "📊 Latest ETL Runs Status:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$etlQuery = @"
SELECT 
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
LIMIT 10
"@

$etlResult = bq query --use_legacy_sql=false --format=prettyjson --project_id=$PROJECT_ID $etlQuery 2>$null
if ($etlResult) {
    Write-Host $etlResult
} else {
    Write-Host "  ⚠️  ETL runs table not found or empty" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# Check Row Counts
Write-Host "📈 Data Row Counts by Source:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Gmail
$gmailCount = (bq query --use_legacy_sql=false --format=csv --quiet --project_id=$PROJECT_ID "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.gmail_messages\`" 2>$null | Select-Object -Last 1)
Write-Host "Gmail Messages: $gmailCount"

# Salesforce Accounts
$sfAccounts = (bq query --use_legacy_sql=false --format=csv --quiet --project_id=$PROJECT_ID "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.sf_accounts\`" 2>$null | Select-Object -Last 1)
Write-Host "Salesforce Accounts: $sfAccounts"

# Salesforce Contacts
$sfContacts = (bq query --use_legacy_sql=false --format=csv --quiet --project_id=$PROJECT_ID "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.sf_contacts\`" 2>$null | Select-Object -Last 1)
Write-Host "Salesforce Contacts: $sfContacts"

# Dialpad
$dialpadCount = (bq query --use_legacy_sql=false --format=csv --quiet --project_id=$PROJECT_ID "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.dialpad_calls\`" 2>$null | Select-Object -Last 1)
Write-Host "Dialpad Calls: $dialpadCount"

# HubSpot
$hubspotCount = (bq query --use_legacy_sql=false --format=csv --quiet --project_id=$PROJECT_ID "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$DATASET_ID.hubspot_sequences\`" 2>$null | Select-Object -Last 1)
Write-Host "HubSpot Sequences: $hubspotCount"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Status Check Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - Check ETL runs table for job status"
Write-Host "   - Row counts > 0 means data was ingested"
Write-Host "   - Recent ingested_at timestamps show fresh data"
Write-Host "==========================================" -ForegroundColor Cyan

