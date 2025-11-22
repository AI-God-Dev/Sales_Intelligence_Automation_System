# Add HubSpot API Key to Secret Manager
# This script helps you add your HubSpot Private App access token to Secret Manager

param(
    [string]$ProjectId = "maharani-sales-hub-11-2025"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Add HubSpot API Key to Secret Manager" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will add your HubSpot Private App access token to Secret Manager."
Write-Host ""
Write-Host "To get your HubSpot API key:"
Write-Host "1. Log in to HubSpot"
Write-Host "2. Go to Settings → Integrations → Private Apps"
Write-Host "3. Create or open your 'Sales Intelligence System' app"
Write-Host "4. Copy the access token (format: pat-[region]-[random-string])"
Write-Host ""
Write-Host "⚠️  IMPORTANT: The access token is only shown once! Save it immediately!"
Write-Host ""

# Prompt for API key
$apiKey = Read-Host "Enter your HubSpot access token (pat-...)"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "Error: API key cannot be empty" -ForegroundColor Red
    exit 1
}

# Validate format (basic check)
if (-not $apiKey.StartsWith("pat-")) {
    Write-Host "Warning: HubSpot access tokens typically start with 'pat-'. Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Adding API key to Secret Manager..." -ForegroundColor Yellow

# Strip whitespace from API key
$apiKey = $apiKey.Trim()

# Create temporary file with the API key (no newline)
$tempFile = New-TemporaryFile
$apiKey | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline

try {
    # Add secret version
    gcloud secrets versions add hubspot-api-key `
        --data-file=$tempFile `
        --project=$ProjectId
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ HubSpot API key added successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Verify the secret exists:"
        Write-Host "   gcloud secrets describe hubspot-api-key --project=$ProjectId"
        Write-Host ""
        Write-Host "2. Trigger HubSpot ingestion:"
        Write-Host "   .\scripts\test_ingestion.ps1"
        Write-Host "   OR"
        Write-Host "   `$token = gcloud auth print-access-token"
        Write-Host "   `$url = 'https://us-central1-$ProjectId.cloudfunctions.net/hubspot-sync'"
        Write-Host "   Invoke-RestMethod -Uri `$url -Method Post -Headers @{'Authorization'='Bearer ' + `$token; 'Content-Type'='application/json'} -Body '{}'"
        Write-Host ""
    } else {
        Write-Host "Error: Failed to add API key to Secret Manager" -ForegroundColor Red
        exit 1
    }
} finally {
    # Clean up temporary file
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
}


