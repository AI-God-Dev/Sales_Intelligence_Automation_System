# Test script for account-scoring Cloud Function
# Usage: .\scripts\test_account_scoring.ps1

$PROJECT_ID = "maharani-sales-hub-11-2025"
$REGION = "us-central1"
$FUNCTION_NAME = "account-scoring"
$FUNCTION_URL = "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net/account-scoring"

Write-Host "Testing account-scoring Cloud Function..." -ForegroundColor Cyan
Write-Host "URL: $FUNCTION_URL" -ForegroundColor Gray
Write-Host ""

# Get identity token
Write-Host "Getting identity token..." -ForegroundColor Yellow
$token = gcloud auth print-identity-token 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get identity token. Make sure you're logged in:" -ForegroundColor Red
    Write-Host "   gcloud auth login" -ForegroundColor Yellow
    Write-Host "   gcloud auth application-default login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Token obtained" -ForegroundColor Green
Write-Host ""

# Call the function
Write-Host "Calling function..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $FUNCTION_URL -Method POST -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ Function call successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Function call failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
    exit 1
}

