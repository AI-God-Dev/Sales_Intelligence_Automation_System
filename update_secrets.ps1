# Update Secret Manager Secrets with Real Credentials
# Interactive script to update all secrets with real API credentials

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Secret Manager Secrets" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host ""

# Check current secret status
Write-Host "Checking current secret status..." -ForegroundColor Yellow
$secrets = @{
    "gmail-oauth-client-id" = @{
        Name = "Gmail OAuth Client ID"
        Description = "From Google Cloud Console → APIs & Services → Credentials"
        Link = "https://console.cloud.google.com/apis/credentials?project=$projectId"
        Secure = $false
    }
    "gmail-oauth-client-secret" = @{
        Name = "Gmail OAuth Client Secret"
        Description = "From Google Cloud Console (shown only once when created)"
        Link = "https://console.cloud.google.com/apis/credentials?project=$projectId"
        Secure = $true
    }
    "salesforce-client-id" = @{
        Name = "Salesforce Client ID (Consumer Key)"
        Description = "From Salesforce → Setup → App Manager → Connected Apps"
        Link = ""
        Secure = $false
    }
    "salesforce-client-secret" = @{
        Name = "Salesforce Client Secret (Consumer Secret)"
        Description = "From Salesforce Connected App"
        Link = ""
        Secure = $true
    }
    "salesforce-username" = @{
        Name = "Salesforce Username"
        Description = "Salesforce API user email address"
        Link = ""
        Secure = $false
    }
    "salesforce-password" = @{
        Name = "Salesforce Password"
        Description = "Salesforce API user password"
        Link = ""
        Secure = $true
    }
    "salesforce-security-token" = @{
        Name = "Salesforce Security Token"
        Description = "From Salesforce → Settings → Reset Security Token"
        Link = ""
        Secure = $true
    }
    "dialpad-api-key" = @{
        Name = "Dialpad API Key"
        Description = "From Dialpad Admin → Settings → Integrations → API"
        Link = ""
        Secure = $true
    }
    "hubspot-api-key" = @{
        Name = "HubSpot Private App Access Token"
        Description = "From HubSpot → Settings → Private Apps (shown only once)"
        Link = ""
        Secure = $true
    }
}

$updated = 0
$skipped = 0

foreach ($secretId in $secrets.Keys) {
    $secretInfo = $secrets[$secretId]
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "Secret: $($secretInfo.Name)" -ForegroundColor Yellow
    Write-Host "Description: $($secretInfo.Description)" -ForegroundColor Gray
    if ($secretInfo.Link) {
        Write-Host "Link: $($secretInfo.Link)" -ForegroundColor Gray
    }
    
    # Check current value
    try {
        $currentValue = gcloud secrets versions access latest --secret=$secretId --project=$projectId 2>&1 | Out-String
        $currentValue = $currentValue.Trim()
        
        if ($currentValue -and $currentValue -ne "PLACEHOLDER" -and $currentValue.Length -gt 5) {
            $preview = if ($currentValue.Length -gt 30) { $currentValue.Substring(0, 30) + "..." } else { $currentValue }
            Write-Host "Current value: $preview" -ForegroundColor Green
            $update = Read-Host "Secret already has a value. Update? (y/n)"
            if ($update -ne "y" -and $update -ne "Y") {
                Write-Host "Skipped $secretId" -ForegroundColor Yellow
                $skipped++
                continue
            }
        }
    } catch {
        Write-Host "Current value: PLACEHOLDER or empty" -ForegroundColor Yellow
    }
    
    # Get new value
    Write-Host ""
    if ($secretInfo.Secure) {
        $value = Read-Host "Enter $($secretInfo.Name)" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($value)
        $plainValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    } else {
        $plainValue = Read-Host "Enter $($secretInfo.Name)"
    }
    
    if (-not $plainValue -or $plainValue.Trim().Length -eq 0) {
        Write-Host "Empty value provided. Skipping..." -ForegroundColor Yellow
        $skipped++
        continue
    }
    
    # Update secret
    try {
        Write-Host "Updating secret..." -ForegroundColor Yellow
        $tempFile = New-TemporaryFile
        $plainValue | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
        
        gcloud secrets versions add $secretId --data-file=$tempFile --project=$projectId | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Secret updated successfully" -ForegroundColor Green
            $updated++
        } else {
            Write-Host "[X] Failed to update secret" -ForegroundColor Red
        }
        
        Remove-Item $tempFile -Force
    } catch {
        Write-Host "[X] Error updating secret: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Updated: $updated" -ForegroundColor Green
Write-Host "Skipped: $skipped" -ForegroundColor Yellow
Write-Host ""

if ($updated -gt 0) {
    Write-Host "[OK] Secrets updated successfully!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] No secrets were updated." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Verify secrets: Run 'gcloud secrets versions access latest --secret=SECRET_NAME --project=$projectId'" -ForegroundColor Gray
Write-Host "  2. Configure Gmail Domain-Wide Delegation (see docs/PHASE1_ENVIRONMENT_SETUP.md)" -ForegroundColor Gray
Write-Host "  3. Test Cloud Functions once deployment is fixed" -ForegroundColor Gray
