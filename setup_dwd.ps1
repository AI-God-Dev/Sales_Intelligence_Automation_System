# Domain-Wide Delegation Setup Script
# This script guides you through saving OAuth credentials and provides DWD setup instructions

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Domain-Wide Delegation Setup Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get or Create OAuth Client ID
Write-Host "PART A: Gmail OAuth Client ID" -ForegroundColor Yellow
Write-Host ""

Write-Host "Do you already have a Gmail OAuth Client ID?" -ForegroundColor White
Write-Host "1. Yes, I have it"
Write-Host "2. No, I need to create one"
Write-Host ""

$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "2") {
    Write-Host ""
    Write-Host "Creating OAuth Client ID..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor White
    Write-Host "1. Open: https://console.cloud.google.com/apis/credentials?project=$projectId" -ForegroundColor Cyan
    Write-Host "2. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'" -ForegroundColor Gray
    Write-Host "3. Application type: Web application" -ForegroundColor Gray
    Write-Host "4. Name: 'Sales Intelligence Gmail Access'" -ForegroundColor Gray
    Write-Host "5. Enable 'Domain-wide Delegation' checkbox" -ForegroundColor Gray
    Write-Host "6. Click 'CREATE'" -ForegroundColor Gray
    Write-Host "7. Copy the Client ID and Client Secret (shown only once!)" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter when you have the credentials..."
}

Write-Host ""
Write-Host "Enter your Gmail OAuth Client ID:" -ForegroundColor Yellow
Write-Host "(Format: 123456789-abcdefghijklmnop.apps.googleusercontent.com)" -ForegroundColor Gray
$clientId = Read-Host "Client ID"

if ($clientId -and $clientId -ne "PLACEHOLDER") {
    Write-Host ""
    Write-Host "Saving Client ID to Secret Manager..." -ForegroundColor Yellow
    $clientId | gcloud secrets versions add gmail-oauth-client-id --data-file=- --project=$projectId
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Client ID saved!" -ForegroundColor Green
        
        # Extract numeric part
        $numericId = ($clientId -split '\.')[0]
        Write-Host ""
        Write-Host "Numeric Client ID (for Workspace Admin):" -ForegroundColor Cyan
        Write-Host "  $numericId" -ForegroundColor Yellow
        
        Write-Host ""
        Write-Host "Enter your Gmail OAuth Client Secret:" -ForegroundColor Yellow
        Write-Host "(Format: GOCSPX-...)" -ForegroundColor Gray
        $clientSecret = Read-Host "Client Secret"
        
        if ($clientSecret) {
            Write-Host ""
            Write-Host "Saving Client Secret..." -ForegroundColor Yellow
            $clientSecret | gcloud secrets versions add gmail-oauth-client-secret --data-file=- --project=$projectId
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Client Secret saved!" -ForegroundColor Green
            } else {
                Write-Host "[ERROR] Failed to save Client Secret" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "PART B: Google Workspace Admin Setup" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Now configure Domain-Wide Delegation:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Go to Google Workspace Admin Console:" -ForegroundColor White
        Write-Host "   URL: https://admin.google.com/" -ForegroundColor Cyan
        Write-Host "   Sign in as super admin" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Navigate to:" -ForegroundColor White
        Write-Host "   Security → API Controls → Domain-wide Delegation" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Click 'Add new'" -ForegroundColor White
        Write-Host ""
        Write-Host "4. Enter these details:" -ForegroundColor White
        Write-Host "   Client ID: $numericId" -ForegroundColor Yellow
        Write-Host "   OAuth Scopes (one per line):" -ForegroundColor Gray
        Write-Host "     https://www.googleapis.com/auth/gmail.readonly" -ForegroundColor Cyan
        Write-Host "     https://www.googleapis.com/auth/gmail.modify" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "5. Click 'Authorize'" -ForegroundColor White
        Write-Host ""
        Write-Host "6. Verify it appears in the list" -ForegroundColor White
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Service Account Email:" -ForegroundColor Cyan
        Write-Host "  sales-intel-poc-sa@$projectId.iam.gserviceaccount.com" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Once DWD is configured, you can test gmail-sync!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        
    } else {
        Write-Host "[ERROR] Failed to save Client ID" -ForegroundColor Red
    }
} else {
    Write-Host "[!] Invalid or placeholder Client ID. Please create one first." -ForegroundColor Yellow
}

