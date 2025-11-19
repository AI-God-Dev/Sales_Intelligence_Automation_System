# BigQuery Dataset and Tables Setup Script
# Creates the sales_intelligence dataset and all required tables

$ErrorActionPreference = "Stop"

# Get configuration from environment variables or use defaults
$projectId = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$datasetId = if ($env:BIGQUERY_DATASET) { $env:BIGQUERY_DATASET } else { "sales_intelligence" }

# Validate required variables
if (-not $projectId) {
    Write-Host "[ERROR] GCP_PROJECT_ID environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:GCP_PROJECT_ID = 'your-project-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BigQuery Dataset and Tables Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Dataset: $datasetId" -ForegroundColor Yellow
Write-Host ""

# Step 1: Prepare SQL file (replace placeholders)
Write-Host "Step 1: Preparing SQL file..." -ForegroundColor Green
# Use cross-platform path handling
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$sqlFile = Join-Path $projectRoot "bigquery\schemas\create_tables.sql"
$sqlFileTemp = Join-Path $projectRoot "bigquery\schemas\create_tables_temp.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "ERROR: SQL file not found at $sqlFile" -ForegroundColor Red
    exit 1
}

$sqlContent = Get-Content $sqlFile -Raw
$sqlContent = $sqlContent -replace '\{project_id\}', $projectId
$sqlContent | Out-File -FilePath $sqlFileTemp -Encoding UTF8 -NoNewline

Write-Host "✓ SQL file prepared" -ForegroundColor Green
Write-Host ""

# Step 2: Create dataset
Write-Host "Step 2: Creating BigQuery dataset..." -ForegroundColor Green
$datasetExists = bq ls -d --project_id=$projectId $datasetId 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating dataset: $datasetId" -ForegroundColor Yellow
    bq mk --dataset --location=$region --project_id=$projectId $datasetId
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create dataset" -ForegroundColor Red
        Remove-Item $sqlFileTemp -ErrorAction SilentlyContinue
        exit 1
    }
    Write-Host "✓ Dataset created" -ForegroundColor Green
} else {
    Write-Host "✓ Dataset already exists" -ForegroundColor Green
}
Write-Host ""

# Step 3: Create tables from SQL file
Write-Host "Step 3: Creating tables from SQL file..." -ForegroundColor Green
bq query --use_legacy_sql=false --project_id=$projectId --format=prettyjson < $sqlFileTemp
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create tables" -ForegroundColor Red
    Remove-Item $sqlFileTemp -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "✓ Tables created successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Verify table creation
Write-Host "Step 4: Verifying table creation..." -ForegroundColor Green
$tables = @(
    "gmail_messages",
    "gmail_participants",
    "gmail_sync_state",
    "sf_accounts",
    "sf_contacts",
    "sf_leads",
    "sf_opportunities",
    "sf_activities",
    "dialpad_calls",
    "account_recommendations",
    "hubspot_sequences",
    "etl_runs",
    "manual_mappings"
)

$allTablesExist = $true
foreach ($table in $tables) {
    $tableExists = bq ls --project_id=$projectId "$datasetId.$table" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $table" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $table (MISSING)" -ForegroundColor Red
        $allTablesExist = $false
    }
}

# Verify view
Write-Host "Verifying view..." -ForegroundColor Yellow
$viewExists = bq ls --project_id=$projectId "$datasetId.v_unmatched_emails" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ v_unmatched_emails (view)" -ForegroundColor Green
} else {
    Write-Host "  ✗ v_unmatched_emails (MISSING)" -ForegroundColor Red
    $allTablesExist = $false
}

Write-Host ""

# Cleanup temp file
Remove-Item $sqlFileTemp -ErrorAction SilentlyContinue

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allTablesExist) {
    Write-Host "✓ BigQuery setup completed successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some tables may be missing. Check errors above." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

