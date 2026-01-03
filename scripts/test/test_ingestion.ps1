# Test Ingestion Script
# Manually triggers all ingestion functions to test the pipeline

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Ingestion Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get access token
Write-Host "Getting access token..." -ForegroundColor Yellow
$accessToken = gcloud auth print-access-token
if (-not $accessToken) {
    Write-Host "ERROR: Failed to get access token" -ForegroundColor Red
    exit 1
}

$baseUrl = "https://$region-$projectId.cloudfunctions.net"

# Function to trigger a Cloud Function
function Invoke-Ingestion {
    param(
        [string]$FunctionName,
        [string]$Body,
        [string]$Description
    )
    
    Write-Host "Testing: $Description" -ForegroundColor Yellow
    Write-Host "  Function: $FunctionName" -ForegroundColor Gray
    
    $url = "$baseUrl/$FunctionName"
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $Body -ErrorAction Stop
        Write-Host "  ✓ Success" -ForegroundColor Green
        Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        return $false
    }
    Write-Host ""
}

# Test Gmail Full Sync
Write-Host "1. Gmail Full Sync" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "gmail-sync" -Body '{"sync_type":"full"}' -Description "Gmail full sync"
Start-Sleep -Seconds 2

# Test Gmail Incremental Sync
Write-Host "2. Gmail Incremental Sync" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "gmail-sync" -Body '{"sync_type":"incremental"}' -Description "Gmail incremental sync"
Start-Sleep -Seconds 2

# Test Salesforce Full Sync (Account)
Write-Host "3. Salesforce Full Sync - Account" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "salesforce-sync" -Body '{"sync_type":"full","object_type":"Account"}' -Description "Salesforce Account full sync"
Start-Sleep -Seconds 2

# Test Salesforce Full Sync (Contact)
Write-Host "4. Salesforce Full Sync - Contact" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "salesforce-sync" -Body '{"sync_type":"full","object_type":"Contact"}' -Description "Salesforce Contact full sync"
Start-Sleep -Seconds 2

# Test Salesforce Full Sync (Lead)
Write-Host "5. Salesforce Full Sync - Lead" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "salesforce-sync" -Body '{"sync_type":"full","object_type":"Lead"}' -Description "Salesforce Lead full sync"
Start-Sleep -Seconds 2

# Test Salesforce Full Sync (Opportunity)
Write-Host "6. Salesforce Full Sync - Opportunity" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "salesforce-sync" -Body '{"sync_type":"full","object_type":"Opportunity"}' -Description "Salesforce Opportunity full sync"
Start-Sleep -Seconds 2

# Test Salesforce Full Sync (Activity)
Write-Host "7. Salesforce Full Sync - Activity" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "salesforce-sync" -Body '{"sync_type":"full","object_type":"Activity"}' -Description "Salesforce Activity full sync"
Start-Sleep -Seconds 2

# Test Dialpad Sync
Write-Host "8. Dialpad Sync" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "dialpad-sync" -Body '{}' -Description "Dialpad call logs sync"
Start-Sleep -Seconds 2

# Test HubSpot Sync
Write-Host "9. HubSpot Sync" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "hubspot-sync" -Body '{}' -Description "HubSpot sequences sync"
Start-Sleep -Seconds 2

# Test Entity Resolution
Write-Host "10. Entity Resolution" -ForegroundColor Cyan
Invoke-Ingestion -FunctionName "entity-resolution" -Body '{}' -Description "Entity resolution and matching"
Start-Sleep -Seconds 2

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ingestion Testing Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check Cloud Function logs: .\scripts\check_logs.ps1" -ForegroundColor White
Write-Host "2. Verify BigQuery data: .\scripts\check_bigquery.ps1" -ForegroundColor White
Write-Host "3. Check ETL run history: bq query --use_legacy_sql=false --project_id=$projectId \"SELECT * FROM \`$projectId.sales_intelligence.etl_runs ORDER BY started_at DESC LIMIT 10\"" -ForegroundColor White
Write-Host ""

