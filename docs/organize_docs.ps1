# Organize Documentation Files
# This script organizes all markdown files into a structured directory

Write-Host "📁 Organizing documentation files..." -ForegroundColor Green

# Create directory structure
$dirs = @(
    "docs\phases",
    "docs\guides",
    "docs\integrations",
    "docs\archive",
    "docs\fixes"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

# Move phase-specific files
$phaseFiles = @{
    "PHASE1_COMPLETE.md" = "docs\phases\"
    "PHASE2_AND_3_COMPLETE.md" = "docs\phases\"
    "PHASE2_AND_3_DEPLOYMENT_GUIDE.md" = "docs\phases\"
    "PHASE1_CODE_REVIEW_AND_REFINEMENT.md" = "docs\archive\"
}

foreach ($file in $phaseFiles.Keys) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $phaseFiles[$file] -Force
        Write-Host "Moved: $file -> $($phaseFiles[$file])" -ForegroundColor Yellow
    }
}

# Move fix/troubleshooting files
$fixFiles = @{
    "DIALPAD_404_FIX.md" = "docs\fixes\"
    "HUBSPOT_API_KEY_FIX.md" = "docs\fixes\"
    "HUBSPOT_ENDPOINT_FIX.md" = "docs\fixes\"
    "HUBSPOT_INGESTION_COMPLETE.md" = "docs\fixes\"
    "HUBSPOT_INGESTION_FIXED.md" = "docs\fixes\"
    "CLOUD_FUNCTION_DEPLOYMENT_FIX.md" = "docs\fixes\"
}

foreach ($file in $fixFiles.Keys) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $fixFiles[$file] -Force
        Write-Host "Moved: $file -> $($fixFiles[$file])" -ForegroundColor Yellow
    }
}

# Move guide files
$guideFiles = @{
    "QUICK_START.md" = "docs\guides\"
    "QUICK_RUN.md" = "docs\guides\"
    "RUN_PROJECT.md" = "docs\guides\"
    "QUICK_START_TESTING.md" = "docs\guides\"
    "QUICK_TEST_GUIDE.md" = "docs\guides\"
    "COMPLETE_SETUP_GUIDE.md" = "docs\guides\"
    "create_gmail_oauth_client.md" = "docs\guides\"
    "MANUAL_STEPS.md" = "docs\guides\"
}

foreach ($file in $guideFiles.Keys) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $guideFiles[$file] -Force
        Write-Host "Moved: $file -> $($guideFiles[$file])" -ForegroundColor Yellow
    }
}

# Move summary/review files to archive
$archiveFiles = @{
    "CODE_REVIEW_AND_FIXES.md" = "docs\archive\"
    "DEPLOYMENT_REVIEW.md" = "docs\archive\"
    "PROJECT_REVIEW_SUMMARY.md" = "docs\archive\"
    "SETUP_COMPLETE_SUMMARY.md" = "docs\archive\"
    "TESTING_SUMMARY.md" = "docs\archive\"
    "PRODUCTION_READY_FEATURES.md" = "docs\archive\"
    "PROJECT_STATUS.md" = "docs\archive\"
    "INTEGRATION_MODULES_README.md" = "docs\archive\"
}

foreach ($file in $archiveFiles.Keys) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $archiveFiles[$file] -Force
        Write-Host "Moved: $file -> $($archiveFiles[$file])" -ForegroundColor Yellow
    }
}

# Move web app specific files
$webAppFiles = @{
    "ACCESS_WEB_APP.md" = "docs\guides\"
    "WEB_APP_RUNNING.md" = "docs\guides\"
}

foreach ($file in $webAppFiles.Keys) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination $webAppFiles[$file] -Force
        Write-Host "Moved: $file -> $($webAppFiles[$file])" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Documentation organization complete!" -ForegroundColor Green
Write-Host "`nNew structure:" -ForegroundColor Cyan
Write-Host "  docs/phases/     - Phase-specific documentation"
Write-Host "  docs/guides/     - Setup and usage guides"
Write-Host "  docs/fixes/      - Fix documentation"
Write-Host "  docs/archive/    - Historical/summary documents"

