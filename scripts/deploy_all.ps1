# ============================================================================
# MASTER DEPLOYMENT SCRIPT - Sales Intelligence Automation System
# ============================================================================
# This script deploys ALL Cloud Functions (Phase 1 + Phase 2) to GCP
# 
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. GCP_PROJECT_ID environment variable set (or edit below)
#   3. Service account created with required permissions
#   4. Required APIs enabled
#   5. BigQuery dataset and tables created
#   6. Secrets configured in Secret Manager
#
# Usage:
#   .\scripts\deploy_all.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURATION - Update these values for your environment
# ============================================================================
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "YOUR_PROJECT_ID" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intelligence-sa" }
$SERVICE_ACCOUNT = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Validate configuration
if ($PROJECT_ID -eq "YOUR_PROJECT_ID" -or -not $PROJECT_ID) {
    Write-Host "[ERROR] GCP_PROJECT_ID not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:GCP_PROJECT_ID = 'your-project-id'" -ForegroundColor Yellow
    Write-Host "Or edit this script and set `$PROJECT_ID directly" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Yellow
}

function Deploy-Function {
    param(
        [string]$FunctionName,
        [string]$EntryPoint,
        [string]$Description,
        [int]$MemoryMB = 512,
        [int]$TimeoutSeconds = 540,
        [int]$MaxInstances = 10,
        [string[]]$AdditionalEnvVars = @()
    )
    
    Write-Step "Deploying $FunctionName ($Description)"
    Write-Host "  Entry Point: $EntryPoint" -ForegroundColor Gray
    Write-Host "  Memory: ${MemoryMB}MB, Timeout: ${TimeoutSeconds}s" -ForegroundColor Gray
    
    # Build environment variables
    $envVars = @(
        "GCP_PROJECT_ID=$PROJECT_ID",
        "GCP_REGION=$REGION"
    )
    $envVars += $AdditionalEnvVars
    
    $envVarsString = $envVars -join ","
    
    # Deploy function
    $deployCommand = @(
        "gcloud", "functions", "deploy", $FunctionName,
        "--gen2",
        "--runtime=python311",
        "--region=$REGION",
        "--source=.",
        "--entry-point=$EntryPoint",
        "--trigger-http",
        "--no-allow-unauthenticated",
        "--service-account=$SERVICE_ACCOUNT",
        "--memory=${MemoryMB}MB",
        "--timeout=${TimeoutSeconds}s",
        "--max-instances=$MaxInstances",
        "--min-instances=0",
        "--set-env-vars=$envVarsString",
        "--project=$PROJECT_ID"
    )
    
    try {
        & $deployCommand[0] $deployCommand[1..($deployCommand.Length-1)]
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [✓] Successfully deployed $FunctionName" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  [✗] Failed to deploy $FunctionName (exit code: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  [✗] Error deploying $FunctionName : $_" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# MAIN DEPLOYMENT
# ============================================================================

Write-Header "Sales Intelligence System - Master Deployment"
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Service Account: $SERVICE_ACCOUNT" -ForegroundColor Yellow

# Ensure we're in project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

if (-not (Test-Path "main.py") -and -not (Test-Path "config\config.py")) {
    Write-Host "[ERROR] Not in project root! Expected to find main.py or config\config.py" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    exit 1
}

Write-Host "Project root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# PHASE 1: DATA INGESTION FUNCTIONS
# ============================================================================

Write-Header "Phase 1: Data Ingestion Functions"

$phase1Functions = @(
    @{
        Name = "gmail-sync"
        EntryPoint = "cloud_functions.gmail_sync.main.gmail_sync"
        Description = "Gmail message ingestion"
        MemoryMB = 512
        TimeoutSeconds = 540
    },
    @{
        Name = "salesforce-sync"
        EntryPoint = "cloud_functions.salesforce_sync.main.salesforce_sync"
        Description = "Salesforce object ingestion"
        MemoryMB = 512
        TimeoutSeconds = 540
    },
    @{
        Name = "dialpad-sync"
        EntryPoint = "cloud_functions.dialpad_sync.main.dialpad_sync"
        Description = "Dialpad call logs ingestion"
        MemoryMB = 512
        TimeoutSeconds = 540
    },
    @{
        Name = "hubspot-sync"
        EntryPoint = "cloud_functions.hubspot_sync.main.hubspot_sync"
        Description = "HubSpot sequences ingestion"
        MemoryMB = 512
        TimeoutSeconds = 300
    },
    @{
        Name = "entity-resolution"
        EntryPoint = "cloud_functions.entity_resolution.main.entity_resolution"
        Description = "Entity resolution and matching"
        MemoryMB = 1024
        TimeoutSeconds = 540
    }
)

$phase1Results = @{}
foreach ($func in $phase1Functions) {
    $success = Deploy-Function `
        -FunctionName $func.Name `
        -EntryPoint $func.EntryPoint `
        -Description $func.Description `
        -MemoryMB $func.MemoryMB `
        -TimeoutSeconds $func.TimeoutSeconds
    $phase1Results[$func.Name] = $success
}

# ============================================================================
# PHASE 2: INTELLIGENCE & AUTOMATION FUNCTIONS
# ============================================================================

Write-Header "Phase 2: Intelligence & Automation Functions"

$phase2Functions = @(
    @{
        Name = "generate-embeddings"
        EntryPoint = "intelligence.embeddings.main.generate_embeddings"
        Description = "Generate vector embeddings for emails and calls"
        MemoryMB = 1024
        TimeoutSeconds = 540
        AdditionalEnvVars = @("LLM_PROVIDER=vertex_ai", "EMBEDDING_PROVIDER=vertex_ai")
    },
    @{
        Name = "account-scoring"
        EntryPoint = "intelligence.scoring.main.account_scoring_job"
        Description = "AI-powered account scoring and prioritization"
        MemoryMB = 2048
        TimeoutSeconds = 540
        MaxInstances = 3
        AdditionalEnvVars = @("LLM_PROVIDER=vertex_ai")
    },
    @{
        Name = "nlp-query"
        EntryPoint = "intelligence.nlp_query.main.nlp_query"
        Description = "Natural language to SQL query conversion"
        MemoryMB = 1024
        TimeoutSeconds = 60
        AdditionalEnvVars = @("LLM_PROVIDER=vertex_ai")
    },
    @{
        Name = "semantic-search"
        EntryPoint = "intelligence.vector_search.main.semantic_search"
        Description = "Semantic search using vector embeddings"
        MemoryMB = 1024
        TimeoutSeconds = 60
        AdditionalEnvVars = @("EMBEDDING_PROVIDER=vertex_ai")
    },
    @{
        Name = "create-leads"
        EntryPoint = "intelligence.automation.main.create_leads"
        Description = "Create Salesforce leads from unmatched emails"
        MemoryMB = 512
        TimeoutSeconds = 300
    },
    @{
        Name = "enroll-hubspot"
        EntryPoint = "intelligence.automation.main.enroll_hubspot"
        Description = "Enroll contacts in HubSpot sequences"
        MemoryMB = 512
        TimeoutSeconds = 300
    },
    @{
        Name = "get-hubspot-sequences"
        EntryPoint = "intelligence.automation.main.get_hubspot_sequences"
        Description = "Get available HubSpot sequences"
        MemoryMB = 512
        TimeoutSeconds = 60
    },
    @{
        Name = "generate-email-reply"
        EntryPoint = "intelligence.email_replies.main.generate_email_reply"
        Description = "Generate AI email replies"
        MemoryMB = 1024
        TimeoutSeconds = 120
        AdditionalEnvVars = @("LLM_PROVIDER=vertex_ai")
    }
)

$phase2Results = @{}
foreach ($func in $phase2Functions) {
    $success = Deploy-Function `
        -FunctionName $func.Name `
        -EntryPoint $func.EntryPoint `
        -Description $func.Description `
        -MemoryMB $func.MemoryMB `
        -TimeoutSeconds $func.TimeoutSeconds `
        -MaxInstances $func.MaxInstances `
        -AdditionalEnvVars $func.AdditionalEnvVars
    $phase2Results[$func.Name] = $success
}

# ============================================================================
# CONFIGURE IAM PERMISSIONS
# ============================================================================

Write-Header "Configuring IAM Permissions"

$allFunctions = $phase1Functions + $phase2Functions
$successfulFunctions = @()

foreach ($func in $allFunctions) {
    $phase1Success = if ($phase1Results.ContainsKey($func.Name)) { $phase1Results[$func.Name] } else { $false }
    $phase2Success = if ($phase2Results.ContainsKey($func.Name)) { $phase2Results[$func.Name] } else { $false }
    
    if ($phase1Success -or $phase2Success) {
        $successfulFunctions += $func.Name
    }
}

Write-Step "Granting Cloud Scheduler permission to invoke functions"
foreach ($funcName in $successfulFunctions) {
    try {
        gcloud functions add-iam-policy-binding $funcName `
            --region=$REGION `
            --member="serviceAccount:$SERVICE_ACCOUNT" `
            --role="roles/cloudfunctions.invoker" `
            --project=$PROJECT_ID 2>&1 | Out-Null
        
        Write-Host "  [✓] IAM policy set for $funcName" -ForegroundColor Green
    } catch {
        Write-Host "  [⚠] Could not set IAM policy for $funcName : $_" -ForegroundColor Yellow
    }
}

# Grant public access for web app functions (optional - adjust based on security requirements)
Write-Step "Granting public access for web app functions (if needed)"
$publicFunctions = @("nlp-query", "get-hubspot-sequences", "semantic-search")
foreach ($funcName in $publicFunctions) {
    if ($successfulFunctions -contains $funcName) {
        try {
            gcloud functions add-iam-policy-binding $funcName `
                --region=$REGION `
                --member="allUsers" `
                --role="roles/cloudfunctions.invoker" `
                --project=$PROJECT_ID 2>&1 | Out-Null
            
            Write-Host "  [✓] Public access granted for $funcName" -ForegroundColor Green
        } catch {
            Write-Host "  [⚠] Could not grant public access for $funcName : $_" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

Write-Header "Deployment Summary"

Write-Host "Phase 1 Functions:" -ForegroundColor Cyan
foreach ($func in $phase1Functions) {
    $status = if ($phase1Results[$func.Name]) { "✓ Success" } else { "✗ Failed" }
    $color = if ($phase1Results[$func.Name]) { "Green" } else { "Red" }
    Write-Host "  $($func.Name): $status" -ForegroundColor $color
}

Write-Host ""
Write-Host "Phase 2 Functions:" -ForegroundColor Cyan
foreach ($func in $phase2Functions) {
    $status = if ($phase2Results[$func.Name]) { "✓ Success" } else { "✗ Failed" }
    $color = if ($phase2Results[$func.Name]) { "Green" } else { "Red" }
    Write-Host "  $($func.Name): $status" -ForegroundColor $color
}

$allPhase1Success = ($phase1Results.Values | Where-Object { $_ -eq $false }).Count -eq 0
$allPhase2Success = ($phase2Results.Values | Where-Object { $_ -eq $false }).Count -eq 0
$allSuccess = $allPhase1Success -and $allPhase2Success

Write-Host ""
if ($allSuccess) {
    Write-Host "[✓] All functions deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Verify functions: gcloud functions list --gen2 --region=$REGION --project=$PROJECT_ID" -ForegroundColor Yellow
    Write-Host "  2. Test a function: gcloud functions call gmail-sync --gen2 --region=$REGION --project=$PROJECT_ID" -ForegroundColor Yellow
    Write-Host "  3. Create Cloud Scheduler jobs (see CLIENT_DEPLOYMENT_GUIDE.md)" -ForegroundColor Yellow
    Write-Host "  4. Deploy web application (see CLIENT_DEPLOYMENT_GUIDE.md)" -ForegroundColor Yellow
} else {
    Write-Host "[⚠] Some functions failed to deploy. Review errors above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "  1. Check logs: gcloud functions logs read FUNCTION_NAME --gen2 --region=$REGION --limit=50" -ForegroundColor Yellow
    Write-Host "  2. Verify service account permissions" -ForegroundColor Yellow
    Write-Host "  3. Ensure all required APIs are enabled" -ForegroundColor Yellow
    Write-Host "  4. Check TROUBLESHOOTING.md for common issues" -ForegroundColor Yellow
}

Write-Header "Deployment Complete"
