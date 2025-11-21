# Redeploy Gmail Sync Function with rate limiting fixes
# PowerShell version

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intel-poc-sa" }
$SERVICE_ACCOUNT = "$SERVICE_ACCOUNT_NAME@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "Redeploying Gmail Sync Function with rate limiting improvements..." -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host "Service Account: $SERVICE_ACCOUNT" -ForegroundColor Gray
Write-Host ""

# Get project root
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $PROJECT_ROOT

# Deploy Gmail Sync Function
gcloud functions deploy gmail-sync `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=gmail_sync `
  --trigger-http `
  --service-account=$SERVICE_ACCOUNT `
  --memory=512MB `
  --timeout=540s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" `
  --project=$PROJECT_ID

Write-Host ""
Write-Host "✅ Gmail Sync Function redeployed with rate limiting fixes!" -ForegroundColor Green
Write-Host ""
Write-Host "The function now includes:" -ForegroundColor Yellow
Write-Host "  - Exponential backoff retry logic"
Write-Host "  - Rate limiting (0.25s delay between requests)"
Write-Host "  - Automatic retry on rate limit errors (up to 5 retries)"
Write-Host "  - Better error handling for failed messages"
Write-Host ""

