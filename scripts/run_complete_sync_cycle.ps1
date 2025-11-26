# Complete Sync Cycle - Run All Syncs in Proper Order
# This script runs all syncs in the correct sequence with proper delays

$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Complete Sync Cycle" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get token
$token = gcloud auth print-identity-token
if (-not $token) {
    Write-Host "Error: Failed to get identity token" -ForegroundColor Red
    exit 1
}

$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"

function Invoke-SyncWithRetry {
    param(
        [string]$FunctionName,
        [string]$Body,
        [string]$Description,
        [int]$MaxRetries = 3
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
                -Method Post `
                -Headers @{
                    Authorization = "Bearer $token"
                    "Content-Type" = "application/json"
                } `
                -Body $Body `
                -ErrorAction Stop
            
            Write-Host "  ✅ Success" -ForegroundColor Green
            if ($response | Get-Member -Name "rows_synced" -MemberType Properties) {
                Write-Host "     Rows synced: $($response.rows_synced)" -ForegroundColor Gray
            }
            return $true
        } catch {
            if ($attempt -lt $MaxRetries) {
                $waitTime = [math]::Pow(2, $attempt)
                Write-Host "  ⚠️  Attempt $attempt failed, retrying in $waitTime seconds..." -ForegroundColor Yellow
                Start-Sleep -Seconds $waitTime
            } else {
                Write-Host "  ❌ Failed after $MaxRetries attempts" -ForegroundColor Red
                Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
                return $false
            }
        }
    }
    return $false
}

# Phase 1: Salesforce Sync (All Objects)
Write-Host "📊 Phase 1: Salesforce Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$sfObjects = @("Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage")
foreach ($obj in $sfObjects) {
    $body = @{
        object_type = $obj
        sync_type = "incremental"
    } | ConvertTo-Json -Compress
    
    Invoke-SyncWithRetry "salesforce-sync" $body "Salesforce $obj" -MaxRetries 2
    Start-Sleep -Seconds 3
}

Write-Host ""

# Phase 2: Dialpad Sync
Write-Host "📞 Phase 2: Dialpad Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
Invoke-SyncWithRetry "dialpad-sync" $dpBody "Dialpad Calls" -MaxRetries 2
Start-Sleep -Seconds 3

Write-Host ""

# Phase 3: HubSpot Sync
Write-Host "📧 Phase 3: HubSpot Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$hsBody = @{} | ConvertTo-Json -Compress
Invoke-SyncWithRetry "hubspot-sync" $hsBody "HubSpot Sequences" -MaxRetries 2
Start-Sleep -Seconds 3

Write-Host ""

# Phase 4: Entity Resolution
Write-Host "🔗 Phase 4: Entity Resolution" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$erBody = @{
    entity_type = "all"
    batch_size = 1000
} | ConvertTo-Json -Compress

Invoke-SyncWithRetry "entity-resolution" $erBody "Entity Resolution" -MaxRetries 2

Write-Host ""
Write-Host "⏳ Waiting 60 seconds for processing..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Phase 5: Validation
Write-Host ""
Write-Host "✅ Phase 5: Validation" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

& "$PSScriptRoot\validate_all_syncs.ps1"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Complete Sync Cycle Finished!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

