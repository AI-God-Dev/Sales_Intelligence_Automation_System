# Comprehensive Deployment Verification Script
# Verifies all components are properly deployed and accessible

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$datasetId = "sales_intelligence"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host ""

$allChecksPassed = $true

# 1. Verify BigQuery Dataset
Write-Host "1. Verifying BigQuery Dataset..." -ForegroundColor Yellow
$datasetExists = bq ls -d --project_id=$projectId $datasetId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Dataset '$datasetId' exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ Dataset '$datasetId' NOT FOUND" -ForegroundColor Red
    $allChecksPassed = $false
}

# Verify tables
$requiredTables = @(
    "gmail_messages", "gmail_participants", "gmail_sync_state",
    "sf_accounts", "sf_contacts", "sf_leads", "sf_opportunities", "sf_activities",
    "dialpad_calls", "account_recommendations", "hubspot_sequences",
    "etl_runs", "manual_mappings"
)
$missingTables = @()
foreach ($table in $requiredTables) {
    $tableExists = bq ls --project_id=$projectId "$datasetId.$table" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingTables += $table
    }
}
if ($missingTables.Count -eq 0) {
    Write-Host "   ✓ All required tables exist" -ForegroundColor Green
} else {
    Write-Host "   ✗ Missing tables: $($missingTables -join ', ')" -ForegroundColor Red
    $allChecksPassed = $false
}
Write-Host ""

# 2. Verify Cloud Functions
Write-Host "2. Verifying Cloud Functions..." -ForegroundColor Yellow
$requiredFunctions = @("gmail-sync", "salesforce-sync", "dialpad-sync", "hubspot-sync", "entity-resolution")
$missingFunctions = @()
foreach ($func in $requiredFunctions) {
    $funcExists = gcloud functions describe $func --region=$region --project=$projectId --gen2 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Function '$func' exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Function '$func' NOT FOUND" -ForegroundColor Red
        $missingFunctions += $func
        $allChecksPassed = $false
    }
}
Write-Host ""

# 3. Verify Cloud Scheduler Jobs
Write-Host "3. Verifying Cloud Scheduler Jobs..." -ForegroundColor Yellow
$requiredJobs = @(
    "gmail-full-sync", "gmail-incremental-sync",
    "salesforce-full-sync", "salesforce-incremental-sync",
    "dialpad-sync", "hubspot-sync", "entity-resolution"
)
$missingJobs = @()
foreach ($job in $requiredJobs) {
    $jobExists = gcloud scheduler jobs describe $job --location=$region --project=$projectId 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Job '$job' exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Job '$job' NOT FOUND" -ForegroundColor Red
        $missingJobs += $job
        $allChecksPassed = $false
    }
}
Write-Host ""

# 4. Verify Pub/Sub Topic
Write-Host "4. Verifying Pub/Sub Topic..." -ForegroundColor Yellow
$topicExists = gcloud pubsub topics describe ingestion-errors --project=$projectId 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Topic 'ingestion-errors' exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ Topic 'ingestion-errors' NOT FOUND" -ForegroundColor Red
    $allChecksPassed = $false
}
Write-Host ""

# 5. Verify Secrets
Write-Host "5. Verifying Secret Manager Secrets..." -ForegroundColor Yellow
$requiredSecrets = @(
    "salesforce-client-id", "salesforce-client-secret", "salesforce-username",
    "salesforce-password", "salesforce-security-token", "salesforce-refresh-token",
    "dialpad-api-key", "hubspot-api-key",
    "gmail-oauth-client-id", "gmail-oauth-client-secret"
)
$missingSecrets = @()
foreach ($secret in $requiredSecrets) {
    $secretExists = gcloud secrets describe $secret --project=$projectId 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Secret '$secret' exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Secret '$secret' NOT FOUND" -ForegroundColor Red
        $missingSecrets += $secret
        $allChecksPassed = $false
    }
}
Write-Host ""

# 6. Check BigQuery Row Counts
Write-Host "6. Checking BigQuery Table Row Counts..." -ForegroundColor Yellow
foreach ($table in $requiredTables) {
    $rowCount = bq query --use_legacy_sql=false --format=csv --project_id=$projectId "SELECT COUNT(*) as cnt FROM \`$projectId.$datasetId.$table\`" 2>$null | Select-Object -Skip 1
    if ($LASTEXITCODE -eq 0 -and $rowCount) {
        Write-Host "   $table : $rowCount rows" -ForegroundColor Gray
    }
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allChecksPassed) {
    Write-Host "✓ All verification checks passed!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some verification checks failed:" -ForegroundColor Yellow
    if ($missingTables.Count -gt 0) {
        Write-Host "  - Missing tables: $($missingTables -join ', ')" -ForegroundColor Red
    }
    if ($missingFunctions.Count -gt 0) {
        Write-Host "  - Missing functions: $($missingFunctions -join ', ')" -ForegroundColor Red
    }
    if ($missingJobs.Count -gt 0) {
        Write-Host "  - Missing scheduler jobs: $($missingJobs -join ', ')" -ForegroundColor Red
    }
    if ($missingSecrets.Count -gt 0) {
        Write-Host "  - Missing secrets: $($missingSecrets -join ', ')" -ForegroundColor Red
    }
}
Write-Host "========================================" -ForegroundColor Cyan

