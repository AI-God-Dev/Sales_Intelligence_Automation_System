# Setup secrets in Google Secret Manager (PowerShell)
# This script creates all required secrets and grants service account access

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$ServiceAccountName = "sales-intelligence-sa"
)

if (-not $ProjectId) {
    Write-Host "ERROR: GCP_PROJECT_ID not set. Please set it or pass as parameter." -ForegroundColor Red
    Write-Host "Usage: .\scripts\setup_secrets.ps1 -ProjectId 'YOUR_PROJECT_ID'" -ForegroundColor Yellow
    exit 1
}

$ServiceAccount = "${ServiceAccountName}@${ProjectId}.iam.gserviceaccount.com"

Write-Host "Setting up secrets in Secret Manager for project: $ProjectId" -ForegroundColor Green
Write-Host "Service Account: $ServiceAccount" -ForegroundColor Gray
Write-Host ""

# List of all required secrets
$secrets = @(
    "salesforce-client-id",
    "salesforce-client-secret",
    "salesforce-username",
    "salesforce-password",
    "salesforce-security-token",
    "salesforce-refresh-token",
    "salesforce-instance-url",
    "dialpad-api-key",
    "hubspot-api-key",
    "openai-api-key",
    "anthropic-api-key"
)

$createdCount = 0
$skippedCount = 0
$errorCount = 0

foreach ($secret in $secrets) {
    Write-Host "Processing secret: $secret" -ForegroundColor Yellow
    
    try {
        # Check if secret already exists
        $existing = gcloud secrets describe $secret --project=$ProjectId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Secret already exists. Skipping creation." -ForegroundColor Gray
            $skippedCount++
        } else {
            # Create secret with empty value (user will add value later)
            echo "" | gcloud secrets create $secret `
                --data-file=- `
                --project=$ProjectId `
                --replication-policy="automatic" 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Secret created successfully" -ForegroundColor Green
                $createdCount++
                Write-Host "    To add value: echo -n 'YOUR_VALUE' | gcloud secrets versions add $secret --data-file=- --project=$ProjectId" -ForegroundColor Cyan
            } else {
                Write-Host "  ✗ Failed to create secret" -ForegroundColor Red
                $errorCount++
                continue
            }
        }
        
        # Grant service account access to secret
        Write-Host "  Granting service account access..." -ForegroundColor Gray
        gcloud secrets add-iam-policy-binding $secret `
            --member="serviceAccount:$ServiceAccount" `
            --role="roles/secretmanager.secretAccessor" `
            --project=$ProjectId 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Access granted" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Warning: Could not grant access (may need manual setup)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "  ✗ Error processing secret: $_" -ForegroundColor Red
        $errorCount++
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Secret Setup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Created: $createdCount" -ForegroundColor Green
Write-Host "Skipped (already exists): $skippedCount" -ForegroundColor Yellow
Write-Host "Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($createdCount -gt 0) {
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Add values to each secret using:" -ForegroundColor White
    Write-Host "   echo -n 'YOUR_VALUE' | gcloud secrets versions add SECRET_NAME --data-file=- --project=$ProjectId" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Verify secrets:" -ForegroundColor White
    Write-Host "   gcloud secrets list --project=$ProjectId" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Secret setup complete!" -ForegroundColor Green

