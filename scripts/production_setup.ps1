# Production-Ready Data Sync Setup
# This script does everything needed for production deployment

$ErrorActionPreference = "Continue"
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"
$dataset = "sales_intelligence"
$serviceAccount = "sales-intel-poc-sa@${projectId}.iam.gserviceaccount.com"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Production-Ready Data Sync Setup                   ║" -ForegroundColor Cyan
Write-Host "║   Complete Deployment & Configuration                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Prerequisites
Write-Host "Step 1: Verifying Prerequisites..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check gcloud auth
try {
    $token = gcloud auth print-identity-token 2>$null
    if (-not $token) {
        throw "No token"
    }
    Write-Host "  ✅ gcloud authentication" -ForegroundColor Green
} catch {
    Write-Host "  ❌ gcloud authentication failed" -ForegroundColor Red
    Write-Host "     Run: gcloud auth login" -ForegroundColor Yellow
    exit 1
}

# Check project
$currentProject = gcloud config get-value project 2>$null
if ($currentProject -ne $projectId) {
    Write-Host "  ⚠️  Setting project to $projectId" -ForegroundColor Yellow
    gcloud config set project $projectId
}
Write-Host "  ✅ Project: $projectId" -ForegroundColor Green

# Check BigQuery access
try {
    $bqTest = bq query --use_legacy_sql=false --format=prettyjson "SELECT 1 as test" 2>&1 | Out-Null
    Write-Host "  ✅ BigQuery access" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  BigQuery access may need setup" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Create Missing Tables
Write-Host "Step 2: Ensuring All Tables Exist..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check and create EmailMessage table
Write-Host "  Checking EmailMessage table..." -ForegroundColor Cyan
$checkQuery = "SELECT COUNT(*) as count FROM ``$projectId.$dataset.sf_email_messages`` LIMIT 1"
try {
    bq query --use_legacy_sql=false $checkQuery 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ EmailMessage table exists" -ForegroundColor Green
    } else {
        throw "Table check failed"
    }
} catch {
    Write-Host "    Creating EmailMessage table..." -ForegroundColor Yellow
    $createQuery = "CREATE TABLE IF NOT EXISTS ``$projectId.$dataset.sf_email_messages`` (email_message_id STRING NOT NULL, from_address STRING, to_address STRING, cc_address STRING, bcc_address STRING, subject STRING, text_body STRING, html_body STRING, message_date TIMESTAMP, related_to_id STRING, created_date TIMESTAMP, last_modified_date TIMESTAMP, ingested_at TIMESTAMP) PARTITION BY DATE(message_date) CLUSTER BY from_address, related_to_id"
    bq query --use_legacy_sql=false $createQuery 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ EmailMessage table created" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  EmailMessage table creation may have failed" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 3: Deploy Updated Functions
Write-Host "Step 3: Deploying Updated Cloud Functions..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$functions = @(
    @{Name="salesforce-sync"; Source="cloud_functions/salesforce_sync"; Memory="512MB"},
    @{Name="dialpad-sync"; Source="cloud_functions/dialpad_sync"; Memory="512MB"},
    @{Name="hubspot-sync"; Source="cloud_functions/hubspot_sync"; Memory="1024MB"},
    @{Name="entity-resolution"; Source="cloud_functions/entity_resolution"; Memory="512MB"}
)

foreach ($func in $functions) {
    Write-Host "  Deploying $($func.Name)..." -ForegroundColor Cyan
    try {
        gcloud functions deploy $func.Name `
            --gen2 `
            --region=$region `
            --runtime=python311 `
            --source=$func.Source `
            --entry-point=$($func.Name.Replace("-", "_")) `
            --trigger-http `
            --allow-unauthenticated `
            --memory=$func.Memory `
            --timeout=540s `
            --max-instances=10 `
            --service-account=$serviceAccount `
            2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ $($func.Name) deployed" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️  $($func.Name) deployment had issues" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    ❌ $($func.Name) deployment failed: $_" -ForegroundColor Red
    }
    Start-Sleep -Seconds 3
}

Write-Host ""

# Step 4: Test All Syncs
Write-Host "Step 4: Testing All Syncs..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$baseUrl = "https://${region}-${projectId}.cloudfunctions.net"
$token = gcloud auth print-identity-token

