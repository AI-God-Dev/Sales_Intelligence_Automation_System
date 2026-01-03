# Complete HubSpot ingestion: Redeploy with increased memory and trigger ingestion
# This script:
# 1. Redeploys HubSpot sync with 1GB memory
# 2. Waits for deployment to complete
# 3. Triggers HubSpot ingestion
# 4. Monitors logs for success/failure

param(
    [string]$ProjectId = "maharani-sales-hub-11-2025",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

$ServiceAccount = "sales-intel-poc-sa@${ProjectId}.iam.gserviceaccount.com"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "HubSpot Ingestion - Complete Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host "Service Account: $ServiceAccount"
Write-Host ""

# Step 1: Redeploy HubSpot sync with 1GB memory
Write-Host "Step 1: Redeploying HubSpot sync with 1GB memory..." -ForegroundColor Yellow
Write-Host ""

$deployArgs = @(
    "functions", "deploy", "hubspot-sync",
    "--gen2",
    "--runtime=python311",
    "--region=$Region",
    "--source=.",
    "--entry-point=hubspot_sync",
    "--trigger-http",
    "--service-account=$ServiceAccount",
    "--memory=1024MB",
    "--timeout=540s",
    "--max-instances=10",
    "--min-instances=0",
    "--set-env-vars=GCP_PROJECT_ID=$ProjectId,GCP_REGION=$Region",
    "--project=$ProjectId"
)

& gcloud $deployArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy HubSpot sync function" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ HubSpot sync deployed successfully with 1GB memory" -ForegroundColor Green
Write-Host ""

# Step 2: Wait for deployment to be ready
Write-Host "Step 2: Waiting for deployment to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verify deployment
Write-Host "Verifying deployment status..." -ForegroundColor Yellow
try {
    $deployStatus = gcloud functions describe hubspot-sync --region=$Region --project=$ProjectId --format="value(state)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $deployStatus = "UNKNOWN"
    }
} catch {
    $deployStatus = "UNKNOWN"
}

Write-Host "Deployment status: $deployStatus"
Write-Host ""

# Step 3: Get access token for triggering
Write-Host "Step 3: Preparing to trigger HubSpot ingestion..." -ForegroundColor Yellow
$token = gcloud auth print-access-token
if (-not $token -or $LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to get access token. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}

# Step 4: Trigger HubSpot sync
Write-Host "Step 4: Triggering HubSpot ingestion..." -ForegroundColor Yellow
Write-Host ""

$functionName = "hubspot-sync"
$url = "https://${Region}-${ProjectId}.cloudfunctions.net/${functionName}"
$body = '{"sync_type":"full"}'

Write-Host "URL: $url"
Write-Host "Payload: $body"
Write-Host ""

$httpCode = $null
$responseBody = $null

try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ErrorAction Stop
    $httpCode = 200
    $responseBody = ($response | ConvertTo-Json -Depth 10)
} catch {
    if ($_.Exception.Response) {
        $httpCode = [int]$_.Exception.Response.StatusCode.value__
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
        } catch {
            $responseBody = $_.Exception.Message
        }
    } else {
        $httpCode = 500
        $responseBody = $_.Exception.Message
    }
}

Write-Host "HTTP Status Code: $httpCode"
Write-Host "Response Body: $responseBody"
Write-Host ""

if ($httpCode -eq 200 -or $httpCode -eq 202) {
    Write-Host "✓ Successfully triggered HubSpot ingestion (HTTP $httpCode)" -ForegroundColor Green
    Write-Host ""
    
    # Step 5: Monitor logs
    Write-Host "Step 5: Monitoring ingestion progress..." -ForegroundColor Yellow
    Write-Host "Waiting 30 seconds before checking logs..."
    Start-Sleep -Seconds 30
    
    Write-Host ""
    Write-Host "Recent HubSpot sync logs:" -ForegroundColor Yellow
    Write-Host "----------------------------------------"
    
    # Try to get logs
    $logCmd = "gcloud functions logs read hubspot-sync --region=$Region --project=$ProjectId --limit=20 --format=`"table(timestamp,severity,textPayload)`" 2>&1"
    $logOutput = Invoke-Expression $logCmd
    if ($LASTEXITCODE -ne 0) {
        $logCmd2 = "gcloud logging read `"resource.type=cloud_function AND resource.labels.function_name=hubspot-sync`" --project=$ProjectId --limit=20 --format=`"table(timestamp,severity,textPayload)`" 2>&1"
        $logOutput = Invoke-Expression $logCmd2
    }
    Write-Host $logOutput
    
    Write-Host "----------------------------------------"
    Write-Host ""
    
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "HubSpot Ingestion Setup Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To view detailed logs, run:" -ForegroundColor Cyan
    Write-Host "  gcloud functions logs read hubspot-sync --region=$Region --project=$ProjectId --limit=50"
    Write-Host ""
    Write-Host "Or check in Cloud Console:" -ForegroundColor Cyan
    Write-Host "  https://console.cloud.google.com/functions/details/$Region/hubspot-sync?project=$ProjectId"
    Write-Host ""
} else {
    Write-Host "✗ Failed to trigger HubSpot ingestion (HTTP $httpCode)" -ForegroundColor Red
    Write-Host "Response: $responseBody"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if you have invoke permissions:"
    Write-Host "   .\scripts\grant_user_invoker_permission.ps1"
    Write-Host "2. Check function status:"
    Write-Host "   gcloud functions describe hubspot-sync --region=$Region --project=$ProjectId"
    exit 1
}
