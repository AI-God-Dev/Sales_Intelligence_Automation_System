# Fix Salesforce OAuth Authentication
# This script helps update the Salesforce Consumer Secret in Secret Manager

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Salesforce OAuth Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current client_id
Write-Host "Current Client ID in Secret Manager:" -ForegroundColor Yellow
try {
    $currentClientId = (gcloud secrets versions access latest --secret=salesforce-client-id --project=$projectId).Trim()
    Write-Host "  $currentClientId" -ForegroundColor White
} catch {
    Write-Host "  ✗ Failed to retrieve client_id" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "The OAuth test shows 'invalid_client' error." -ForegroundColor Yellow
Write-Host "This means the Consumer Secret doesn't match the Consumer Key." -ForegroundColor Yellow
Write-Host ""
Write-Host "To fix this:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to Salesforce → Setup → App Manager → Connected Apps" -ForegroundColor White
Write-Host "2. Find the Connected App with Consumer Key (Client ID):" -ForegroundColor White
Write-Host "   $currentClientId" -ForegroundColor Gray
Write-Host "3. Click 'View' → 'Manage Consumer Details'" -ForegroundColor White
Write-Host "4. Click 'Reveal' next to Consumer Secret (if hidden)" -ForegroundColor White
Write-Host "5. Copy the Consumer Secret" -ForegroundColor White
Write-Host ""
Write-Host "Then paste it below to update Secret Manager:" -ForegroundColor Cyan
Write-Host ""

$newClientSecret = Read-Host "Enter Consumer Secret (or press Enter to skip)"

if ([string]::IsNullOrWhiteSpace($newClientSecret)) {
    Write-Host ""
    Write-Host "Skipped. To update manually, run:" -ForegroundColor Yellow
    Write-Host "  echo -n 'YOUR_CONSUMER_SECRET' | gcloud secrets versions add salesforce-client-secret --data-file=- --project=$projectId" -ForegroundColor Cyan
    exit 0
}

# Update the secret
Write-Host ""
Write-Host "Updating Consumer Secret in Secret Manager..." -ForegroundColor Yellow

try {
    $tempFile = New-TemporaryFile
    $newClientSecret.Trim() | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
    
    gcloud secrets versions add salesforce-client-secret --data-file=$tempFile --project=$projectId | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Consumer Secret updated successfully!" -ForegroundColor Green
        Remove-Item $tempFile -Force
        
        Write-Host ""
        Write-Host "Testing OAuth authentication..." -ForegroundColor Yellow
        
        # Test the OAuth flow
        $refreshToken = (gcloud secrets versions access latest --secret=salesforce-refresh-token --project=$projectId).Trim()
        $body = "grant_type=refresh_token&client_id=$currentClientId&client_secret=$newClientSecret.Trim()&refresh_token=$refreshToken"
        
        try {
            $response = Invoke-RestMethod -Uri "https://login.salesforce.com/services/oauth2/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✓ OAuth Authentication SUCCESSFUL!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Instance URL: $($response.instance_url)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "All credentials are now correct! The sync should work." -ForegroundColor Green
            
        } catch {
            Write-Host ""
            Write-Host "✗ OAuth test failed: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.ErrorDetails.Message) {
                Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
            }
            Write-Host ""
            Write-Host "Please verify:" -ForegroundColor Yellow
            Write-Host "  1. The Consumer Secret is correct" -ForegroundColor Yellow
            Write-Host "  2. The Consumer Key and Secret are from the same Connected App" -ForegroundColor Yellow
            Write-Host "  3. The refresh token is still valid" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "✗ Failed to update Consumer Secret" -ForegroundColor Red
        Remove-Item $tempFile -Force
        exit 1
    }
    
} catch {
    Write-Host "✗ Error updating Consumer Secret: $_" -ForegroundColor Red
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
    exit 1
}

