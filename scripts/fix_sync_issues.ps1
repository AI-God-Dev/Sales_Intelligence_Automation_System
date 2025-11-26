# Fix sync issues - Create missing tables and test syncs
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fixing Sync Issues" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create EmailMessage table
Write-Host "Step 1: Creating EmailMessage table..." -ForegroundColor Yellow
& "$PSScriptRoot\create_email_message_table.ps1"
Write-Host ""

# Step 2: Test syncs with retry
Write-Host "Step 2: Testing syncs with improved retry logic..." -ForegroundColor Yellow
Write-Host ""

$token = gcloud auth print-identity-token
$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"

function Test-SyncWithRetry {
    param($FunctionName, $Body, $Description, $MaxRetries = 3)
    
    Write-Host "Testing $Description..." -ForegroundColor Cyan
    
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
                -Method Post `
                -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
                -Body $Body `
                -ErrorAction Stop
            
            Write-Host "  ✅ Success: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
            return $true
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($statusCode -eq 503 -or $statusCode -eq 429 -or $statusCode -eq 500) {
                if ($attempt -lt $MaxRetries) {
                    $waitTime = [math]::Min([math]::Pow(2, $attempt), 30)
                    Write-Host "  ⚠️  Attempt $attempt failed (HTTP $statusCode), retrying in $waitTime seconds..." -ForegroundColor Yellow
                    Start-Sleep -Seconds $waitTime
                } else {
                    Write-Host "  ❌ Failed after $MaxRetries attempts: HTTP $statusCode" -ForegroundColor Red
                    return $false
                }
            } else {
                Write-Host "  ❌ Failed: HTTP $statusCode - $($_.Exception.Message)" -ForegroundColor Red
                return $false
            }
        }
    }
    return $false
}

# Test EmailMessage sync
Write-Host "Testing EmailMessage sync..." -ForegroundColor Yellow
$emBody = @{object_type="EmailMessage"; sync_type="incremental"} | ConvertTo-Json -Compress
Test-SyncWithRetry "salesforce-sync" $emBody "EmailMessage Sync" -MaxRetries 5

Start-Sleep -Seconds 5

# Test Event sync
Write-Host ""
Write-Host "Testing Event sync..." -ForegroundColor Yellow
$eventBody = @{object_type="Event"; sync_type="incremental"} | ConvertTo-Json -Compress
Test-SyncWithRetry "salesforce-sync" $eventBody "Event Sync" -MaxRetries 5

Start-Sleep -Seconds 5

# Test Lead sync
Write-Host ""
Write-Host "Testing Lead sync..." -ForegroundColor Yellow
$leadBody = @{object_type="Lead"; sync_type="incremental"} | ConvertTo-Json -Compress
Test-SyncWithRetry "salesforce-sync" $leadBody "Lead Sync" -MaxRetries 5

Start-Sleep -Seconds 5

# Test Task sync
Write-Host ""
Write-Host "Testing Task sync..." -ForegroundColor Yellow
$taskBody = @{object_type="Task"; sync_type="incremental"} | ConvertTo-Json -Compress
Test-SyncWithRetry "salesforce-sync" $taskBody "Task Sync" -MaxRetries 5

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fix Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

