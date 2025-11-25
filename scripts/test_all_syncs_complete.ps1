# Complete Sync Test and Verification Script
# Tests all sync functions and verifies data in BigQuery

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Sync Test & Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Redeploy all functions with latest fixes
Write-Host "Step 1: Redeploying Cloud Functions..." -ForegroundColor Yellow
$functions = @("gmail-sync", "salesforce-sync", "dialpad-sync", "hubspot-sync")
foreach ($func in $functions) {
    Write-Host "  Deploying $func..." -ForegroundColor Gray
    gcloud functions deploy $func --gen2 --region=$region --project=$projectId --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $func deployed" -ForegroundColor Green
    } else {
        Write-Host "    ✗ $func deployment failed" -ForegroundColor Red
    }
}
Write-Host ""

# Step 2: Test Gmail Sync
Write-Host "Step 2: Testing Gmail Sync..." -ForegroundColor Yellow
try {
    $response = gcloud functions call gmail-sync --gen2 --region=$region --data '{}' --project=$projectId 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Gmail sync triggered successfully" -ForegroundColor Green
        Start-Sleep -Seconds 5
    } else {
        Write-Host "  ✗ Gmail sync failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 3: Test Salesforce Sync (all objects)
Write-Host "Step 3: Testing Salesforce Sync..." -ForegroundColor Yellow
$sfObjects = @("Account", "Contact", "Lead", "Opportunity")
foreach ($obj in $sfObjects) {
    Write-Host "  Syncing $obj..." -ForegroundColor Gray
    try {
        $data = "{`"object_type`":`"$obj`",`"sync_type`":`"full`"}"
        $response = gcloud functions call salesforce-sync --gen2 --region=$region --data $data --project=$projectId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ $obj sync triggered" -ForegroundColor Green
        } else {
            Write-Host "    ✗ $obj sync failed" -ForegroundColor Red
        }
        Start-Sleep -Seconds 3
    } catch {
        Write-Host "    ✗ Error: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Step 4: Test Dialpad Sync
Write-Host "Step 4: Testing Dialpad Sync..." -ForegroundColor Yellow
try {
    $response = gcloud functions call dialpad-sync --gen2 --region=$region --data '{"sync_type":"full"}' --project=$projectId 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Dialpad sync triggered successfully" -ForegroundColor Green
        Start-Sleep -Seconds 5
    } else {
        Write-Host "  ✗ Dialpad sync failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 5: Test HubSpot Sync
Write-Host "Step 5: Testing HubSpot Sync..." -ForegroundColor Yellow
try {
    $response = gcloud functions call hubspot-sync --gen2 --region=$region --data '{}' --project=$projectId 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ HubSpot sync triggered successfully" -ForegroundColor Green
        Start-Sleep -Seconds 3
    } else {
        Write-Host "  ✗ HubSpot sync failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 6: Wait for syncs to complete
Write-Host "Step 6: Waiting for syncs to complete (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host ""

# Step 7: Check BigQuery Data
Write-Host "Step 7: Verifying BigQuery Data..." -ForegroundColor Yellow
$tables = @{
    "gmail_messages" = "Gmail Messages"
    "gmail_participants" = "Gmail Participants"
    "sf_accounts" = "Salesforce Accounts"
    "sf_contacts" = "Salesforce Contacts"
    "sf_leads" = "Salesforce Leads"
    "sf_opportunities" = "Salesforce Opportunities"
    "dialpad_calls" = "Dialpad Calls"
    "hubspot_sequences" = "HubSpot Sequences"
}

foreach ($table in $tables.Keys) {
    $query = "SELECT COUNT(*) as row_count FROM \`$projectId.sales_intelligence.$table\`"
    $result = bq query --use_legacy_sql=false --format=csv --project_id=$projectId $query 2>$null | Select-Object -Skip 1
    if ($LASTEXITCODE -eq 0 -and $result) {
        $count = [int]$result
        if ($count -gt 0) {
            Write-Host "  ✓ $($tables[$table]): $count rows" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ $($tables[$table]): 0 rows (no data yet)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✗ $($tables[$table]): Error querying" -ForegroundColor Red
    }
}
Write-Host ""

# Step 8: Check ETL Runs
Write-Host "Step 8: Checking Recent ETL Runs..." -ForegroundColor Yellow
$etlQuery = "SELECT source_system, job_type, status, rows_processed, rows_failed, started_at FROM \`$projectId.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"
$etlResults = bq query --use_legacy_sql=false --format=json --project_id=$projectId $etlQuery 2>$null
if ($LASTEXITCODE -eq 0) {
    $etlData = $etlResults | ConvertFrom-Json
    foreach ($run in $etlData) {
        $statusColor = if ($run.status -eq "success") { "Green" } elseif ($run.status -eq "partial") { "Yellow" } else { "Red" }
        Write-Host "  $($run.source_system) - $($run.job_type) - $($run.status) - $($run.rows_processed) rows" -ForegroundColor $statusColor
    }
} else {
    Write-Host "  ✗ Error querying ETL runs" -ForegroundColor Red
}
Write-Host ""

# Step 9: Check Function Logs for Errors
Write-Host "Step 9: Checking Recent Logs for Errors..." -ForegroundColor Yellow
foreach ($func in $functions) {
    $logs = gcloud functions logs read $func --gen2 --region=$region --limit=5 --project=$projectId 2>&1
    $errorLogs = $logs | Select-String -Pattern "ERROR|Error|error|Failed|failed"
    if ($errorLogs) {
        Write-Host "  ⚠ $func has errors in recent logs" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ $func logs look clean" -ForegroundColor Green
    }
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review BigQuery data: .\scripts\check_bigquery.ps1" -ForegroundColor White
Write-Host "2. Check detailed logs: .\scripts\check_logs.ps1" -ForegroundColor White
Write-Host "3. View ETL runs in BigQuery console" -ForegroundColor White
Write-Host ""

