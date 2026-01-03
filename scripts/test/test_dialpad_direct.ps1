# Test Dialpad API Directly
# This script tests the Dialpad API to verify it's working

$projectId = "maharani-sales-hub-11-2025"
$secretId = "dialpad-api-key"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing Dialpad API Directly" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get API key from Secret Manager
Write-Host "Fetching API key from Secret Manager..." -ForegroundColor Yellow
try {
    $apiKey = gcloud secrets versions access latest --secret=$secretId --project=$projectId 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Could not fetch API key" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ API key retrieved" -ForegroundColor Green
} catch {
    Write-Host "❌ Error fetching API key: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Testing Dialpad API endpoints..." -ForegroundColor Yellow
Write-Host ""

$baseUrl = "https://dialpad.com/api/v2"
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

# Test 1: /call endpoint with limit
Write-Host "Test 1: /call endpoint with limit=1000" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/call?limit=1000" -Method Get -Headers $headers -TimeoutSec 60
    Write-Host "  Status: Success" -ForegroundColor Green
    if ($response -is [Array]) {
        Write-Host "  Response type: Array" -ForegroundColor White
        Write-Host "  Number of calls: $($response.Count)" -ForegroundColor $(if ($response.Count -gt 0) { "Green" } else { "Yellow" })
        if ($response.Count -gt 0) {
            Write-Host "  First call ID: $($response[0].id)" -ForegroundColor White
            Write-Host "  First call date_started: $($response[0].date_started)" -ForegroundColor White
        }
    } elseif ($response -is [PSCustomObject]) {
        Write-Host "  Response type: Object" -ForegroundColor White
        Write-Host "  Keys: $($response.PSObject.Properties.Name -join ', ')" -ForegroundColor White
        $items = $response.items
        if ($items) {
            Write-Host "  Items count: $($items.Count)" -ForegroundColor $(if ($items.Count -gt 0) { "Green" } else { "Yellow" })
        }
    }
} catch {
    Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  HTTP Status: $statusCode" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Test 2: /calls endpoint (plural)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/calls?limit=1000" -Method Get -Headers $headers -TimeoutSec 60
    Write-Host "  Status: Success" -ForegroundColor Green
    if ($response -is [Array]) {
        Write-Host "  Response type: Array" -ForegroundColor White
        Write-Host "  Number of calls: $($response.Count)" -ForegroundColor $(if ($response.Count -gt 0) { "Green" } else { "Yellow" })
    } elseif ($response -is [PSCustomObject]) {
        Write-Host "  Response type: Object" -ForegroundColor White
        Write-Host "  Keys: $($response.PSObject.Properties.Name -join ', ')" -ForegroundColor White
    }
} catch {
    Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

