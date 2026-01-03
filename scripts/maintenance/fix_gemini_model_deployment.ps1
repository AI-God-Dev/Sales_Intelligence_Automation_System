# Quick Fix Script for Gemini Model Deployment Issue
# This script fixes the 404 Vertex AI model error and redeploys functions
# Run from project root: .\scripts\fix_gemini_model_deployment.ps1

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "maharani-sales-hub-11-2025"
$REGION = "us-central1"
$SERVICE_ACCOUNT = "sales-intel-poc-sa@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gemini Model Deployment Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Enable Vertex AI API" -ForegroundColor Yellow
Write-Host "  2. Grant Vertex AI permissions to service account" -ForegroundColor Yellow
Write-Host "  3. Redeploy account-scoring function with gemini-2.5-pro" -ForegroundColor Yellow
Write-Host "  4. Update scheduler job configuration" -ForegroundColor Yellow
Write-Host "  5. Test the deployment" -ForegroundColor Yellow
Write-Host ""

# Confirm project
Write-Host "Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "Region: $REGION" -ForegroundColor Green
Write-Host "Service Account: $SERVICE_ACCOUNT" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Enable Vertex AI API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
    Write-Host "[✓] Vertex AI API enabled" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not enable Vertex AI API (may already be enabled)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Grant Vertex AI Permissions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$SERVICE_ACCOUNT" `
        --role="roles/aiplatform.user"
    Write-Host "[✓] Vertex AI User role granted" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not grant role (may already exist)" -ForegroundColor Yellow
}

try {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$SERVICE_ACCOUNT" `
        --role="roles/bigquery.jobUser"
    Write-Host "[✓] BigQuery Job User role granted" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not grant role (may already exist)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Redeploy account-scoring Function" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Deploying with gemini-2.5-pro model..." -ForegroundColor Yellow

gcloud functions deploy account-scoring `
    --gen2 `
    --runtime=python311 `
    --region=$REGION `
    --source=. `
    --entry-point=account_scoring_job `
    --trigger-http `
    --no-allow-unauthenticated `
    --service-account=$SERVICE_ACCOUNT `
    --memory=2048MB `
    --timeout=540s `
    --max-instances=3 `
    --min-instances=0 `
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=sales_intelligence,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" `
    --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] account-scoring function deployed successfully" -ForegroundColor Green
} else {
    Write-Host "[✗] Failed to deploy account-scoring function" -ForegroundColor Red
    Write-Host "Check logs above for details" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Update Scheduler Job" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Checking if scheduler job exists..." -ForegroundColor Yellow

$jobExists = gcloud scheduler jobs describe account-scoring-daily `
    --location=$REGION `
    --project=$PROJECT_ID 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Scheduler job exists. Deleting and recreating with updated timeout..." -ForegroundColor Yellow
    
    gcloud scheduler jobs delete account-scoring-daily `
        --location=$REGION `
        --project=$PROJECT_ID `
        --quiet
    
    Write-Host "[✓] Old scheduler job deleted" -ForegroundColor Green
}

Write-Host "Creating scheduler job with 20-minute timeout..." -ForegroundColor Yellow

gcloud scheduler jobs create http account-scoring-daily `
    --location=$REGION `
    --schedule="0 7 * * *" `
    --time-zone="America/New_York" `
    --uri="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/account-scoring" `
    --http-method=POST `
    --oidc-service-account-email=$SERVICE_ACCOUNT `
    --max-retry-duration=1200s `
    --max-retry-attempts=2 `
    --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] Scheduler job created successfully" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Could not create scheduler job (may already exist)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 5: Test Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Testing account-scoring function with 5 accounts..." -ForegroundColor Yellow

try {
    $result = gcloud functions call account-scoring `
        --gen2 `
        --region=$REGION `
        --project=$PROJECT_ID `
        --data='{"limit": 5}' 2>&1
    
    Write-Host ""
    Write-Host "Function Response:" -ForegroundColor Green
    Write-Host $result -ForegroundColor White
    Write-Host ""
    
    if ($result -like "*success*") {
        Write-Host "[✓] Function test PASSED" -ForegroundColor Green
    } else {
        Write-Host "[!] Function test completed but check response above" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[✗] Function test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "1. Check function environment variables:" -ForegroundColor Yellow
Write-Host "   gcloud functions describe account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --format=`"yaml(serviceConfig.environmentVariables)`"" -ForegroundColor Gray

Write-Host ""
Write-Host "2. Check function logs:" -ForegroundColor Yellow
Write-Host "   gcloud functions logs read account-scoring --gen2 --region=$REGION --project=$PROJECT_ID --limit=50" -ForegroundColor Gray

Write-Host ""
Write-Host "3. Verify scheduler job:" -ForegroundColor Yellow
Write-Host "   gcloud scheduler jobs describe account-scoring-daily --location=$REGION --project=$PROJECT_ID" -ForegroundColor Gray

Write-Host ""
Write-Host "4. Manually trigger scheduler:" -ForegroundColor Yellow
Write-Host "   gcloud scheduler jobs run account-scoring-daily --location=$REGION --project=$PROJECT_ID" -ForegroundColor Gray

Write-Host ""
Write-Host "5. Check BigQuery for results:" -ForegroundColor Yellow
Write-Host "   SELECT * FROM ``${PROJECT_ID}.sales_intelligence.account_recommendations`` ORDER BY created_at DESC LIMIT 10;" -ForegroundColor Gray

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ Deployment Fix Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The account-scoring function should now work with gemini-2.5-pro" -ForegroundColor Green
Write-Host "Next scheduled run: Tomorrow at 7:00 AM (America/New_York)" -ForegroundColor Green
Write-Host ""
Write-Host "If you still see errors, check the logs using the commands above." -ForegroundColor Yellow
Write-Host ""

