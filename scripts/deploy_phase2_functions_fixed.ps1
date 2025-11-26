# Deploy Phase 2 Intelligence & Automation Cloud Functions (Fixed)
# Deploys from project root with correct entry points

$ErrorActionPreference = "Continue"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intel-poc-sa" }
$SERVICE_ACCOUNT = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploying Phase 2 Cloud Functions" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "Region: $REGION" -ForegroundColor Green
Write-Host "Service Account: $SERVICE_ACCOUNT" -ForegroundColor Green
Write-Host ""

# Get project root
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $PROJECT_ROOT
Write-Host "Project root: $PROJECT_ROOT" -ForegroundColor Yellow
Write-Host ""

# Functions to deploy with their configurations
$functions = @(
    @{
        Name = "generate-embeddings"
        EntryPoint = "intelligence.embeddings.main.generate_embeddings"
        Memory = "1024MB"
        Timeout = "540s"
        MaxInstances = 5
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,LLM_PROVIDER=vertex_ai,EMBEDDING_PROVIDER=vertex_ai"
    },
    @{
        Name = "account-scoring"
        EntryPoint = "intelligence.scoring.main.account_scoring_job"
        Memory = "2048MB"
        Timeout = "540s"
        MaxInstances = 3
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,LLM_PROVIDER=vertex_ai"
    },
    @{
        Name = "nlp-query"
        EntryPoint = "intelligence.nlp_query.main.nlp_query"
        Memory = "1024MB"
        Timeout = "60s"
        MaxInstances = 10
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,LLM_PROVIDER=vertex_ai"
    },
    @{
        Name = "create-leads"
        EntryPoint = "intelligence.automation.main.create_leads"
        Memory = "512MB"
        Timeout = "300s"
        MaxInstances = 5
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION"
    },
    @{
        Name = "enroll-hubspot"
        EntryPoint = "intelligence.automation.main.enroll_hubspot"
        Memory = "512MB"
        Timeout = "300s"
        MaxInstances = 5
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION"
    },
    @{
        Name = "get-hubspot-sequences"
        EntryPoint = "intelligence.automation.main.get_hubspot_sequences"
        Memory = "512MB"
        Timeout = "60s"
        MaxInstances = 10
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION"
    },
    @{
        Name = "generate-email-reply"
        EntryPoint = "intelligence.email_replies.main.generate_email_reply"
        Memory = "1024MB"
        Timeout = "120s"
        MaxInstances = 10
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,LLM_PROVIDER=vertex_ai"
    },
    @{
        Name = "semantic-search"
        EntryPoint = "intelligence.vector_search.main.semantic_search"
        Memory = "1024MB"
        Timeout = "60s"
        MaxInstances = 10
        EnvVars = "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,EMBEDDING_PROVIDER=vertex_ai"
    }
)

$deployed = 0
$failed = 0

foreach ($func in $functions) {
    Write-Host "Deploying $($func.Name)..." -ForegroundColor Yellow
    try {
        gcloud functions deploy $func.Name `
            --gen2 `
            --runtime=python311 `
            --region=$REGION `
            --source=. `
            --entry-point=$func.EntryPoint `
            --trigger-http `
            --service-account=$SERVICE_ACCOUNT `
            --memory=$func.Memory `
            --timeout=$func.Timeout `
            --max-instances=$func.MaxInstances `
            --min-instances=0 `
            --set-env-vars=$func.EnvVars `
            --project=$PROJECT_ID `
            --allow-unauthenticated 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $($func.Name) deployed successfully" -ForegroundColor Green
            $deployed++
        } else {
            Write-Host "  ❌ $($func.Name) deployment failed" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ❌ $($func.Name) deployment error: $_" -ForegroundColor Red
        $failed++
    }
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployed: $deployed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All functions deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Create Cloud Scheduler jobs for daily scoring" -ForegroundColor Yellow
    Write-Host "2. Test account-scoring function" -ForegroundColor Yellow
    Write-Host "3. Verify web app can access functions" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ Some functions failed to deploy" -ForegroundColor Yellow
    Write-Host "Check logs above for details" -ForegroundColor Yellow
}

