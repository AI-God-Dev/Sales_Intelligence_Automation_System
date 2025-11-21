# Check Salesforce sync logs for errors
# PowerShell version

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

Write-Host "Checking Salesforce sync logs for errors..." -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host ""

# Check recent logs
Write-Host "Recent logs (last 50):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
gcloud functions logs read salesforce-sync `
  --region=$REGION `
  --project=$PROJECT_ID `
  --limit=50

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# Check for errors using Cloud Run logs (Gen2 functions)
Write-Host "Checking Cloud Run logs for errors..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=salesforce-sync AND severity>=ERROR" `
  --project=$PROJECT_ID `
  --limit=20 `
  --format="table(timestamp,severity,textPayload)"

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "For real-time logs, use:" -ForegroundColor Yellow
Write-Host "gcloud logging tail `"resource.type=cloud_run_revision AND resource.labels.service_name=salesforce-sync`" --project=$PROJECT_ID" -ForegroundColor Gray

