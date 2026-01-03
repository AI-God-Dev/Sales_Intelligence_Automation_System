# ============================================================================
# SERVICE ACCOUNT SETUP SCRIPT
# ============================================================================
# Creates service account and grants all required IAM roles for the
# Sales Intelligence Automation System
#
# Usage:
#   .\scripts\setup_service_account.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURATION
# ============================================================================
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "YOUR_PROJECT_ID" }
$SERVICE_ACCOUNT_NAME = if ($env:GCP_SERVICE_ACCOUNT_NAME) { $env:GCP_SERVICE_ACCOUNT_NAME } else { "sales-intelligence-sa" }
$SERVICE_ACCOUNT_EMAIL = "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
$YOUR_EMAIL = if ($env:GCP_USER_EMAIL) { $env:GCP_USER_EMAIL } else { "YOUR_EMAIL@example.com" }

# Validate configuration
if ($PROJECT_ID -eq "YOUR_PROJECT_ID" -or -not $PROJECT_ID) {
    Write-Host "[ERROR] GCP_PROJECT_ID not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:GCP_PROJECT_ID = 'your-project-id'" -ForegroundColor Yellow
    exit 1
}

if ($YOUR_EMAIL -eq "YOUR_EMAIL@example.com" -or -not $YOUR_EMAIL) {
    Write-Host "[ERROR] GCP_USER_EMAIL not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:GCP_USER_EMAIL = 'your-email@example.com'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service Account Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Yellow
Write-Host "Your Email: $YOUR_EMAIL" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# STEP 1: CREATE SERVICE ACCOUNT
# ============================================================================

Write-Host "Step 1: Creating service account..." -ForegroundColor Yellow

# Check if service account already exists
$existing = gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [✓] Service account already exists: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green
} else {
    # Create service account
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
        --display-name="Sales Intelligence Service Account" `
        --description="Service account for Sales Intelligence Cloud Functions" `
        --project=$PROJECT_ID
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [✓] Service account created successfully" -ForegroundColor Green
    } else {
        Write-Host "  [✗] Failed to create service account" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# STEP 2: GRANT PROJECT-LEVEL ROLES TO SERVICE ACCOUNT
# ============================================================================

Write-Host ""
Write-Host "Step 2: Granting project-level IAM roles..." -ForegroundColor Yellow

$projectRoles = @(
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/cloudfunctions.invoker",
    "roles/run.invoker",
    "roles/logging.logWriter",
    "roles/pubsub.publisher"
)

foreach ($role in $projectRoles) {
    Write-Host "  Granting $role..." -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
        --role=$role `
        --condition=None `
        --project=$PROJECT_ID 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [✓] $role" -ForegroundColor Green
    } else {
        Write-Host "    [⚠] Failed to grant $role (may already be granted)" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 3: GRANT USER PERMISSIONS
# ============================================================================

Write-Host ""
Write-Host "Step 3: Granting user permissions..." -ForegroundColor Yellow

# Grant Service Account User role (needed to deploy functions)
Write-Host "  Granting Service Account User role..." -ForegroundColor Gray
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL `
    --member="user:$YOUR_EMAIL" `
    --role="roles/iam.serviceAccountUser" `
    --project=$PROJECT_ID 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "    [✓] Service Account User role granted" -ForegroundColor Green
} else {
    Write-Host "    [⚠] Failed to grant Service Account User role" -ForegroundColor Yellow
}

# Grant deployment roles to user
$userRoles = @(
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/secretmanager.admin",
    "roles/bigquery.admin",
    "roles/iam.serviceAccountAdmin"
)

foreach ($role in $userRoles) {
    Write-Host "  Granting $role to user..." -ForegroundColor Gray
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="user:$YOUR_EMAIL" `
        --role=$role `
        --condition=None `
        --project=$PROJECT_ID 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [✓] $role" -ForegroundColor Green
    } else {
        Write-Host "    [⚠] Failed to grant $role (may already be granted)" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 4: ENABLE REQUIRED APIs
# ============================================================================

Write-Host ""
Write-Host "Step 4: Enabling required APIs..." -ForegroundColor Yellow

$requiredAPIs = @(
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "bigquery.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "aiplatform.googleapis.com",
    "pubsub.googleapis.com",
    "gmail.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
)

foreach ($api in $requiredAPIs) {
    Write-Host "  Enabling $api..." -ForegroundColor Gray
    gcloud services enable $api --project=$PROJECT_ID 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [✓] $api enabled" -ForegroundColor Green
    } else {
        Write-Host "    [⚠] Failed to enable $api (may already be enabled)" -ForegroundColor Yellow
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Create BigQuery dataset: .\scripts\create_bigquery_datasets.ps1" -ForegroundColor Yellow
Write-Host "  2. Create secrets in Secret Manager (see CLIENT_DEPLOYMENT_GUIDE.md)" -ForegroundColor Yellow
Write-Host "  3. Deploy Cloud Functions: .\scripts\deploy_all.ps1" -ForegroundColor Yellow
Write-Host ""
