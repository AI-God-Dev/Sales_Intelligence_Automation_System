# ============================================================================
# BIGQUERY DATASET AND TABLES SETUP SCRIPT
# ============================================================================
# Creates BigQuery dataset and all required tables for the
# Sales Intelligence Automation System
#
# Usage:
#   .\scripts\create_bigquery_datasets.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURATION
# ============================================================================
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "YOUR_PROJECT_ID" }
$DATASET_ID = if ($env:BQ_DATASET_NAME) { $env:BQ_DATASET_NAME } elseif ($env:BIGQUERY_DATASET) { $env:BIGQUERY_DATASET } else { "sales_intelligence" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

# Validate configuration
if ($PROJECT_ID -eq "YOUR_PROJECT_ID" -or -not $PROJECT_ID) {
    Write-Host "[ERROR] GCP_PROJECT_ID not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:GCP_PROJECT_ID = 'your-project-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BigQuery Dataset and Tables Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Dataset ID: $DATASET_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# STEP 1: CREATE DATASET
# ============================================================================

Write-Host "Step 1: Creating BigQuery dataset..." -ForegroundColor Yellow

# Check if dataset exists
$existing = bq show --project_id=$PROJECT_ID "${PROJECT_ID}:${DATASET_ID}" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [✓] Dataset already exists: $DATASET_ID" -ForegroundColor Green
} else {
    # Create dataset
    bq mk --dataset `
        --location=$REGION `
        --description="Sales Intelligence data warehouse" `
        --project_id=$PROJECT_ID `
        $DATASET_ID
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [✓] Dataset created successfully" -ForegroundColor Green
    } else {
        Write-Host "  [✗] Failed to create dataset" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# STEP 2: PREPARE SQL FILE
# ============================================================================

Write-Host ""
Write-Host "Step 2: Preparing SQL file..." -ForegroundColor Yellow

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$sqlFile = Join-Path $projectRoot "bigquery\schemas\create_tables.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "  [✗] SQL file not found at: $sqlFile" -ForegroundColor Red
    exit 1
}

# Create temporary SQL file with project ID replaced
$tempSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlContent = Get-Content $sqlFile -Raw

# Replace project ID placeholders (handle both {project_id} and hardcoded project IDs)
# First, try to replace common placeholder patterns
$sqlContent = $sqlContent -replace '\{project_id\}', $PROJECT_ID
$sqlContent = $sqlContent -replace 'maharani-sales-hub-11-2025', $PROJECT_ID

# Write to temp file
Set-Content -Path $tempSqlFile -Value $sqlContent -NoNewline

Write-Host "  [✓] SQL file prepared: $tempSqlFile" -ForegroundColor Green

# ============================================================================
# STEP 3: CREATE TABLES
# ============================================================================

Write-Host ""
Write-Host "Step 3: Creating tables from SQL file..." -ForegroundColor Yellow

try {
    # Read SQL file and execute queries
    # BigQuery CLI may have issues with large SQL files, so we'll execute directly
    bq query --use_legacy_sql=false --project_id=$PROJECT_ID --format=prettyjson < $tempSqlFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [✓] Tables created successfully" -ForegroundColor Green
    } else {
        Write-Host "  [⚠] Some tables may have failed to create (they may already exist)" -ForegroundColor Yellow
        Write-Host "      This is normal if running the script multiple times" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [⚠] Error executing SQL: $_" -ForegroundColor Yellow
    Write-Host "      You may need to run the SQL file manually in BigQuery Console" -ForegroundColor Yellow
}

# ============================================================================
# STEP 4: VERIFY TABLES
# ============================================================================

Write-Host ""
Write-Host "Step 4: Verifying tables..." -ForegroundColor Yellow

try {
    $tables = bq ls --project_id=$PROJECT_ID --format=json $DATASET_ID | ConvertFrom-Json
    
    if ($tables) {
        Write-Host "  [✓] Found $($tables.Count) table(s) in dataset:" -ForegroundColor Green
        foreach ($table in $tables) {
            $tableId = if ($table.tableReference.tableId) { $table.tableReference.tableId } else { $table.id }
            Write-Host "      - $tableId" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [⚠] No tables found. Please check the SQL file execution." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [⚠] Could not list tables: $_" -ForegroundColor Yellow
}

# Cleanup temp file
Remove-Item $tempSqlFile -ErrorAction SilentlyContinue

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BigQuery Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dataset: ${PROJECT_ID}.${DATASET_ID}" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Verify tables in BigQuery Console:" -ForegroundColor Yellow
Write-Host "     https://console.cloud.google.com/bigquery?project=$PROJECT_ID" -ForegroundColor Gray
Write-Host "  2. Create secrets in Secret Manager" -ForegroundColor Yellow
Write-Host "  3. Deploy Cloud Functions: .\scripts\deploy_all.ps1" -ForegroundColor Yellow
Write-Host ""
