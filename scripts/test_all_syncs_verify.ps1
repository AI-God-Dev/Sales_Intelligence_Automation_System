# Comprehensive test script to verify all syncs work with real-world data
$ErrorActionPreference = "Continue"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comprehensive Sync Verification Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get auth token
Write-Host "Getting authentication token..." -ForegroundColor Yellow
try {
    $token = gcloud auth print-identity-token
    Write-Host "✓ Token obtained" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to get token: $_" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Test 1: Salesforce Sync
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test 1: Salesforce Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$sfObjects = @("Account", "Contact", "Lead", "Opportunity")
$sfResults = @{}

foreach ($obj in $sfObjects) {
    Write-Host ""
    Write-Host "Syncing Salesforce $obj..." -ForegroundColor Yellow
    $body = @{
        object_type = $obj
        sync_type = "full"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://salesforce-sync-z455yfejea-uc.a.run.app" -Method Post -Headers $headers -Body $body -ErrorAction Stop
        $sfResults[$obj] = $response
        Write-Host "✓ $obj sync completed" -ForegroundColor Green
        Write-Host "  Status: $($response.status)" -ForegroundColor Gray
        if ($response.rows_synced) {
            Write-Host "  Rows synced: $($response.rows_synced)" -ForegroundColor Gray
        }
        if ($response.errors -and $response.errors -gt 0) {
            Write-Host "  Errors: $($response.errors)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ $obj sync failed: $($_.Exception.Message)" -ForegroundColor Red
        $sfResults[$obj] = @{error = $_.Exception.Message}
    }
    
    Start-Sleep -Seconds 2
}

# Test 2: Dialpad Sync
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test 2: Dialpad Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Syncing Dialpad calls..." -ForegroundColor Yellow
$body = '{"sync_type":"full"}'

try {
    $response = Invoke-RestMethod -Uri "https://dialpad-sync-z455yfejea-uc.a.run.app" -Method Post -Headers $headers -Body $body -ErrorAction Stop
    Write-Host "✓ Dialpad sync completed" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
    if ($response.rows_synced) {
        Write-Host "  Rows synced: $($response.rows_synced)" -ForegroundColor Gray
    }
    if ($response.errors -and $response.errors -gt 0) {
        Write-Host "  Errors: $($response.errors)" -ForegroundColor Yellow
    }
    $dialpadResult = $response
} catch {
    Write-Host "✗ Dialpad sync failed: $($_.Exception.Message)" -ForegroundColor Red
    $dialpadResult = @{error = $_.Exception.Message}
}

Start-Sleep -Seconds 2

# Test 3: HubSpot Sync
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test 3: HubSpot Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Syncing HubSpot sequences..." -ForegroundColor Yellow
$body = '{"sync_type":"full"}'

try {
    $response = Invoke-RestMethod -Uri "https://hubspot-sync-z455yfejea-uc.a.run.app" -Method Post -Headers $headers -Body $body -ErrorAction Stop
    Write-Host "✓ HubSpot sync completed" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
    if ($response.rows_synced) {
        Write-Host "  Rows synced: $($response.rows_synced)" -ForegroundColor Gray
    }
    if ($response.errors -and $response.errors -gt 0) {
        Write-Host "  Errors: $($response.errors)" -ForegroundColor Yellow
    }
    $hubspotResult = $response
} catch {
    Write-Host "✗ HubSpot sync failed: $($_.Exception.Message)" -ForegroundColor Red
    $hubspotResult = @{error = $_.Exception.Message}
}

Start-Sleep -Seconds 3

# Test 4: Verify BigQuery Data
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test 4: BigQuery Data Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$bqTables = @(
    @{name="salesforce_accounts"; description="Salesforce Accounts"},
    @{name="salesforce_contacts"; description="Salesforce Contacts"},
    @{name="salesforce_leads"; description="Salesforce Leads"},
    @{name="salesforce_opportunities"; description="Salesforce Opportunities"},
    @{name="dialpad_calls"; description="Dialpad Calls"},
    @{name="hubspot_sequences"; description="HubSpot Sequences"}
)

$bqResults = @{}

foreach ($table in $bqTables) {
    Write-Host "Checking $($table.description)..." -ForegroundColor Yellow
    $query = "SELECT COUNT(*) as total FROM ``$projectId.sales_intelligence.$($table.name)``"
    
    try {
        $result = bq query --use_legacy_sql=false --format=json $query 2>&1
        if ($LASTEXITCODE -eq 0) {
            $json = $result | ConvertFrom-Json
            $count = $json[0].total
            $bqResults[$table.name] = $count
            if ($count -gt 0) {
                Write-Host "✓ $($table.description): $count rows" -ForegroundColor Green
            } else {
                Write-Host "⚠ $($table.description): 0 rows (no data yet)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "✗ Failed to query $($table.name): $result" -ForegroundColor Red
            $bqResults[$table.name] = "ERROR"
        }
    } catch {
        Write-Host "✗ Error checking $($table.name): $_" -ForegroundColor Red
        $bqResults[$table.name] = "ERROR"
    }
}

# Test 5: Check Recent Logs
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test 5: Recent Error Logs Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$functions = @("salesforce-sync", "dialpad-sync", "hubspot-sync")

foreach ($func in $functions) {
    Write-Host "Checking $func logs..." -ForegroundColor Yellow
    try {
        $logs = gcloud functions logs read $func --gen2 --region=$region --limit=5 --project=$projectId 2>&1
        $errorLogs = $logs | Select-String -Pattern "ERROR|Error|error|FAILED|Failed|failed" | Select-Object -First 3
        if ($errorLogs) {
            Write-Host "⚠ Found errors in $func:" -ForegroundColor Yellow
            $errorLogs | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        } else {
            Write-Host "✓ No recent errors in $func" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠ Could not check logs for $func" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Salesforce Sync Results:" -ForegroundColor White
foreach ($obj in $sfObjects) {
    if ($sfResults[$obj].error) {
        Write-Host "  ✗ $obj: FAILED" -ForegroundColor Red
    } elseif ($sfResults[$obj].rows_synced -gt 0) {
        Write-Host "  ✓ $obj: $($sfResults[$obj].rows_synced) rows synced" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $obj: No rows synced" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Dialpad Sync:" -ForegroundColor White
if ($dialpadResult.error) {
    Write-Host "  ✗ FAILED: $($dialpadResult.error)" -ForegroundColor Red
} elseif ($dialpadResult.rows_synced -gt 0) {
    Write-Host "  ✓ $($dialpadResult.rows_synced) rows synced" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No rows synced" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "HubSpot Sync:" -ForegroundColor White
if ($hubspotResult.error) {
    Write-Host "  ✗ FAILED: $($hubspotResult.error)" -ForegroundColor Red
} elseif ($hubspotResult.rows_synced -gt 0) {
    Write-Host "  ✓ $($hubspotResult.rows_synced) rows synced" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No rows synced" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "BigQuery Data:" -ForegroundColor White
foreach ($table in $bqTables) {
    $count = $bqResults[$table.name]
    if ($count -eq "ERROR") {
        Write-Host "  ✗ $($table.description): ERROR" -ForegroundColor Red
    } elseif ($count -gt 0) {
        Write-Host "  ✓ $($table.description): $count rows" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $($table.description): 0 rows" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

