# Create Pub/Sub Topic for Error Notifications
# Creates the ingestion-errors topic for error notifications

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$topicName = "ingestion-errors"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating Pub/Sub Topic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Topic: $topicName" -ForegroundColor Yellow
Write-Host ""

# Check if topic already exists
$topicExists = gcloud pubsub topics describe $topicName --project=$projectId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Topic '$topicName' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating topic: $topicName" -ForegroundColor Yellow
    gcloud pubsub topics create $topicName --project=$projectId
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create topic" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Topic created successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Pub/Sub topic setup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

