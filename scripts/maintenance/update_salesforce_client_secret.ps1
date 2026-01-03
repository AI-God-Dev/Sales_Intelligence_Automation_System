# Quick script to update Salesforce Consumer Secret
# Run this after getting the Consumer Secret from Salesforce

param(
    [Parameter(Mandatory=$true)]
    [string]$ConsumerSecret
)

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "Updating Salesforce Consumer Secret..." -ForegroundColor Yellow

# Remove any whitespace
$ConsumerSecret = $ConsumerSecret.Trim()

if ([string]::IsNullOrWhiteSpace($ConsumerSecret)) {
    Write-Host "Error: Consumer Secret cannot be empty" -ForegroundColor Red
    exit 1
}

# Update the secret
$tempFile = New-TemporaryFile
try {
    $ConsumerSecret | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
    
    gcloud secrets versions add salesforce-client-secret --data-file=$tempFile --project=$projectId | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Consumer Secret updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to update Consumer Secret" -ForegroundColor Red
        exit 1
    }
} finally {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}

# Test OAuth
Write-Host ""
Write-Host "Testing OAuth authentication..." -ForegroundColor Yellow

$clientId = (gcloud secrets versions access latest --secret=salesforce-client-id --project=$projectId).Trim()
$refreshToken = (gcloud secrets versions access latest --secret=salesforce-refresh-token --project=$projectId).Trim()

$body = "grant_type=refresh_token&client_id=$clientId&client_secret=$ConsumerSecret&refresh_token=$refreshToken"

try {
    $response = Invoke-RestMethod -Uri "https://login.salesforce.com/services/oauth2/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ OAuth Authentication SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Instance URL: $($response.instance_url)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "All credentials are correct! Testing sync..." -ForegroundColor Green
    
    # Test the sync
    Start-Sleep -Seconds 2
    $token = gcloud auth print-identity-token
    $syncResponse = Invoke-RestMethod -Uri "https://salesforce-sync-z455yfejea-uc.a.run.app" -Method Post -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} -Body '{"object_type":"Account","sync_type":"full"}' -ErrorAction Stop
    
    Write-Host ""
    Write-Host "✓ Salesforce sync test completed!" -ForegroundColor Green
    Write-Host "  Status: $($syncResponse.status)" -ForegroundColor Gray
    if ($syncResponse.rows_synced) {
        Write-Host "  Rows synced: $($syncResponse.rows_synced)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ OAuth test failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please verify the Consumer Secret is correct." -ForegroundColor Yellow
    exit 1
}