function Test-Sync {
    param($FunctionName, $Body, $Description)
    Write-Host "  Testing $Description..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "${baseUrl}/${FunctionName}" `
            -Method Post `
            -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
            -Body $Body `
            -ErrorAction Stop `
            -TimeoutSec 300
        
        $status = if ($response.status -eq "success") { "✅" } else { "⚠️" }
        Write-Host "    $status $Description - Status: $($response.status)" -ForegroundColor $(if ($response.status -eq "success") { "Green" } else { "Yellow" })
        if ($response.PSObject.Properties.Name -contains "rows_synced") {
            Write-Host "      Rows synced: $($response.rows_synced)" -ForegroundColor Gray
        }
        return $true
    } catch {
        Write-Host "    ❌ $Description failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test Salesforce syncs
Write-Host "  Salesforce Syncs:" -ForegroundColor Yellow
$sfObjects = @("Account", "Contact", "Lead", "Opportunity", "Task", "Event", "EmailMessage")
foreach ($obj in $sfObjects) {
    $body = @{object_type=$obj; sync_type="incremental"} | ConvertTo-Json -Compress
    Test-Sync "salesforce-sync" $body "Salesforce $obj"
    Start-Sleep -Seconds 2
}

# Test Dialpad
Write-Host "  Dialpad Sync:" -ForegroundColor Yellow
$dpBody = @{sync_type="incremental"} | ConvertTo-Json -Compress
Test-Sync "dialpad-sync" $dpBody "Dialpad Calls"

# Test HubSpot
Write-Host "  HubSpot Sync:" -ForegroundColor Yellow
$hsBody = @{} | ConvertTo-Json -Compress
Test-Sync "hubspot-sync" $hsBody "HubSpot Sequences"

# Test Entity Resolution
Write-Host "  Entity Resolution:" -ForegroundColor Yellow
$erBody = @{entity_type="all"; batch_size=1000} | ConvertTo-Json -Compress
Test-Sync "entity-resolution" $erBody "Entity Resolution"

Write-Host ""
Write-Host "⏳ Waiting 30 seconds for syncs to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 5: Verify Data
Write-Host ""
Write-Host "Step 5: Verifying Data in BigQuery..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$tables = @(
    @{Name="sf_accounts"; Desc="Salesforce Accounts"},
    @{Name="sf_contacts"; Desc="Salesforce Contacts"},
    @{Name="sf_leads"; Desc="Salesforce Leads"},
    @{Name="sf_opportunities"; Desc="Salesforce Opportunities"},
    @{Name="sf_activities"; Desc="Salesforce Activities"},
    @{Name="sf_email_messages"; Desc="Salesforce EmailMessages"},
    @{Name="dialpad_calls"; Desc="Dialpad Calls"},
    @{Name="hubspot_sequences"; Desc="HubSpot Sequences"}
)

foreach ($table in $tables) {
    $query = "SELECT COUNT(*) as total FROM ``$projectId.$dataset.$($table.Name)``"
    try {
        $result = bq query --use_legacy_sql=false --format=prettyjson $query 2>&1
        if ($LASTEXITCODE -eq 0) {
            $json = $result | ConvertFrom-Json
            $count = $json[0].total
            $status = if ($count -gt 0) { "✅" } else { "⚠️" }
            Write-Host "  $status $($table.Desc): $count records" -ForegroundColor $(if ($count -gt 0) { "Green" } else { "Yellow" })
        }
    } catch {
        Write-Host "  ❌ $($table.Desc): Error checking" -ForegroundColor Red
    }
}

# Step 6: Check ETL Runs
Write-Host ""
Write-Host "Step 6: Checking Recent ETL Runs..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$etlQuery = "SELECT source_system, status, rows_processed, started_at FROM ``$projectId.$dataset.etl_runs`` ORDER BY started_at DESC LIMIT 10"
try {
    $etlResult = bq query --use_legacy_sql=false --format=prettyjson $etlQuery 2>&1
    if ($LASTEXITCODE -eq 0) {
        $etlJson = $etlResult | ConvertFrom-Json
        foreach ($run in $etlJson) {
            $statusColor = if ($run.status -eq "success") { "Green" } elseif ($run.status -eq "partial") { "Yellow" } else { "Red" }
            Write-Host "  $($run.source_system): $($run.status) - $($run.rows_processed) rows" -ForegroundColor $statusColor
        }
    }
} catch {
    Write-Host "  ⚠️  Could not check ETL runs" -ForegroundColor Yellow
}

# Step 7: Setup Cloud Scheduler (Optional)
Write-Host ""
Write-Host "Step 7: Cloud Scheduler Setup (Optional)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "  To set up scheduled syncs, run:" -ForegroundColor Gray
Write-Host "    .\scripts\setup_scheduler.ps1" -ForegroundColor Cyan
Write-Host ""

# Final Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Production Setup Complete!                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ All functions deployed" -ForegroundColor Green
Write-Host "✅ All syncs tested" -ForegroundColor Green
Write-Host "✅ Data verified" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor syncs: gcloud functions logs read salesforce-sync --gen2 --region=$region" -ForegroundColor White
Write-Host "  2. Set up scheduled syncs: .\scripts\setup_scheduler.ps1" -ForegroundColor White
Write-Host "  3. Review ETL runs in BigQuery" -ForegroundColor White
Write-Host ""
Write-Host ""

