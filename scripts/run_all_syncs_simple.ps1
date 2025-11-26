# Simple script to run all syncs and verify
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running All Syncs" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get token
$token = gcloud auth print-identity-token
if (-not $token) {
    Write-Host "Error: Failed to get token. Run: gcloud auth login" -ForegroundColor Red
    exit 1
}

$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"

# Function to trigger sync
function Trigger-Sync {
    param($FunctionName, $Body, $Description)
    Write-Host "Triggering $Description..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
            -Method Post `
            -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
            -Body $Body `
            -ErrorAction Stop
        Write-Host "  Success: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Salesforce syncs
Write-Host "Salesforce Syncs:" -ForegroundColor Cyan
$sfObjects = @("Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage")
foreach ($obj in $sfObjects) {
    $body = @{object_type=$obj; sync_type="incremental"} | ConvertTo-Json -Compress
    Trigger-Sync "salesforce-sync" $body "Salesforce $obj"
    Start-Sleep -Seconds 2
}

# Dialpad sync
Write-Host ""
Write-Host "Dialpad Sync:" -ForegroundColor Cyan
$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
Trigger-Sync "dialpad-sync" $dpBody "Dialpad Calls"

# HubSpot sync
Write-Host ""
Write-Host "HubSpot Sync:" -ForegroundColor Cyan
$hsBody = @{} | ConvertTo-Json -Compress
Trigger-Sync "hubspot-sync" $hsBody "HubSpot Sequences"

# Entity Resolution
Write-Host ""
Write-Host "Entity Resolution:" -ForegroundColor Cyan
$erBody = @{entity_type="all"; batch_size=1000} | ConvertTo-Json -Compress
Trigger-Sync "entity-resolution" $erBody "Entity Resolution"

Write-Host ""
Write-Host "Waiting 30 seconds for processing..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check data
Write-Host ""
Write-Host "Checking Data:" -ForegroundColor Cyan
$tables = @("sf_accounts", "sf_contacts", "sf_leads", "sf_opportunities", "sf_activities", "sf_email_messages", "dialpad_calls", "hubspot_sequences")
foreach ($table in $tables) {
    $query = "SELECT COUNT(*) as total FROM ``$projectId.sales_intelligence.$table``"
    try {
        $result = bq query --use_legacy_sql=false --format=prettyjson $query 2>&1
        if ($LASTEXITCODE -eq 0) {
            $json = $result | ConvertFrom-Json
            $count = $json[0].total
            Write-Host "  $table : $count records" -ForegroundColor $(if ($count -gt 0) { "Green" } else { "Yellow" })
        }
    } catch {
        Write-Host "  $table : Error" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Complete!" -ForegroundColor Green

