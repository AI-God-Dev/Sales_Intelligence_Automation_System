# Deploy Phase 2 Intelligence & Automation Cloud Functions (PowerShell)
# IMPORTANT: Deploys from project root to include shared modules

$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$DATASET_NAME = if ($env:BQ_DATASET_NAME) { $env:BQ_DATASET_NAME } elseif ($env:BIGQUERY_DATASET) { $env:BIGQUERY_DATASET } else { "sales_intelligence" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intel-poc-sa" }
$SERVICE_ACCOUNT = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

Write-Host "Deploying Phase 2 Cloud Functions to project: $PROJECT_ID" -ForegroundColor Green
Write-Host "Using service account: $SERVICE_ACCOUNT" -ForegroundColor Green

# Get project root - use current directory if script is run from project root, otherwise calculate
if (Test-Path "main.py") {
    $PROJECT_ROOT = Get-Location
    Write-Host "Using current directory as project root: $PROJECT_ROOT" -ForegroundColor Gray
} else {
    # Try to find project root relative to script location
    $scriptPath = $MyInvocation.MyCommand.Path
    if ($scriptPath) {
        $PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $scriptPath)
    } else {
        # Fallback: assume we're in scripts directory
        $PROJECT_ROOT = Split-Path -Parent (Get-Location)
    }
    Set-Location $PROJECT_ROOT
    Write-Host "Changed to project root: $PROJECT_ROOT" -ForegroundColor Gray
}

# Verify main.py exists
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found in $PROJECT_ROOT" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Deploy Embeddings Generator
Write-Host "Deploying Embeddings Generator Function..." -ForegroundColor Yellow
gcloud functions deploy generate-embeddings `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=generate_embeddings `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=1024MB `
  --timeout=540s `
  --max-instances=5 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro,EMBEDDING_PROVIDER=vertex_ai" `
  --project=$PROJECT_ID

# Deploy Account Scoring Function
Write-Host "Deploying Account Scoring Function..." -ForegroundColor Yellow
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
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" `
  --project=$PROJECT_ID

# Deploy NLP Query Function
Write-Host "Deploying NLP Query Function..." -ForegroundColor Yellow
gcloud functions deploy nlp-query `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=nlp_query `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=1024MB `
  --timeout=60s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" `
  --project=$PROJECT_ID

# Deploy Lead Creation Function
Write-Host "Deploying Lead Creation Function..." -ForegroundColor Yellow
gcloud functions deploy create-leads `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=create_leads `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=512MB `
  --timeout=300s `
  --max-instances=5 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" `
  --project=$PROJECT_ID

# Deploy HubSpot Enrollment Function
Write-Host "Deploying HubSpot Enrollment Function..." -ForegroundColor Yellow
gcloud functions deploy enroll-hubspot `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=enroll_hubspot `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=512MB `
  --timeout=300s `
  --max-instances=5 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" `
  --project=$PROJECT_ID

# Deploy Get HubSpot Sequences Function
Write-Host "Deploying Get HubSpot Sequences Function..." -ForegroundColor Yellow
gcloud functions deploy get-hubspot-sequences `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=get_hubspot_sequences `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=512MB `
  --timeout=60s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME" `
  --project=$PROJECT_ID

# Deploy Email Reply Generator Function
Write-Host "Deploying Email Reply Generator Function..." -ForegroundColor Yellow
gcloud functions deploy generate-email-reply `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=generate_email_reply `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=1024MB `
  --timeout=120s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,LLM_PROVIDER=vertex_ai,LLM_MODEL=gemini-2.5-pro" `
  --project=$PROJECT_ID

# Deploy Semantic Search Function
Write-Host "Deploying Semantic Search Function..." -ForegroundColor Yellow
gcloud functions deploy semantic-search `
  --gen2 `
  --runtime=python311 `
  --region=$REGION `
  --source=. `
  --entry-point=semantic_search `
  --trigger-http `
  --no-allow-unauthenticated `
  --service-account=$SERVICE_ACCOUNT `
  --memory=1024MB `
  --timeout=60s `
  --max-instances=10 `
  --min-instances=0 `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,BQ_DATASET_NAME=$DATASET_NAME,EMBEDDING_PROVIDER=vertex_ai" `
  --project=$PROJECT_ID

# Grant Cloud Scheduler permission to invoke functions
Write-Host "Granting Cloud Scheduler permission to invoke functions..." -ForegroundColor Yellow
$functions = @("generate-embeddings", "account-scoring", "nlp-query", "create-leads", "enroll-hubspot", "get-hubspot-sequences", "generate-email-reply", "semantic-search")
foreach ($func in $functions) {
    try {
        gcloud functions add-iam-policy-binding $func `
          --region=$REGION `
          --member="serviceAccount:$SERVICE_ACCOUNT" `
          --role="roles/cloudfunctions.invoker" `
          --project=$PROJECT_ID
    } catch {
        Write-Host "Warning: Could not add IAM binding for $func" -ForegroundColor Yellow
    }
}

# Grant public access for web app (or use authenticated access)
Write-Host "Granting public access for web app integration..." -ForegroundColor Yellow
$publicFunctions = @("nlp-query", "get-hubspot-sequences", "semantic-search")
foreach ($func in $publicFunctions) {
    try {
        gcloud functions add-iam-policy-binding $func `
          --region=$REGION `
          --member="allUsers" `
          --role="roles/cloudfunctions.invoker" `
          --project=$PROJECT_ID
    } catch {
        Write-Host "Warning: Could not add public access for $func" -ForegroundColor Yellow
    }
}

Write-Host "Phase 2 deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Enable Vertex AI API: gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID"
Write-Host "2. Verify service account has Vertex AI User role"
Write-Host "3. Create Cloud Scheduler jobs for daily scoring and embeddings"
Write-Host "4. Deploy web application"

