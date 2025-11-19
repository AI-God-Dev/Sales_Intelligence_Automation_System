# Quick Fix for Terraform 409 Errors
# Run this script to import all existing resources into Terraform state

$ErrorActionPreference = "Continue"  # Continue on errors so we can import multiple resources

$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Terraform 409 Errors" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "This will import existing resources into Terraform state" -ForegroundColor Yellow
Write-Host ""

# Check if we're in infrastructure directory
$currentDir = Get-Location
if (-not (Test-Path "main.tf")) {
    Write-Host "[ERROR] Not in infrastructure directory!" -ForegroundColor Red
    Write-Host "Please run: cd infrastructure" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Importing BigQuery dataset..." -ForegroundColor Green
try {
    terraform import google_bigquery_dataset.sales_intelligence "${projectId}:sales_intelligence" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ BigQuery dataset imported" -ForegroundColor Green
    } else {
        Write-Host "  (Already in state or error occurred)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  (Could not import - may already be in state)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 2: Importing Cloud Scheduler jobs..." -ForegroundColor Green

$jobs = @(
    @{TerraformName="gmail_incremental_sync"; GCPName="gmail-incremental-sync"},
    @{TerraformName="gmail_full_sync"; GCPName="gmail-full-sync"},
    @{TerraformName="salesforce_incremental_sync"; GCPName="salesforce-incremental-sync"},
    @{TerraformName="salesforce_full_sync"; GCPName="salesforce-full-sync"},
    @{TerraformName="dialpad_sync"; GCPName="dialpad-sync"},
    @{TerraformName="hubspot_sync"; GCPName="hubspot-sync"},
    @{TerraformName="entity_resolution"; GCPName="entity-resolution"}
)

$importedCount = 0
foreach ($job in $jobs) {
    $resourcePath = "projects/$projectId/locations/$region/jobs/$($job.GCPName)"
    Write-Host "  Importing $($job.GCPName)..." -ForegroundColor Gray -NoNewline
    try {
        terraform import "google_cloud_scheduler_job.$($job.TerraformName)" $resourcePath 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            $importedCount++
        } else {
            Write-Host " (already in state)" -ForegroundColor Gray
        }
    } catch {
        Write-Host " (error)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Import Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Imported $importedCount scheduler jobs" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: terraform plan" -ForegroundColor White
Write-Host "   (This should now show NO 409 errors)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. If plan looks good, run: terraform apply" -ForegroundColor White
Write-Host ""

