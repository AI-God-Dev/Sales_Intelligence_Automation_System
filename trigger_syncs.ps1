# Trigger all syncs
$projectId = "maharani-sales-hub-11-2025"
$region = "us-central1"

# Get access token
$token = gcloud auth print-access-token

# Salesforce Sync - Account
Write-Host "Triggering Salesforce Account sync..." -ForegroundColor Yellow
$sfUrl = "https://us-central1-$projectId.cloudfunctions.net/salesforce-sync"
$sfBody = @{object_type="Account";sync_type="full"} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri $sfUrl -Method Post -Headers @{Authorization="Bearer $token";ContentType="application/json"} -Body $sfBody
    Write-Host "✓ Salesforce Account sync triggered: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 5

# Salesforce Sync - Contact
Write-Host "Triggering Salesforce Contact sync..." -ForegroundColor Yellow
$sfBody = @{object_type="Contact";sync_type="full"} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri $sfUrl -Method Post -Headers @{Authorization="Bearer $token";ContentType="application/json"} -Body $sfBody
    Write-Host "✓ Salesforce Contact sync triggered: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 5

# Dialpad Sync
Write-Host "Triggering Dialpad sync..." -ForegroundColor Yellow
$dpUrl = "https://us-central1-$projectId.cloudfunctions.net/dialpad-sync"
$dpBody = @{sync_type="full"} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri $dpUrl -Method Post -Headers @{Authorization="Bearer $token";ContentType="application/json"} -Body $dpBody
    Write-Host "✓ Dialpad sync triggered: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 5

# HubSpot Sync
Write-Host "Triggering HubSpot sync..." -ForegroundColor Yellow
$hsUrl = "https://us-central1-$projectId.cloudfunctions.net/hubspot-sync"
$hsBody = @{} | ConvertTo-Json -Compress
try {
    $response = Invoke-RestMethod -Uri $hsUrl -Method Post -Headers @{Authorization="Bearer $token";ContentType="application/json"} -Body $hsBody
    Write-Host "✓ HubSpot sync triggered: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
}

Write-Host "`nWaiting 30 seconds for syncs to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`nChecking results..." -ForegroundColor Yellow


