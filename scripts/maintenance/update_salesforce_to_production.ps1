# Update Salesforce from Sandbox to Production
# Client can run this themselves to switch to production

$ErrorActionPreference = "Stop"

$PROJECT_ID = $env:GCP_PROJECT_ID
if (-not $PROJECT_ID) {
    $PROJECT_ID = "maharani-sales-hub-11-2025"
}

$REGION = $env:GCP_REGION
if (-not $REGION) {
    $REGION = "us-central1"
}

$SERVICE_ACCOUNT = "sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Switching Salesforce to Production" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host ""

# Step 1: Prompt for secret updates
Write-Host "Step 1: Update Salesforce Secrets" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "Run these commands to update secrets (replace with your production values):" -ForegroundColor White
Write-Host ""
Write-Host '  "YOUR_PRODUCTION_USERNAME" | gcloud secrets versions add salesforce-username --data-file=-' -ForegroundColor Gray
Write-Host '  "YOUR_PRODUCTION_PASSWORD" | gcloud secrets versions add salesforce-password --data-file=-' -ForegroundColor Gray
Write-Host '  "YOUR_PRODUCTION_SECURITY_TOKEN" | gcloud secrets versions add salesforce-security-token --data-file=-' -ForegroundColor Gray
Write-Host ""
$response = Read-Host "Have you updated the secrets? (y/n)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "Please update secrets first, then run this script again." -ForegroundColor Red
    exit 1
}

# Step 2: Redeploy with production domain
Write-Host ""
Write-Host "Step 2: Redeploying Salesforce Sync with Production Domain..." -ForegroundColor Yellow
Write-Host ""

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
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,SALESFORCE_DOMAIN=login" `
  --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy salesforce-sync function" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Salesforce sync deployed successfully with production domain (login)" -ForegroundColor Green
Write-Host ""

# Step 3: Wait for deployment
Write-Host "Step 3: Waiting for deployment to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 4: Test sync
Write-Host ""
Write-Host "Step 4: Testing Salesforce sync..." -ForegroundColor Yellow
Write-Host ""

$TOKEN = gcloud auth print-access-token
$FUNCTION_NAME = "salesforce-sync"
$URL = "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"

$body = @{
    sync_type = "full"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $URL -Method Post -Headers @{
        "Authorization" = "Bearer $TOKEN"
        "Content-Type" = "application/json"
    } -Body $body
    
    Write-Host "✓ Successfully triggered Salesforce sync" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting 30 seconds before checking logs..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
    Write-Host ""
    Write-Host "Recent Salesforce sync logs:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    gcloud functions logs read salesforce-sync --gen2 --region=$REGION --project=$PROJECT_ID --limit=20
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Salesforce Production Switch Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verify data in BigQuery:" -ForegroundColor Yellow
    Write-Host '  bq query "SELECT COUNT(*) FROM sales_intelligence.sf_accounts"' -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "✗ Failed to trigger Salesforce sync" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the logs for details:" -ForegroundColor Yellow
    Write-Host "  gcloud functions logs read salesforce-sync --gen2 --region=$REGION --project=$PROJECT_ID --limit=50" -ForegroundColor Gray
    exit 1
}

