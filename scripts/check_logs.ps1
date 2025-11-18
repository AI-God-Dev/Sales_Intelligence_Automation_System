# Check Cloud Function Logs
# Displays recent logs for all Cloud Functions

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloud Function Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$functions = @("gmail-sync", "salesforce-sync", "dialpad-sync", "hubspot-sync", "entity-resolution")

foreach ($func in $functions) {
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "Function: $func" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    
    gcloud functions logs read $func `
        --region=$region `
        --project=$projectId `
        --gen2 `
        --limit=10 `
        --format="table(timestamp,severity,textPayload)"
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "To view more logs, use:" -ForegroundColor Yellow
Write-Host "gcloud functions logs read FUNCTION_NAME --region=$region --project=$projectId --gen2 --limit=50" -ForegroundColor White
Write-Host ""

