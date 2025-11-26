# Test Salesforce Sync
$ErrorActionPreference = "Stop"

Write-Host "Testing Salesforce sync..." -ForegroundColor Yellow

$token = gcloud auth print-identity-token
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = '{"object_type":"Account","sync_type":"full"}'

try {
    $response = Invoke-RestMethod -Uri "https://salesforce-sync-z455yfejea-uc.a.run.app" -Method Post -Headers $headers -Body $body -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Salesforce sync SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Status: $($response.status)" -ForegroundColor Gray
    if ($response.rows_synced) {
        Write-Host "Rows synced: $($response.rows_synced)" -ForegroundColor Gray
    }
    if ($response.errors) {
        Write-Host "Errors: $($response.errors)" -ForegroundColor Yellow
    }
    Write-Host ""
    $response | ConvertTo-Json -Depth 3
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Salesforce sync FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

