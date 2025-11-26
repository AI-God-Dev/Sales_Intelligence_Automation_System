# Check BigQuery table row counts
$project = "maharani-sales-hub-11-2025"
$dataset = "sales_intelligence"

Write-Host "=== Checking BigQuery Table Row Counts ===" -ForegroundColor Cyan

# Dialpad calls
Write-Host "`nChecking dialpad_calls..." -ForegroundColor Yellow
$dialpadQuery = "SELECT COUNT(*) as total FROM ``$project.$dataset.dialpad_calls``"
$dialpadResult = bq query --project_id=$project --use_legacy_sql=false --format=json $dialpadQuery 2>&1
if ($LASTEXITCODE -eq 0) {
    $dialpadData = $dialpadResult | ConvertFrom-Json
    Write-Host "Dialpad calls: $($dialpadData[0].total)" -ForegroundColor Green
} else {
    Write-Host "Error querying dialpad_calls: $dialpadResult" -ForegroundColor Red
}

# Salesforce contacts
Write-Host "`nChecking sf_contacts..." -ForegroundColor Yellow
$sfQuery = "SELECT COUNT(*) as total FROM ``$project.$dataset.sf_contacts``"
$sfResult = bq query --project_id=$project --use_legacy_sql=false --format=json $sfQuery 2>&1
if ($LASTEXITCODE -eq 0) {
    $sfData = $sfResult | ConvertFrom-Json
    Write-Host "Salesforce contacts: $($sfData[0].total)" -ForegroundColor Green
} else {
    Write-Host "Error querying sf_contacts: $sfResult" -ForegroundColor Red
}

# Salesforce accounts
Write-Host "`nChecking sf_accounts..." -ForegroundColor Yellow
$sfAccQuery = "SELECT COUNT(*) as total FROM ``$project.$dataset.sf_accounts``"
$sfAccResult = bq query --project_id=$project --use_legacy_sql=false --format=json $sfAccQuery 2>&1
if ($LASTEXITCODE -eq 0) {
    $sfAccData = $sfAccResult | ConvertFrom-Json
    Write-Host "Salesforce accounts: $($sfAccData[0].total)" -ForegroundColor Green
} else {
    Write-Host "Error querying sf_accounts: $sfAccResult" -ForegroundColor Red
}

# HubSpot sequences
Write-Host "`nChecking hubspot_sequences..." -ForegroundColor Yellow
$hsQuery = "SELECT COUNT(*) as total FROM ``$project.$dataset.hubspot_sequences``"
$hsResult = bq query --project_id=$project --use_legacy_sql=false --format=json $hsQuery 2>&1
if ($LASTEXITCODE -eq 0) {
    $hsData = $hsResult | ConvertFrom-Json
    Write-Host "HubSpot sequences: $($hsData[0].total)" -ForegroundColor Green
} else {
    Write-Host "Error querying hubspot_sequences: $hsResult" -ForegroundColor Red
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan

