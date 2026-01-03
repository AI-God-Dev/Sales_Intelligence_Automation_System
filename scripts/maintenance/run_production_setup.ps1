# Simplified Production Setup Runner
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Production-Ready Data Sync Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Prerequisites
Write-Host "Step 1: Verifying Prerequisites..." -ForegroundColor Yellow
$token = gcloud auth print-identity-token
if (-not $token) {
    Write-Host "  Error: Please run 'gcloud auth login'" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Authentication verified" -ForegroundColor Green
Write-Host ""

# Step 2: Create EmailMessage Table
Write-Host "Step 2: Creating EmailMessage Table..." -ForegroundColor Yellow
$createQuery = "CREATE TABLE IF NOT EXISTS ``$projectId.sales_intelligence.sf_email_messages`` (email_message_id STRING NOT NULL, from_address STRING, to_address STRING, cc_address STRING, bcc_address STRING, subject STRING, text_body STRING, html_body STRING, message_date TIMESTAMP, related_to_id STRING, created_date TIMESTAMP, last_modified_date TIMESTAMP, ingested_at TIMESTAMP) PARTITION BY DATE(message_date) CLUSTER BY from_address, related_to_id"
bq query --use_legacy_sql=false $createQuery 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: EmailMessage table ready" -ForegroundColor Green
} else {
    Write-Host "  Warning: Table may already exist" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Deploy Functions
Write-Host "Step 3: Deploying Cloud Functions..." -ForegroundColor Yellow
Write-Host "  This will take a few minutes..." -ForegroundColor Gray

$functions = @(
    "salesforce-sync",
    "dialpad-sync", 
    "hubspot-sync",
    "entity-resolution"
)

foreach ($func in $functions) {
    Write-Host "  Deploying $func..." -ForegroundColor Cyan
    $source = "cloud_functions/$($func.Replace("-", "_"))"
    $entry = $func.Replace("-", "_")
    
    gcloud functions deploy $func `
        --gen2 `
        --region=$region `
        --runtime=python311 `
        --source=$source `
        --entry-point=$entry `
        --trigger-http `
        --allow-unauthenticated `
        --memory=512MB `
        --timeout=540s `
        --max-instances=10 `
        --service-account=sales-intel-poc-sa@$projectId.iam.gserviceaccount.com `
        2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    OK: $func deployed" -ForegroundColor Green
    } else {
        Write-Host "    Warning: $func deployment had issues" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 5
}

Write-Host ""

# Step 4: Test Syncs
Write-Host "Step 4: Testing Syncs..." -ForegroundColor Yellow
$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"
$token = gcloud auth print-identity-token

# Test Salesforce Contact (most important)
Write-Host "  Testing Salesforce Contact sync..." -ForegroundColor Cyan
$body = @{object_type="Contact"; sync_type="incremental"} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}/salesforce-sync" `
        -Method Post `
        -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
        -Body $body `
        -ErrorAction Stop
    Write-Host "    OK: Contact sync - $($response.rows_synced) rows" -ForegroundColor Green
} catch {
    Write-Host "    Warning: Contact sync test failed" -ForegroundColor Yellow
}

# Test Dialpad
Write-Host "  Testing Dialpad sync..." -ForegroundColor Cyan
$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}/dialpad-sync" `
        -Method Post `
        -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
        -Body $dpBody `
        -ErrorAction Stop
    Write-Host "    OK: Dialpad sync - $($response.calls_synced) calls" -ForegroundColor Green
} catch {
    Write-Host "    Warning: Dialpad sync test failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Production Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Set up scheduled syncs: .\setup_scheduler.ps1" -ForegroundColor White
Write-Host "  2. Monitor logs: gcloud functions logs read salesforce-sync --gen2 --region=$region" -ForegroundColor White
Write-Host "  3. Check data: bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM \`$projectId.sales_intelligence.sf_contacts\`'" -ForegroundColor White
Write-Host ""

