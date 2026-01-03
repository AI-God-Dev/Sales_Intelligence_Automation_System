# Check BigQuery Data
# Displays row counts and recent data from BigQuery tables

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$datasetId = "sales_intelligence"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BigQuery Data Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$tables = @(
    "gmail_messages",
    "gmail_participants",
    "sf_accounts",
    "sf_contacts",
    "sf_leads",
    "sf_opportunities",
    "sf_activities",
    "dialpad_calls",
    "hubspot_sequences",
    "etl_runs"
)

Write-Host "Table Row Counts:" -ForegroundColor Yellow
Write-Host ""

foreach ($table in $tables) {
    $query = "SELECT COUNT(*) as row_count FROM \`$projectId.$datasetId.$table\`"
    $result = bq query --use_legacy_sql=false --format=csv --project_id=$projectId $query 2>$null | Select-Object -Skip 1
    if ($LASTEXITCODE -eq 0 -and $result) {
        Write-Host "  $table : $result rows" -ForegroundColor Green
    } else {
        Write-Host "  $table : Error querying" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Recent ETL Runs:" -ForegroundColor Yellow
$etlQuery = "SELECT source_system, job_type, status, rows_processed, started_at FROM \`$projectId.$datasetId.etl_runs\` ORDER BY started_at DESC LIMIT 10"
bq query --use_legacy_sql=false --format=prettyjson --project_id=$projectId $etlQuery 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "To query specific tables, use:" -ForegroundColor Yellow
Write-Host "bq query --use_legacy_sql=false --project_id=$projectId \"SELECT * FROM \`$projectId.$datasetId.TABLE_NAME LIMIT 10\"" -ForegroundColor White
Write-Host ""

