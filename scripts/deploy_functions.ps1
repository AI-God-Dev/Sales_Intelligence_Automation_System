# Deploy All Cloud Functions to GCP
# Deploys from project root to include shared modules (utils, config, entity_resolution)

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$serviceAccount = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Cloud Functions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host "Region: $region" -ForegroundColor Yellow
Write-Host "Service Account: $serviceAccount" -ForegroundColor Yellow
Write-Host ""

# Ensure we're in project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Function to deploy a Cloud Function
function Deploy-Function {
    param(
        [string]$FunctionName,
        [string]$EntryPoint,
        [string]$Description
    )
    
    Write-Host "Deploying $FunctionName..." -ForegroundColor Yellow
    Write-Host "  Entry Point: $EntryPoint" -ForegroundColor Gray
    
    gcloud functions deploy $FunctionName `
        --gen2 `
        --runtime=python311 `
        --region=$region `
        --source=. `
        --entry-point=$EntryPoint `
        --trigger-http `
        --service-account=$serviceAccount `
        --memory=512MB `
        --timeout=540s `
        --max-instances=10 `
        --min-instances=0 `
        --set-env-vars="GCP_PROJECT_ID=$projectId,GCP_REGION=$region" `
        --project=$projectId
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [X] Failed to deploy $FunctionName" -ForegroundColor Red
        return $false
    }
    
    Write-Host "  [OK] Successfully deployed $FunctionName" -ForegroundColor Green
    Write-Host ""
    return $true
}

# Deploy all functions
$functions = @(
    @{
        Name = "gmail-sync"
        EntryPoint = "gmail_sync"
        Description = "Gmail message ingestion"
    },
    @{
        Name = "salesforce-sync"
        EntryPoint = "salesforce_sync"
        Description = "Salesforce object ingestion"
    },
    @{
        Name = "dialpad-sync"
        EntryPoint = "dialpad_sync"
        Description = "Dialpad call logs ingestion"
    },
    @{
        Name = "hubspot-sync"
        EntryPoint = "hubspot_sync"
        Description = "HubSpot sequences ingestion"
    },
    @{
        Name = "entity-resolution"
        EntryPoint = "entity_resolution"
        Description = "Entity resolution and matching"
    }
)

$deploymentResults = @{}
foreach ($func in $functions) {
    $success = Deploy-Function -FunctionName $func.Name -EntryPoint $func.EntryPoint -Description $func.Description
    $deploymentResults[$func.Name] = $success
}

# Grant Cloud Scheduler permission to invoke functions
Write-Host "Granting Cloud Scheduler permissions..." -ForegroundColor Yellow
foreach ($func in $functions) {
    if ($deploymentResults[$func.Name]) {
        Write-Host "  Setting IAM policy for $($func.Name)..." -ForegroundColor Gray
        gcloud functions add-iam-policy-binding $func.Name `
            --region=$region `
            --member="serviceAccount:$serviceAccount" `
            --role="roles/cloudfunctions.invoker" `
            --project=$projectId | Out-Null
    }
}
Write-Host "  [OK] IAM permissions set" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
foreach ($func in $functions) {
    $status = if ($deploymentResults[$func.Name]) { "Success" } else { "Failed" }
    $color = if ($deploymentResults[$func.Name]) { "Green" } else { "Red" }
    Write-Host "$($func.Name): $status" -ForegroundColor $color
}

$allSuccess = ($deploymentResults.Values | Where-Object { $_ -eq $false }).Count -eq 0
Write-Host ""
if ($allSuccess) {
    Write-Host "[OK] All functions deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Some functions failed to deploy. Check errors above." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

