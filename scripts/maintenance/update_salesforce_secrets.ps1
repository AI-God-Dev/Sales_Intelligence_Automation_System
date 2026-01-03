# Update Salesforce secrets in Secret Manager
# PowerShell version - Interactive script to update credentials

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Update Salesforce Secrets in Secret Manager" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will update Salesforce credentials." -ForegroundColor Yellow
Write-Host "You need:" -ForegroundColor Yellow
Write-Host "  1. Salesforce username" -ForegroundColor Gray
Write-Host "  2. Salesforce password" -ForegroundColor Gray
Write-Host "  3. Salesforce security token (get from email if reset)" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Continue? (y/n)"
if ($continue -ne "y" -and $continue -ne "Y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# Check if secrets exist
Write-Host ""
Write-Host "Checking existing secrets..." -ForegroundColor Cyan
$secrets = @("salesforce-username", "salesforce-password", "salesforce-security-token")
foreach ($secret in $secrets) {
    $exists = gcloud secrets describe $secret --project=$PROJECT_ID 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Secret exists: $secret" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Secret missing: $secret (will create)" -ForegroundColor Yellow
        gcloud secrets create $secret --project=$PROJECT_ID 2>$null
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Enter Salesforce Credentials" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Get username
$sfUsername = Read-Host "Salesforce Username (email)"
echo -n $sfUsername | gcloud secrets versions add salesforce-username `
  --data-file=- --project=$PROJECT_ID

# Get password (secure input)
$sfPassword = Read-Host "Salesforce Password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($sfPassword)
$sfPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
echo -n $sfPasswordPlain | gcloud secrets versions add salesforce-password `
  --data-file=- --project=$PROJECT_ID
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

# Get security token
$sfToken = Read-Host "Salesforce Security Token (or press Enter to skip if not reset)"
if (![string]::IsNullOrEmpty($sfToken)) {
    echo -n $sfToken | gcloud secrets versions add salesforce-security-token `
      --data-file=- --project=$PROJECT_ID
    Write-Host "✅ Security token updated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Security token not updated (using existing)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Secrets updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify credentials are correct"
Write-Host "  2. Retry Salesforce sync"
Write-Host "  3. Check logs if still failing"
Write-Host "==========================================" -ForegroundColor Cyan

