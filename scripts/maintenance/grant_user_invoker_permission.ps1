# Grant Cloud Functions Invoker role to current user for manual testing
# PowerShell version

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "maharani-sales-hub-11-2025" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }

# Get current user email
$USER_EMAIL = gcloud config get-value account 2>$null
if ([string]::IsNullOrEmpty($USER_EMAIL)) {
    Write-Host "Error: No user logged in. Please run: gcloud auth login" -ForegroundColor Red
    exit 1
}

Write-Host "Granting Cloud Functions Invoker role to: $USER_EMAIL" -ForegroundColor Yellow
Write-Host "Project: $PROJECT_ID"
Write-Host ""

# List of functions
$FUNCTIONS = @("gmail-sync", "salesforce-sync", "dialpad-sync", "hubspot-sync", "entity-resolution")

foreach ($FUNCTION_NAME in $FUNCTIONS) {
    Write-Host "Granting permission to invoke: $FUNCTION_NAME..." -ForegroundColor Gray
    
    gcloud functions add-iam-policy-binding $FUNCTION_NAME `
        --region=$REGION `
        --member="user:$USER_EMAIL" `
        --role="roles/cloudfunctions.invoker" `
        --project=$PROJECT_ID 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Successfully granted permission to $FUNCTION_NAME" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to grant permission to $FUNCTION_NAME" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "Done! You can now invoke the functions using your user account." -ForegroundColor Green

