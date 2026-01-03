# Test Real-World Data Sync for Salesforce and Dialpad
# This script tests all sync functions with real-world data

$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing Real-World Data Sync" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Cyan
Write-Host "Region: $region" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get identity token
Write-Host "Getting identity token..." -ForegroundColor Yellow
$token = gcloud auth print-identity-token
if (-not $token) {
    Write-Host "Error: Failed to get identity token. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Token obtained" -ForegroundColor Green
Write-Host ""

$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"

# Function to trigger a sync and check response
function Test-Sync {
    param(
        [string]$FunctionName,
        [string]$Data,
        [string]$Description
    )
    
    Write-Host "🔄 Testing $Description..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
            -Method Post `
            -Headers @{
                Authorization = "Bearer $token"
                "Content-Type" = "application/json"
            } `
            -Body $Data `
            -ErrorAction Stop
        
        Write-Host "  ✅ Success: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorBody = $_.ErrorDetails.Message
        Write-Host "  ❌ Failed (HTTP $statusCode): $errorBody" -ForegroundColor Red
        return $false
    }
    Write-Host ""
}

# Test Salesforce Sync - All Objects
Write-Host "📊 Testing Salesforce Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

$sfObjects = @("Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage")
foreach ($obj in $sfObjects) {
    $body = @{
        object_type = $obj
        sync_type = "incremental"
    } | ConvertTo-Json -Compress
    
    Test-Sync "salesforce-sync" $body "Salesforce $obj sync"
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "📞 Testing Dialpad Sync" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

# Test Dialpad Sync
$dpBody = @{
    sync_type = "incremental"
} | ConvertTo-Json -Compress

Test-Sync "dialpad-sync" $dpBody "Dialpad call logs sync"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "🔗 Testing Entity Resolution" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

# Test Entity Resolution
$erBody = @{
    entity_type = "all"
    batch_size = 1000
} | ConvertTo-Json -Compress

Test-Sync "entity-resolution" $erBody "Entity resolution (email & phone matching)"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check BigQuery tables for synced data" -ForegroundColor White
Write-Host "2. Review ETL runs table for sync statistics" -ForegroundColor White
Write-Host "3. Verify entity resolution matches" -ForegroundColor White
Write-Host ""
Write-Host "Query examples:" -ForegroundColor Yellow
Write-Host "  bq query --use_legacy_sql=false `"SELECT COUNT(*) FROM \`$projectId.sales_intelligence.sf_email_messages\`"`" -ForegroundColor Gray
Write-Host "  bq query --use_legacy_sql=false `"SELECT COUNT(*) FROM \`$projectId.sales_intelligence.dialpad_calls WHERE transcript_text IS NOT NULL\`"`" -ForegroundColor Gray

