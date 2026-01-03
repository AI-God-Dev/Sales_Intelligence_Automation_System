# Test all ingestion sources
# Quick verification script for client

$ErrorActionPreference = "Continue"

$PROJECT_ID = $env:GCP_PROJECT_ID
if (-not $PROJECT_ID) {
    $PROJECT_ID = "maharani-sales-hub-11-2025"
}

$REGION = $env:GCP_REGION
if (-not $REGION) {
    $REGION = "us-central1"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing All Ingestion Sources" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

function Test-Sync {
    param(
        [string]$FunctionName,
        [string]$DisplayName
    )
    
    Write-Host "Testing $DisplayName..." -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    try {
        $TOKEN = gcloud auth print-access-token
        $URL = "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FunctionName}"
        
        $body = @{
            sync_type = "full"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $URL -Method Post -Headers @{
            "Authorization" = "Bearer $TOKEN"
            "Content-Type" = "application/json"
        } -Body $body -ErrorAction Stop
        
        Write-Host "✓ $DisplayName triggered successfully" -ForegroundColor Green
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "✗ $DisplayName failed (HTTP $statusCode)" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Test each sync
Test-Sync -FunctionName "gmail-sync" -DisplayName "Gmail Sync"
Test-Sync -FunctionName "salesforce-sync" -DisplayName "Salesforce Sync"
Test-Sync -FunctionName "dialpad-sync" -DisplayName "Dialpad Sync"
Test-Sync -FunctionName "hubspot-sync" -DisplayName "HubSpot Sync"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Check BigQuery for data:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host 'bq query "SELECT COUNT(*) FROM sales_intelligence.gmail_messages"' -ForegroundColor Gray
Write-Host 'bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"' -ForegroundColor Gray
Write-Host 'bq query "SELECT COUNT(*) FROM sales_intelligence.dialpad_calls"' -ForegroundColor Gray
Write-Host 'bq query "SELECT COUNT(*) FROM sales_intelligence.hubspot_sequences"' -ForegroundColor Gray
Write-Host ""

