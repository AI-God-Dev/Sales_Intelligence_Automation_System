# Setup Cloud Scheduler for Automated Syncs
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$serviceAccount = "sales-intel-poc-sa@${projectId}.iam.gserviceaccount.com"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setting Up Cloud Scheduler Jobs" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if scheduler API is enabled
Write-Host "Checking Cloud Scheduler API..." -ForegroundColor Yellow
$apiEnabled = gcloud services list --enabled --filter="name:cloudscheduler.googleapis.com" 2>&1
if (-not $apiEnabled) {
    Write-Host "  Enabling Cloud Scheduler API..." -ForegroundColor Yellow
    gcloud services enable cloudscheduler.googleapis.com --project=$projectId
}

Write-Host ""

# Function to create scheduler job
function Create-SchedulerJob {
    param($JobName, $Schedule, $FunctionName, $Body, $Description)
    
    Write-Host "Creating scheduler job: $JobName" -ForegroundColor Cyan
    Write-Host "  Schedule: $Schedule" -ForegroundColor Gray
    Write-Host "  Function: $FunctionName" -ForegroundColor Gray
    
    # Check if job exists
    $existing = gcloud scheduler jobs describe $JobName --location=$region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Job exists, updating..." -ForegroundColor Yellow
        $action = "update"
    } else {
        Write-Host "  Creating new job..." -ForegroundColor Yellow
        $action = "create"
    }
    
    $functionUrl = "https://${region}-${projectId}.cloudfunctions.net/${FunctionName}"
    
    if ($action -eq "create") {
        gcloud scheduler jobs create http $JobName `
            --location=$region `
            --schedule=$Schedule `
            --uri=$functionUrl `
            --http-method=POST `
            --headers="Content-Type=application/json" `
            --message-body=$Body `
            --oidc-service-account-email=$serviceAccount `
            --description="Automated $Description" `
            --time-zone="America/Los_Angeles" `
            2>&1 | Out-Null
    } else {
        gcloud scheduler jobs update http $JobName `
            --location=$region `
            --schedule=$Schedule `
            --uri=$functionUrl `
            --http-method=POST `
            --headers="Content-Type=application/json" `
            --message-body=$Body `
            --oidc-service-account-email=$serviceAccount `
            --description="Automated $Description" `
            --time-zone="America/Los_Angeles" `
            2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $JobName configured" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ❌ Failed to configure $JobName" -ForegroundColor Red
        return $false
    }
}

# Salesforce Syncs - Hourly incremental
Write-Host "Salesforce Syncs (Hourly Incremental):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$sfObjects = @("Account", "Contact", "Lead", "Opportunity")
foreach ($obj in $sfObjects) {
    $jobName = "salesforce-${obj.ToLower()}-hourly"
    $body = @{object_type=$obj; sync_type="incremental"} | ConvertTo-Json -Compress
    Create-SchedulerJob $jobName "0 * * * *" "salesforce-sync" $body "Salesforce $obj sync"
    Start-Sleep -Seconds 2
}

# Salesforce Activities - Every 2 hours
Write-Host ""
Write-Host "Salesforce Activities (Every 2 Hours):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$activities = @("Task", "Event")
foreach ($act in $activities) {
    $jobName = "salesforce-${act.ToLower()}-2hourly"
    $body = @{object_type=$act; sync_type="incremental"} | ConvertTo-Json -Compress
    Create-SchedulerJob $jobName "0 */2 * * *" "salesforce-sync" $body "Salesforce $act sync"
    Start-Sleep -Seconds 2
}

# Salesforce EmailMessage - Daily
Write-Host ""
Write-Host "Salesforce EmailMessage (Daily):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$emBody = @{object_type="EmailMessage"; sync_type="incremental"} | ConvertTo-Json -Compress
Create-SchedulerJob "salesforce-emailmessage-daily" "0 2 * * *" "salesforce-sync" $emBody "Salesforce EmailMessage sync"

# Dialpad Sync - Every 2 hours
Write-Host ""
Write-Host "Dialpad Sync (Every 2 Hours):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
Create-SchedulerJob "dialpad-sync-2hourly" "0 */2 * * *" "dialpad-sync" $dpBody "Dialpad call sync"

# HubSpot Sync - Daily
Write-Host ""
Write-Host "HubSpot Sync (Daily):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$hsBody = @{} | ConvertTo-Json -Compress
Create-SchedulerJob "hubspot-sync-daily" "0 3 * * *" "hubspot-sync" $hsBody "HubSpot sequence sync"

# Entity Resolution - Daily
Write-Host ""
Write-Host "Entity Resolution (Daily):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$erBody = @{entity_type="all"; batch_size=1000} | ConvertTo-Json -Compress
Create-SchedulerJob "entity-resolution-daily" "0 4 * * *" "entity-resolution" $erBody "Entity resolution"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Scheduler Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "View scheduled jobs:" -ForegroundColor Yellow
Write-Host "  gcloud scheduler jobs list --location=$region" -ForegroundColor White
Write-Host ""
Write-Host "Test a job:" -ForegroundColor Yellow
Write-Host "  gcloud scheduler jobs run JOB_NAME --location=$region" -ForegroundColor White
Write-Host ""

