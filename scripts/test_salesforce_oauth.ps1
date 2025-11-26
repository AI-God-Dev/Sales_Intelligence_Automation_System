# Test Salesforce OAuth Authentication
# This script tests the OAuth flow with credentials from Secret Manager

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Salesforce OAuth Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get credentials from Secret Manager
Write-Host "Reading credentials from Secret Manager..." -ForegroundColor Yellow

try {
    $clientIdOutput = gcloud secrets versions access latest --secret=salesforce-client-id --project=$projectId 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed with exit code $LASTEXITCODE"
    }
    $clientId = ($clientIdOutput | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($clientId)) {
        throw "Client ID is empty"
    }
    Write-Host "✓ Client ID retrieved" -ForegroundColor Green
    Write-Host "  Client ID: $($clientId.Substring(0, [Math]::Min(50, $clientId.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to retrieve client_id: $_" -ForegroundColor Red
    exit 1
}

try {
    $clientSecretOutput = gcloud secrets versions access latest --secret=salesforce-client-secret --project=$projectId 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed with exit code $LASTEXITCODE"
    }
    $clientSecret = ($clientSecretOutput | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($clientSecret)) {
        throw "Client Secret is empty"
    }
    Write-Host "✓ Client Secret retrieved" -ForegroundColor Green
    Write-Host "  Client Secret: $($clientSecret.Substring(0, [Math]::Min(20, $clientSecret.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to retrieve client_secret: $_" -ForegroundColor Red
    exit 1
}

try {
    $refreshTokenOutput = gcloud secrets versions access latest --secret=salesforce-refresh-token --project=$projectId 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed with exit code $LASTEXITCODE"
    }
    $refreshToken = ($refreshTokenOutput | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($refreshToken)) {
        throw "Refresh Token is empty"
    }
    Write-Host "✓ Refresh Token retrieved" -ForegroundColor Green
    Write-Host "  Refresh Token: $($refreshToken.Substring(0, [Math]::Min(30, $refreshToken.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to retrieve refresh_token: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Testing OAuth token exchange..." -ForegroundColor Yellow

# Test OAuth token exchange
$tokenUrl = "https://login.salesforce.com/services/oauth2/token"
$body = @{
    grant_type = "refresh_token"
    client_id = $clientId
    client_secret = $clientSecret
    refresh_token = $refreshToken
}

try {
    $response = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ OAuth Authentication SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access Token: $($response.access_token.Substring(0, [Math]::Min(50, $response.access_token.Length)))..." -ForegroundColor Gray
    Write-Host "Instance URL: $($response.instance_url)" -ForegroundColor Gray
    Write-Host "Token Type: $($response.token_type)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "All credentials are correct! The sync should work now." -ForegroundColor Green
    
} catch {
    $errorResponse = $_.ErrorDetails.Message
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ OAuth Authentication FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $errorResponse" -ForegroundColor Red
    Write-Host ""
    
    if ($errorResponse -match '"error":"invalid_client"') {
        Write-Host "DIAGNOSIS: Invalid Client Credentials" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "The client_id or client_secret in Secret Manager does not match." -ForegroundColor Yellow
        Write-Host "This usually means:" -ForegroundColor Yellow
        Write-Host "  1. The client_secret is incorrect" -ForegroundColor Yellow
        Write-Host "  2. The client_secret has extra whitespace or newlines" -ForegroundColor Yellow
        Write-Host "  3. The client_id and client_secret are from different Connected Apps" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "SOLUTION:" -ForegroundColor Cyan
        Write-Host "  1. Go to Salesforce → Setup → App Manager → Connected Apps" -ForegroundColor White
        Write-Host "  2. Find the Connected App with Consumer Key: $($clientId.Substring(0, [Math]::Min(50, $clientId.Length)))..." -ForegroundColor White
        Write-Host "  3. Click 'View' → 'Manage Consumer Details'" -ForegroundColor White
        Write-Host "  4. Copy the Consumer Secret (it may be hidden - click 'Reveal')" -ForegroundColor White
        Write-Host "  5. Update it in Secret Manager using:" -ForegroundColor White
        Write-Host ""
        Write-Host "     echo -n 'YOUR_CONSUMER_SECRET' | gcloud secrets versions add salesforce-client-secret --data-file=- --project=$projectId" -ForegroundColor Cyan
        Write-Host ""
    } elseif ($errorResponse -match '"error":"invalid_grant"') {
        Write-Host "DIAGNOSIS: Invalid Refresh Token" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "The refresh_token is invalid or expired." -ForegroundColor Yellow
        Write-Host "You need to generate a new refresh token using the OAuth flow." -ForegroundColor Yellow
    } else {
        Write-Host "DIAGNOSIS: Unknown OAuth Error" -ForegroundColor Yellow
        Write-Host "Check the error message above for details." -ForegroundColor Yellow
    }
    
    exit 1
}

