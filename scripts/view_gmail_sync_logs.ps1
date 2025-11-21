# View real-time logs for Gmail sync Cloud Function
# PowerShell version - For Gen2 Cloud Functions (Cloud Run)

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$FUNCTION_NAME = "gmail-sync"

Write-Host "Viewing real-time logs for: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop watching logs" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# For Gen2 functions (Cloud Run), use Cloud Run service name
# Real-time log streaming using Cloud Run logging
$filter = "resource.type=cloud_run_revision AND resource.labels.service_name=$FUNCTION_NAME"

gcloud logging tail $filter `
    --project=$PROJECT_ID `
    --format="table(timestamp,severity,textPayload)"

