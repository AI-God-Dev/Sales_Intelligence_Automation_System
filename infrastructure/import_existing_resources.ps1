# Script to import existing GCP resources into Terraform state
# Run this if you get 409 errors saying resources already exist

$ErrorActionPreference = "Stop"

$projectId = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Importing Existing Resources to Terraform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Region: $region" -ForegroundColor Yellow
Write-Host ""

# Check if terraform is initialized
if (-not (Test-Path ".terraform")) {
    Write-Host "Error: Terraform not initialized. Run 'terraform init' first." -ForegroundColor Red
    exit 1
}

# Import BigQuery Dataset
Write-Host "1. Importing BigQuery dataset..." -ForegroundColor Green
terraform import google_bigquery_dataset.sales_intelligence "$projectId`:sales_intelligence" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ BigQuery dataset imported" -ForegroundColor Green
} else {
    Write-Host "  (Already imported or doesn't exist)" -ForegroundColor Gray
}

# Import Cloud Scheduler Jobs
Write-Host ""
Write-Host "2. Importing Cloud Scheduler jobs..." -ForegroundColor Green
$jobs = @(
    @{Name="gmail-incremental-sync"; Resource="gmail_incremental_sync"},
    @{Name="gmail-full-sync"; Resource="gmail_full_sync"},
    @{Name="salesforce-incremental-sync"; Resource="salesforce_incremental_sync"},
    @{Name="salesforce-full-sync"; Resource="salesforce_full_sync"},
    @{Name="dialpad-sync"; Resource="dialpad_sync"},
    @{Name="hubspot-sync"; Resource="hubspot_sync"},
    @{Name="entity-resolution"; Resource="entity_resolution"}
)

foreach ($job in $jobs) {
    Write-Host "  Importing $($job.Name)..." -ForegroundColor Gray
    $resourcePath = "projects/$projectId/locations/$region/jobs/$($job.Name)"
    terraform import "google_cloud_scheduler_job.$($job.Resource)" $resourcePath 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $($job.Name) imported" -ForegroundColor Green
    } else {
        Write-Host "    (Already imported or doesn't exist)" -ForegroundColor Gray
    }
}

# Import Pub/Sub Topics (if they exist)
Write-Host ""
Write-Host "3. Importing Pub/Sub topics (if they exist)..." -ForegroundColor Green
$topics = @(
    @{Name="gmail-ingestion"; Resource="gmail_ingestion"},
    @{Name="salesforce-ingestion"; Resource="salesforce_ingestion"},
    @{Name="dialpad-ingestion"; Resource="dialpad_ingestion"},
    @{Name="hubspot-ingestion"; Resource="hubspot_ingestion"},
    @{Name="ingestion-errors"; Resource="ingestion_errors"}
)

foreach ($topic in $topics) {
    Write-Host "  Importing $($topic.Name)..." -ForegroundColor Gray
    $resourcePath = "projects/$projectId/topics/$($topic.Name)"
    terraform import "google_pubsub_topic.$($topic.Resource)" $resourcePath 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $($topic.Name) imported" -ForegroundColor Green
    } else {
        Write-Host "    (Already imported or doesn't exist)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Import complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run 'terraform plan' to see if there are any differences"
Write-Host "2. If needed, run 'terraform apply' to sync any differences"
Write-Host ""

