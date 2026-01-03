# Run all data ingestion syncs in sequence
# PowerShell version - Run this after Gmail sync completes

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running All Data Ingestion Syncs" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get identity token
$TOKEN = gcloud auth print-identity-token 2>$null
if ([string]::IsNullOrEmpty($TOKEN)) {
    Write-Host "Error: Failed to get identity token. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}

$BASE_URL = "https://${REGION}-${PROJECT_ID}.cloudfunctions.net"

# Function to trigger a sync
function Trigger-Sync {
    param(
        [string]$FunctionName,
        [string]$Data,
        [string]$Description
    )
    
    Write-Host "🔄 Triggering $Description..." -ForegroundColor Yellow
    
    $response = curl.exe -s -w "`n%{http_code}" -X POST `
        "${BASE_URL}/${FunctionName}" `
        -H "Authorization: Bearer ${TOKEN}" `
        -H "Content-Type: application/json" `
        -d $Data 2>$null
    
    $lines = $response -split "`n"
    $httpCode = $lines[-1]
    $body = ($lines[0..($lines.Length-2)] -join "`n")
    
    if ($httpCode -eq "200" -or $httpCode -eq "202") {
        Write-Host "  ✅ Successfully triggered $FunctionName (HTTP $httpCode)" -ForegroundColor Green
        Write-Host "  Response: $body" -ForegroundColor Gray
        return $true
    } else {
        Write-Host "  ❌ Failed to trigger $FunctionName (HTTP $httpCode)" -ForegroundColor Red
        Write-Host "  Response: $body" -ForegroundColor Gray
        return $false
    }
    Write-Host ""
}

# Step 1: Salesforce Sync
Write-Host "📊 Step 1: Salesforce Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

Trigger-Sync "salesforce-sync" '{"sync_type":"full","object_type":"Account"}' "Salesforce Accounts sync"
Start-Sleep -Seconds 5

Trigger-Sync "salesforce-sync" '{"sync_type":"full","object_type":"Contact"}' "Salesforce Contacts sync"
Start-Sleep -Seconds 5

Trigger-Sync "salesforce-sync" '{"sync_type":"full","object_type":"Lead"}' "Salesforce Leads sync"
Start-Sleep -Seconds 5

Trigger-Sync "salesforce-sync" '{"sync_type":"full","object_type":"Opportunity"}' "Salesforce Opportunities sync"
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "📞 Step 2: Dialpad Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Trigger-Sync "dialpad-sync" '{"sync_type":"incremental"}' "Dialpad call logs sync"
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "📧 Step 3: HubSpot Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Trigger-Sync "hubspot-sync" '{"sync_type":"full"}' "HubSpot sequences sync"
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🔄 Step 4: Entity Resolution" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray
Trigger-Sync "entity-resolution" '{}' "Entity resolution and matching"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ All syncs triggered!" -ForegroundColor Green
Write-Host ""
Write-Host "⏳ Waiting 2 minutes for initial processing..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

Write-Host ""
Write-Host "📊 Checking ingestion status..." -ForegroundColor Cyan
& ".\scripts\check_ingestion_status.ps1"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Check BigQuery tables for data"
Write-Host "   2. Verify ETL runs table for job status"
Write-Host "   3. Check logs if any syncs failed"
Write-Host "==========================================" -ForegroundColor Cyan

