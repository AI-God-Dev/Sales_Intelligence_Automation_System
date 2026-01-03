# Deploy fixes to Cloud Functions
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploying Fixes to Cloud Functions" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Deploying Salesforce Sync with fixes..." -ForegroundColor Yellow
Write-Host "This will update the function with:" -ForegroundColor Gray
Write-Host "  - Improved retry logic" -ForegroundColor Gray
Write-Host "  - Text truncation for large fields" -ForegroundColor Gray
Write-Host "  - Better error handling" -ForegroundColor Gray
Write-Host "  - Record validation" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Deploying salesforce-sync..." -ForegroundColor Cyan

try {
    gcloud functions deploy salesforce-sync `
        --gen2 `
        --region=$region `
        --runtime=python311 `
        --source=cloud_functions/salesforce_sync `
        --entry-point=salesforce_sync `
        --trigger-http `
        --allow-unauthenticated `
        --memory=512MB `
        --timeout=540s `
        --max-instances=10 `
        --service-account=sales-intel-poc-sa@$projectId.iam.gserviceaccount.com
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Test EmailMessage sync: .\fix_sync_issues.ps1" -ForegroundColor White
        Write-Host "  2. Monitor logs: gcloud functions logs read salesforce-sync --gen2 --region=$region --limit=20" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "❌ Deployment failed" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error during deployment: $_" -ForegroundColor Red
}

