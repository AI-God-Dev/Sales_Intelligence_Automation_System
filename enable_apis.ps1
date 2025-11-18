# Enable Required GCP APIs
# Enables all APIs needed for the Sales Intelligence System

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enabling GCP APIs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host ""

# Ensure correct project is set
Write-Host "Setting project to $projectId..." -ForegroundColor Yellow
gcloud config set project $projectId

$apis = @(
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com",
    "appengine.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "gmail.googleapis.com"
)

Write-Host "Enabling APIs..." -ForegroundColor Yellow
Write-Host ""

$enabledCount = 0
$alreadyEnabledCount = 0
$failedCount = 0

foreach ($api in $apis) {
    Write-Host "Checking $api..." -ForegroundColor Gray
    
    # Check if API is already enabled
    $isEnabled = gcloud services list --enabled --filter="name:$api" --format="value(name)" --project=$projectId 2>$null
    
    if ($isEnabled) {
        Write-Host "  ✓ Already enabled" -ForegroundColor Green
        $alreadyEnabledCount++
    } else {
        Write-Host "  Enabling..." -ForegroundColor Yellow
        gcloud services enable $api --project=$projectId
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Enabled" -ForegroundColor Green
            $enabledCount++
        } else {
            Write-Host "  ✗ Failed to enable" -ForegroundColor Red
            $failedCount++
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API Enablement Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enabled: $enabledCount" -ForegroundColor Green
Write-Host "Already enabled: $alreadyEnabledCount" -ForegroundColor Yellow
Write-Host "Failed: $failedCount" -ForegroundColor $(if ($failedCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failedCount -gt 0) {
    Write-Host "⚠ Some APIs failed to enable. Check errors above." -ForegroundColor Yellow
    Write-Host "You may need to wait a few minutes and try again." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ All APIs enabled successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
}

