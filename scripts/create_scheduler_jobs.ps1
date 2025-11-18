# Create Cloud Scheduler Jobs for Automated Ingestion
# Creates all scheduled jobs for Gmail, Salesforce, Dialpad, HubSpot, and Entity Resolution

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$serviceAccount = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"
$timezone = "America/New_York"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Cloud Scheduler Jobs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Region: $region" -ForegroundColor Yellow
Write-Host ""

# Get Cloud Function URLs
$functionBaseUrl = "https://$region-$projectId.cloudfunctions.net"

# Define all scheduler jobs
$jobs = @(
    @{
        Name = "gmail-full-sync"
        Schedule = "0 2 * * *"  # Daily at 2 AM
        Uri = "$functionBaseUrl/gmail-sync"
        Body = @{ sync_type = "full" }
        Description = "Full Gmail sync - runs daily at 2 AM"
    },
    @{
        Name = "gmail-incremental-sync"
        Schedule = "0 * * * *"  # Every hour
        Uri = "$functionBaseUrl/gmail-sync"
        Body = @{ sync_type = "incremental" }
        Description = "Incremental Gmail sync - runs every hour"
    },
    @{
        Name = "salesforce-full-sync"
        Schedule = "0 3 * * 0"  # Weekly on Sunday at 3 AM
        Uri = "$functionBaseUrl/salesforce-sync"
        Body = @{ sync_type = "full"; object_type = "Account" }
        Description = "Full Salesforce sync - runs weekly on Sunday at 3 AM"
    },
    @{
        Name = "salesforce-incremental-sync"
        Schedule = "0 */6 * * *"  # Every 6 hours
        Uri = "$functionBaseUrl/salesforce-sync"
        Body = @{ sync_type = "incremental"; object_type = "Account" }
        Description = "Incremental Salesforce sync - runs every 6 hours"
    },
    @{
        Name = "dialpad-sync"
        Schedule = "0 1 * * *"  # Daily at 1 AM
        Uri = "$functionBaseUrl/dialpad-sync"
        Body = @{ sync_type = "incremental" }
        Description = "Dialpad call logs sync - runs daily at 1 AM"
    },
    @{
        Name = "hubspot-sync"
        Schedule = "0 4 * * *"  # Daily at 4 AM
        Uri = "$functionBaseUrl/hubspot-sync"
        Body = @{}
        Description = "HubSpot sequences sync - runs daily at 4 AM"
    },
    @{
        Name = "entity-resolution"
        Schedule = "0 */4 * * *"  # Every 4 hours
        Uri = "$functionBaseUrl/entity-resolution"
        Body = @{}
        Description = "Entity resolution and matching - runs every 4 hours"
    }
)

# Function to create a scheduler job
function Create-SchedulerJob {
    param(
        [string]$JobName,
        [string]$Schedule,
        [string]$Uri,
        [hashtable]$Body,
        [string]$Description
    )
    
    Write-Host "Creating job: $JobName" -ForegroundColor Yellow
    Write-Host "  Schedule: $Schedule" -ForegroundColor Gray
    Write-Host "  Target: $Uri" -ForegroundColor Gray
    
    # Check if job already exists
    $existingJob = gcloud scheduler jobs describe $JobName --location=$region --project=$projectId 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ⚠ Job already exists, updating..." -ForegroundColor Yellow
        gcloud scheduler jobs delete $JobName --location=$region --project=$projectId --quiet 2>$null
    }
    
    # Convert body to JSON
    $bodyJson = ($Body | ConvertTo-Json -Compress)
    
    # Create the job
    $cmd = @(
        "gcloud", "scheduler", "jobs", "create", "http", $JobName,
        "--location=$region",
        "--schedule=$Schedule",
        "--uri=$Uri",
        "--http-method=POST",
        "--oidc-service-account-email=$serviceAccount",
        "--time-zone=$timezone",
        "--message-body=$bodyJson",
        "--headers=Content-Type=application/json",
        "--description=$Description",
        "--project=$projectId"
    )
    
    & $cmd[0] $cmd[1..($cmd.Length-1)]
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create $JobName" -ForegroundColor Red
        return $false
    }
    
    Write-Host "  ✓ Successfully created $JobName" -ForegroundColor Green
    Write-Host ""
    return $true
}

# Create all jobs
$jobResults = @{}
foreach ($job in $jobs) {
    $success = Create-SchedulerJob `
        -JobName $job.Name `
        -Schedule $job.Schedule `
        -Uri $job.Uri `
        -Body $job.Body `
        -Description $job.Description
    $jobResults[$job.Name] = $success
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Scheduler Jobs Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
foreach ($job in $jobs) {
    $status = if ($jobResults[$job.Name]) { "✓ Created" } else { "✗ Failed" }
    $color = if ($jobResults[$job.Name]) { "Green" } else { "Red" }
    Write-Host "$($job.Name): $status" -ForegroundColor $color
}

$allSuccess = ($jobResults.Values | Where-Object { $_ -eq $false }).Count -eq 0
Write-Host ""
if ($allSuccess) {
    Write-Host "✓ All scheduler jobs created successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some jobs failed to create. Check errors above." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

