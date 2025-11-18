# Store Service Account Key in Secret Manager
# This script helps you download and store the service account private key JSON
# for Domain-Wide Delegation support in Cloud Functions Gen2

$ErrorActionPreference = "Stop"
$projectId = "maharani-sales-hub-11-2025"
$serviceAccountEmail = "sales-intel-poc-sa@$projectId.iam.gserviceaccount.com"
$secretName = "service-account-key-json"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Store Service Account Key in Secret Manager" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service Account: $serviceAccountEmail" -ForegroundColor Yellow
Write-Host "Secret Name: $secretName" -ForegroundColor Yellow
Write-Host "Project: $projectId" -ForegroundColor Yellow
Write-Host ""

# Step 1: Check if secret already exists
Write-Host "Step 1: Checking if secret exists..." -ForegroundColor Yellow
$secretExists = gcloud secrets describe $secretName --project=$projectId 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[!] Secret '$secretName' already exists!" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "Do you want to add a new version? (Y/N)"
    if ($choice -ne "Y" -and $choice -ne "y") {
        Write-Host "Cancelled." -ForegroundColor Red
        exit 0
    }
    $action = "add-version"
} else {
    Write-Host "[OK] Secret doesn't exist, will create new one" -ForegroundColor Green
    $action = "create"
}

Write-Host ""
Write-Host "Step 2: Download Service Account Key" -ForegroundColor Yellow
Write-Host ""
Write-Host "You need to download the service account key JSON:" -ForegroundColor White
Write-Host "1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=$projectId" -ForegroundColor Cyan
Write-Host "2. Click on: $serviceAccountEmail" -ForegroundColor Gray
Write-Host "3. Go to 'KEYS' tab" -ForegroundColor Gray
Write-Host "4. Click 'ADD KEY' → 'Create new key'" -ForegroundColor Gray
Write-Host "5. Select 'JSON' format" -ForegroundColor Gray
Write-Host "6. Click 'CREATE' - key will download automatically" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Important: Save this key file securely!" -ForegroundColor Red
Write-Host "⚠️  The private key cannot be retrieved again!" -ForegroundColor Red
Write-Host ""

$keyPath = Read-Host "Enter the path to the downloaded JSON key file (e.g., C:\Users\Admin\Downloads\maharani-sales-hub-11-2025-xxxxx.json)"

if (-not $keyPath -or -not (Test-Path $keyPath)) {
    Write-Host "[ERROR] File not found: $keyPath" -ForegroundColor Red
    Write-Host "Please provide a valid path to the JSON key file." -ForegroundColor Yellow
    exit 1
}

# Validate it's a JSON file
try {
    $keyContent = Get-Content $keyPath -Raw
    $keyJson = $keyContent | ConvertFrom-Json
    
    # Validate it has required fields
    if (-not $keyJson.project_id -or -not $keyJson.private_key -or -not $keyJson.client_email) {
        Write-Host "[ERROR] Invalid service account key JSON. Missing required fields." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "[OK] Valid service account key JSON found!" -ForegroundColor Green
    Write-Host "Project ID: $($keyJson.project_id)" -ForegroundColor Gray
    Write-Host "Service Account: $($keyJson.client_email)" -ForegroundColor Gray
    
    if ($keyJson.client_email -ne $serviceAccountEmail) {
        Write-Host ""
        Write-Host "[!] Warning: Key email ($($keyJson.client_email)) doesn't match expected ($serviceAccountEmail)" -ForegroundColor Yellow
        $continue = Read-Host "Continue anyway? (Y/N)"
        if ($continue -ne "Y" -and $continue -ne "y") {
            Write-Host "Cancelled." -ForegroundColor Red
            exit 0
        }
    }
    
} catch {
    Write-Host "[ERROR] Failed to parse JSON file: $_" -ForegroundColor Red
    Write-Host "Please ensure the file is a valid JSON service account key." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 3: Storing key in Secret Manager..." -ForegroundColor Yellow

if ($action -eq "create") {
    Write-Host "Creating new secret..." -ForegroundColor Gray
    $keyContent | gcloud secrets create $secretName --data-file=- --project=$projectId --replication-policy="automatic" 2>&1 | Out-Null
} else {
    Write-Host "Adding new version to existing secret..." -ForegroundColor Gray
    $keyContent | gcloud secrets versions add $secretName --data-file=- --project=$projectId 2>&1 | Out-Null
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Service account key stored successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Step 4: Grant service account access to the secret
    Write-Host "Step 4: Granting service account access to secret..." -ForegroundColor Yellow
    gcloud secrets add-iam-policy-binding $secretName `
        --member="serviceAccount:$serviceAccountEmail" `
        --role="roles/secretmanager.secretAccessor" `
        --project=$projectId 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Service account granted access to secret" -ForegroundColor Green
    } else {
        Write-Host "[!] Warning: Could not grant access automatically. You may need to do this manually." -ForegroundColor Yellow
        Write-Host "Run: gcloud secrets add-iam-policy-binding $secretName --member=`"serviceAccount:$serviceAccountEmail`" --role=`"roles/secretmanager.secretAccessor`"" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Service Account Key Stored Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Complete Domain-Wide Delegation setup in Google Workspace Admin" -ForegroundColor White
    Write-Host "2. Redeploy gmail-sync function to use the stored key" -ForegroundColor White
    Write-Host "3. Test gmail-sync function" -ForegroundColor White
    Write-Host ""
    Write-Host "Secret Name: $secretName" -ForegroundColor Gray
    Write-Host "Service Account: $serviceAccountEmail" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⚠️  Security Note:" -ForegroundColor Yellow
    Write-Host "   - The service account key is now stored in Secret Manager" -ForegroundColor White
    Write-Host "   - Delete the downloaded JSON file from your local machine" -ForegroundColor White
    Write-Host "   - Never commit the key file to version control" -ForegroundColor White
    
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to store service account key" -ForegroundColor Red
    Write-Host "Please check the error above and try again." -ForegroundColor Yellow
    exit 1
}

