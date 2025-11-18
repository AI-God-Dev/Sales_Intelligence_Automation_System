# Master Setup Script for Sales Intelligence System - Phase 1
# This script orchestrates the complete setup process
# Run this after you have:
# 1. Authenticated gcloud CLI (gcloud auth login)
# 2. Set the project (gcloud config set project maharani-sales-hub-11-2025)
# 3. Created third-party API credentials (see MANUAL_STEPS.md)

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sales Intelligence System - Phase 1 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Region: $region" -ForegroundColor Yellow
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$gcloudInstalled = Get-Command gcloud -ErrorAction SilentlyContinue
$bqInstalled = Get-Command bq -ErrorAction SilentlyContinue

if (-not $gcloudInstalled) {
    Write-Host "ERROR: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}
if (-not $bqInstalled) {
    Write-Host "ERROR: bq CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}

# Check authentication
Write-Host "Checking gcloud authentication..." -ForegroundColor Yellow
$currentProject = gcloud config get-value project 2>$null
if ($currentProject -ne $projectId) {
    Write-Host "Setting project to $projectId..." -ForegroundColor Yellow
    gcloud config set project $projectId
}

$authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $authStatus) {
    Write-Host "ERROR: No active gcloud authentication. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Authenticated as: $authStatus" -ForegroundColor Green
Write-Host ""

# Step 1: Enable APIs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Enabling GCP APIs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
& ".\enable_apis.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to enable APIs" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Create Secrets
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Creating Secret Manager Secrets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "You will be prompted to enter secret values." -ForegroundColor Yellow
Write-Host "Press Enter to skip updating a secret (keep existing value)." -ForegroundColor Yellow
Write-Host ""
& ".\create_secrets.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create secrets" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Setup BigQuery
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Setting up BigQuery Dataset and Tables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
& ".\scripts\setup_bigquery.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to setup BigQuery" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Create Pub/Sub Topic
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Creating Pub/Sub Topic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
& ".\scripts\create_pubsub_topic.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create Pub/Sub topic" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 5: Deploy Cloud Functions
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 5: Deploying Cloud Functions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "This may take several minutes..." -ForegroundColor Yellow
& ".\scripts\deploy_functions.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy Cloud Functions" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 6: Create Cloud Scheduler Jobs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 6: Creating Cloud Scheduler Jobs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
& ".\scripts\create_scheduler_jobs.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create scheduler jobs" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 7: Verify Deployment
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 7: Verifying Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
& ".\scripts\verify_deployment.ps1"
Write-Host ""

# Final Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review the verification output above" -ForegroundColor White
Write-Host "2. Test ingestion by running: .\scripts\test_ingestion.ps1" -ForegroundColor White
Write-Host "3. Check Cloud Function logs: .\scripts\check_logs.ps1" -ForegroundColor White
Write-Host "4. Monitor BigQuery data: .\scripts\check_bigquery.ps1" -ForegroundColor White
Write-Host ""
Write-Host "For manual ingestion triggers, see: docs/INGESTION_TRIGGERS.md" -ForegroundColor Cyan
Write-Host ""

