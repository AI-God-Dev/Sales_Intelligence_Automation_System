# Verify Account Scoring Deployment and Integration
# This script checks if account-scoring is properly deployed and accessible

$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$FUNCTION_NAME = "account-scoring"

Write-Host "Verifying Account Scoring Deployment..." -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host "Function: $FUNCTION_NAME" -ForegroundColor Gray
Write-Host ""

# 1. Check if function exists
Write-Host "1. Checking if function is deployed..." -ForegroundColor Yellow
try {
    $functionInfo = gcloud functions describe $FUNCTION_NAME `
        --gen2 `
        --region=$REGION `
        --project=$PROJECT_ID `
        --format="json" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $functionJson = $functionInfo | ConvertFrom-Json
        Write-Host "   ✅ Function is deployed" -ForegroundColor Green
        Write-Host "   Service: $($functionJson.serviceConfig.service)" -ForegroundColor Gray
        Write-Host "   URL: $($functionJson.serviceConfig.uri)" -ForegroundColor Gray
        Write-Host "   State: $($functionJson.state)" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Function is NOT deployed" -ForegroundColor Red
        Write-Host "   Run: .\scripts\deploy_phase2_functions.ps1" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ❌ Error checking function: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Check IAM permissions
Write-Host "2. Checking IAM permissions..." -ForegroundColor Yellow
try {
    $iamPolicy = gcloud functions get-iam-policy $FUNCTION_NAME `
        --gen2 `
        --region=$REGION `
        --project=$PROJECT_ID `
        --format="json" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $policy = $iamPolicy | ConvertFrom-Json
        if ($policy.bindings) {
            Write-Host "   ✅ IAM policy configured" -ForegroundColor Green
            foreach ($binding in $policy.bindings) {
                Write-Host "   Role: $($binding.role)" -ForegroundColor Gray
                Write-Host "   Members: $($binding.members -join ', ')" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️  No IAM bindings found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Could not retrieve IAM policy" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error checking IAM: $_" -ForegroundColor Yellow
}

Write-Host ""

# 3. Test function invocation
Write-Host "3. Testing function invocation..." -ForegroundColor Yellow
Write-Host "   (This may take a minute if function is cold starting...)" -ForegroundColor Gray
try {
    $testResult = gcloud functions call $FUNCTION_NAME `
        --gen2 `
        --region=$REGION `
        --project=$PROJECT_ID `
        2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Function call successful" -ForegroundColor Green
        Write-Host "   Response:" -ForegroundColor Gray
        Write-Host $testResult -ForegroundColor Gray
        
        # Try to parse JSON response
        try {
            $jsonResult = $testResult | ConvertFrom-Json
            if ($jsonResult.status -eq "success") {
                Write-Host "   ✅ Function returned success status" -ForegroundColor Green
                Write-Host "   Accounts scored: $($jsonResult.accounts_scored)" -ForegroundColor Cyan
            } elseif ($jsonResult.error) {
                Write-Host "   ⚠️  Function returned error: $($jsonResult.error)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   ⚠️  Could not parse JSON response" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ Function call failed" -ForegroundColor Red
        Write-Host "   Error: $testResult" -ForegroundColor Red
        
        if ($testResult -match "503" -or $testResult -match "Service Unavailable") {
            Write-Host "   💡 This might be a cold start. Wait 1-2 minutes and try again." -ForegroundColor Yellow
        } elseif ($testResult -match "403" -or $testResult -match "Forbidden") {
            Write-Host "   💡 Permission issue. Check IAM bindings." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Error testing function: $_" -ForegroundColor Red
}

Write-Host ""

# 4. Check BigQuery table
Write-Host "4. Checking BigQuery account_recommendations table..." -ForegroundColor Yellow
try {
    $bqQuery = @"
SELECT 
    COUNT(*) as total_scores,
    COUNT(DISTINCT account_id) as unique_accounts,
    AVG(priority_score) as avg_priority,
    MAX(score_date) as latest_score_date
FROM \`$PROJECT_ID.sales_intelligence.account_recommendations\`
WHERE score_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
"@
    
    $bqResult = echo $bqQuery | gcloud bq query --use_legacy_sql=false --format=json --project=$PROJECT_ID 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $bqData = $bqResult | ConvertFrom-Json
        if ($bqData) {
            Write-Host "   ✅ BigQuery table accessible" -ForegroundColor Green
            $row = $bqData[0]
            Write-Host "   Total scores (last 7 days): $($row.total_scores)" -ForegroundColor Gray
            Write-Host "   Unique accounts: $($row.unique_accounts)" -ForegroundColor Gray
            Write-Host "   Average priority: $([math]::Round($row.avg_priority, 2))" -ForegroundColor Gray
            Write-Host "   Latest score date: $($row.latest_score_date)" -ForegroundColor Gray
        } else {
            Write-Host "   ⚠️  No scores found in last 7 days" -ForegroundColor Yellow
            Write-Host "   💡 Run account-scoring function to generate scores" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Could not query BigQuery: $bqResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error checking BigQuery: $_" -ForegroundColor Yellow
}

Write-Host ""

# 5. Check Cloud Scheduler job
Write-Host "5. Checking Cloud Scheduler job..." -ForegroundColor Yellow
try {
    $schedulerJob = gcloud scheduler jobs describe account-scoring-daily `
        --location=$REGION `
        --project=$PROJECT_ID `
        --format="json" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $job = $schedulerJob | ConvertFrom-Json
        Write-Host "   ✅ Scheduler job exists" -ForegroundColor Green
        Write-Host "   Schedule: $($job.schedule)" -ForegroundColor Gray
        Write-Host "   State: $($job.state)" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  Scheduler job not found" -ForegroundColor Yellow
        Write-Host "   💡 Create with: gcloud scheduler jobs create http account-scoring-daily ..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Error checking scheduler: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Verification complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If function is not deployed, run: .\scripts\deploy_phase2_functions.ps1" -ForegroundColor White
Write-Host "2. If function call failed, check logs: gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50" -ForegroundColor White
Write-Host "3. Test in web app: streamlit run web_app/app.py" -ForegroundColor White

