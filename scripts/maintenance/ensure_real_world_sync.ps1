# Comprehensive Script to Ensure Real-World Data Sync
# Tests and validates Salesforce, Dialpad, and HubSpot syncs

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$dataset = "sales_intelligence"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Real-World Data Sync Validation" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Gray
Write-Host "Region: $region" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Prerequisites
Write-Host "📋 Step 1: Checking Prerequisites..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check gcloud auth
try {
    $token = gcloud auth print-identity-token 2>$null
    if (-not $token) {
        throw "No token"
    }
    Write-Host "  ✅ gcloud authentication: OK" -ForegroundColor Green
} catch {
    Write-Host "  ❌ gcloud authentication: FAILED" -ForegroundColor Red
    Write-Host "     Run: gcloud auth login" -ForegroundColor Yellow
    exit 1
}

# Check BigQuery access
try {
    $bqTest = bq query --use_legacy_sql=false --format=prettyjson "SELECT 1 as test" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ BigQuery access: OK" -ForegroundColor Green
    } else {
        throw "BigQuery access failed"
    }
} catch {
    Write-Host "  ⚠️  BigQuery access: May need setup" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Trigger All Syncs
Write-Host "🔄 Step 2: Triggering All Syncs..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"
$syncResults = @{}

function Invoke-Sync {
    param(
        [string]$FunctionName,
        [string]$Body,
        [string]$Description
    )
    
    Write-Host "  🔄 $Description..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
            -Method Post `
            -Headers @{
                Authorization = "Bearer $token"
                "Content-Type" = "application/json"
            } `
            -Body $Body `
            -ErrorAction Stop
        
        Write-Host "    ✅ Success" -ForegroundColor Green
        $script:syncResults[$FunctionName] = @{
            Status = "Success"
            Response = $response
        }
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = $_.ErrorDetails.Message
        Write-Host "    ❌ Failed (HTTP $statusCode)" -ForegroundColor Red
        Write-Host "       Error: $errorMsg" -ForegroundColor Red
        $script:syncResults[$FunctionName] = @{
            Status = "Failed"
            Error = $errorMsg
            StatusCode = $statusCode
        }
        return $false
    }
}

# Salesforce Syncs
Write-Host ""
Write-Host "  📊 Salesforce Syncs:" -ForegroundColor Yellow

$sfObjects = @(
    @{Type="Account"; SyncType="incremental"},
    @{Type="Contact"; SyncType="incremental"},
    @{Type="Lead"; SyncType="incremental"},
    @{Type="Opportunity"; SyncType="incremental"},
    @{Type="Task"; SyncType="incremental"},
    @{Type="Event"; SyncType="incremental"},
    @{Type="EmailMessage"; SyncType="incremental"}
)

foreach ($obj in $sfObjects) {
    $body = @{
        object_type = $obj.Type
        sync_type = $obj.SyncType
    } | ConvertTo-Json -Compress
    
    Invoke-Sync "salesforce-sync" $body "Salesforce $($obj.Type)"
    Start-Sleep -Seconds 2
}

# Dialpad Sync
Write-Host ""
Write-Host "  📞 Dialpad Sync:" -ForegroundColor Yellow
$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
Invoke-Sync "dialpad-sync" $dpBody "Dialpad Calls"
Start-Sleep -Seconds 2

# HubSpot Sync
Write-Host ""
Write-Host "  📧 HubSpot Sync:" -ForegroundColor Yellow
$hsBody = @{} | ConvertTo-Json -Compress
Invoke-Sync "hubspot-sync" $hsBody "HubSpot Sequences"
Start-Sleep -Seconds 2

# Entity Resolution
Write-Host ""
Write-Host "  🔗 Entity Resolution:" -ForegroundColor Yellow
$erBody = @{
    entity_type = "all"
    batch_size = 1000
} | ConvertTo-Json -Compress
Invoke-Sync "entity-resolution" $erBody "Entity Resolution"

Write-Host ""
Write-Host "⏳ Waiting 30 seconds for syncs to process..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 3: Verify Data in BigQuery
Write-Host ""
Write-Host "📊 Step 3: Verifying Data in BigQuery..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

function Check-TableData {
    param(
        [string]$TableName,
        [string]$Description
    )
    
    Write-Host "  📋 Checking $Description..." -ForegroundColor Cyan
    
    $query = "SELECT COUNT(*) as total FROM ``$projectId.$dataset.$TableName``"
    
    try {
        $result = bq query --use_legacy_sql=false --format=prettyjson $query 2>&1
        if ($LASTEXITCODE -eq 0) {
            $json = $result | ConvertFrom-Json
            $count = $json[0].total
            if ($count -gt 0) {
                Write-Host "    ✅ Found $count records" -ForegroundColor Green
                return $count
            } else {
                Write-Host "    ⚠️  Table exists but empty" -ForegroundColor Yellow
                return 0
            }
        } else {
            Write-Host "    ❌ Query failed: $result" -ForegroundColor Red
            return -1
        }
    } catch {
        Write-Host "    ❌ Error: $_" -ForegroundColor Red
        return -1
    }
}

$dataResults = @{}

# Check Salesforce tables
Write-Host ""
Write-Host "  📊 Salesforce Tables:" -ForegroundColor Yellow
$dataResults["sf_accounts"] = Check-TableData "sf_accounts" "Salesforce Accounts"
$dataResults["sf_contacts"] = Check-TableData "sf_contacts" "Salesforce Contacts"
$dataResults["sf_leads"] = Check-TableData "sf_leads" "Salesforce Leads"
$dataResults["sf_opportunities"] = Check-TableData "sf_opportunities" "Salesforce Opportunities"
$dataResults["sf_activities"] = Check-TableData "sf_activities" "Salesforce Activities"
$dataResults["sf_email_messages"] = Check-TableData "sf_email_messages" "Salesforce EmailMessages"

# Check Dialpad table
Write-Host ""
Write-Host "  📞 Dialpad Tables:" -ForegroundColor Yellow
$dataResults["dialpad_calls"] = Check-TableData "dialpad_calls" "Dialpad Calls"

# Check HubSpot table
Write-Host ""
Write-Host "  📧 HubSpot Tables:" -ForegroundColor Yellow
$dataResults["hubspot_sequences"] = Check-TableData "hubspot_sequences" "HubSpot Sequences"

# Check ETL Runs
Write-Host ""
Write-Host "  📈 ETL Runs:" -ForegroundColor Yellow
$etlQuery = "SELECT source_system, job_type, status, rows_processed, rows_failed, started_at FROM ``$projectId.$dataset.etl_runs`` ORDER BY started_at DESC LIMIT 10"

try {
    $etlResult = bq query --use_legacy_sql=false --format=prettyjson $etlQuery 2>&1
    if ($LASTEXITCODE -eq 0) {
        $etlJson = $etlResult | ConvertFrom-Json
        if ($etlJson.Count -gt 0) {
            Write-Host "    ✅ Found $($etlJson.Count) recent ETL runs" -ForegroundColor Green
            foreach ($run in $etlJson) {
                $statusColor = if ($run.status -eq "success") { "Green" } elseif ($run.status -eq "partial") { "Yellow" } else { "Red" }
                Write-Host "      - $($run.source_system) ($($run.job_type)): $($run.status) - $($run.rows_processed) rows" -ForegroundColor $statusColor
            }
        } else {
            Write-Host "    ⚠️  No recent ETL runs found" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "    ⚠️  Could not check ETL runs: $_" -ForegroundColor Yellow
}

# Step 4: Check Entity Resolution
Write-Host ""
Write-Host "🔗 Step 4: Checking Entity Resolution..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$erQuery = "SELECT COUNT(*) as total_participants, COUNT(DISTINCT sf_contact_id) as matched_contacts, COUNT(CASE WHEN sf_contact_id IS NOT NULL THEN 1 END) as matched_count FROM ``$projectId.$dataset.gmail_participants``"

try {
    $erResult = bq query --use_legacy_sql=false --format=prettyjson $erQuery 2>&1
    if ($LASTEXITCODE -eq 0) {
        $erJson = $erResult | ConvertFrom-Json
        $erData = $erJson[0]
        Write-Host "  ✅ Email Participants:" -ForegroundColor Green
        Write-Host "     Total: $($erData.total_participants)" -ForegroundColor White
        Write-Host "     Matched: $($erData.matched_count)" -ForegroundColor White
        $matchRate = if ($erData.total_participants -gt 0) { [math]::Round(($erData.matched_count / $erData.total_participants) * 100, 2) } else { 0 }
        Write-Host "     Match Rate: $matchRate%" -ForegroundColor $(if ($matchRate -gt 50) { "Green" } else { "Yellow" })
    }
} catch {
    Write-Host "  ⚠️  Could not check entity resolution: $_" -ForegroundColor Yellow
}

$callMatchQuery = "SELECT COUNT(*) as total_calls, COUNT(DISTINCT matched_contact_id) as matched_contacts, COUNT(CASE WHEN matched_contact_id IS NOT NULL THEN 1 END) as matched_count FROM ``$projectId.$dataset.dialpad_calls``"

try {
    $callMatchResult = bq query --use_legacy_sql=false --format=prettyjson $callMatchQuery 2>&1
    if ($LASTEXITCODE -eq 0) {
        $callMatchJson = $callMatchResult | ConvertFrom-Json
        $callMatchData = $callMatchJson[0]
        Write-Host "  ✅ Dialpad Calls:" -ForegroundColor Green
        Write-Host "     Total: $($callMatchData.total_calls)" -ForegroundColor White
        Write-Host "     Matched: $($callMatchData.matched_count)" -ForegroundColor White
        $callMatchRate = if ($callMatchData.total_calls -gt 0) { [math]::Round(($callMatchData.matched_count / $callMatchData.total_calls) * 100, 2) } else { 0 }
        Write-Host "     Match Rate: $callMatchRate%" -ForegroundColor $(if ($callMatchRate -gt 50) { "Green" } else { "Yellow" })
    }
} catch {
    Write-Host "  ⚠️  Could not check call matches: $_" -ForegroundColor Yellow
}

# Step 5: Summary Report
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 Summary Report" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Sync Status:" -ForegroundColor Yellow
foreach ($key in $syncResults.Keys) {
    $result = $syncResults[$key]
    $statusColor = if ($result.Status -eq "Success") { "Green" } else { "Red" }
    Write-Host "  $key : $($result.Status)" -ForegroundColor $statusColor
}

Write-Host ""
Write-Host "Data Status:" -ForegroundColor Yellow
foreach ($key in $dataResults.Keys) {
    $count = $dataResults[$key]
    if ($count -gt 0) {
        Write-Host "  $key : ✅ $count records" -ForegroundColor Green
    } elseif ($count -eq 0) {
        Write-Host "  $key : ⚠️  Empty" -ForegroundColor Yellow
    } else {
        Write-Host "  $key : ❌ Error" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Validation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review any failed syncs above" -ForegroundColor White
Write-Host "  2. Check Cloud Function logs for errors" -ForegroundColor White
Write-Host "  3. Verify secrets in Secret Manager" -ForegroundColor White
Write-Host "  4. Run incremental syncs regularly" -ForegroundColor White
Write-Host ""

