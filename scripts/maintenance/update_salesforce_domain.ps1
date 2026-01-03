# Update Salesforce domain to sandbox (test.salesforce.com)
# PowerShell version - Run this to configure Cloud Function for Salesforce sandbox

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intel-poc-sa" }
$SERVICE_ACCOUNT = "$SERVICE_ACCOUNT_NAME@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Updating Salesforce Sync for Sandbox" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Domain: test.salesforce.com (sandbox)" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $PROJECT_ROOT

# Redeploy Salesforce Sync with sandbox domain
Write-Host "Redeploying Salesforce Sync Function with sandbox domain..." -ForegroundColor Yellow
gcloud functions deploy salesforce-sync `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=salesforce_sync `
  --trigger-http `
  --service-account=$SERVICE_ACCOUNT `
  --memory=512MB `
  --timeout=540s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,SALESFORCE_DOMAIN=test" `
  --project=$PROJECT_ID

Write-Host ""
Write-Host "✅ Salesforce Sync updated to use sandbox domain (test.salesforce.com)!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 To use production domain instead, set SALESFORCE_DOMAIN=login and redeploy" -ForegroundColor Yellow
Write-Host "   Example: `$env:SALESFORCE_DOMAIN='login'; .\scripts\update_salesforce_domain.ps1" -ForegroundColor Gray
Write-Host ""

