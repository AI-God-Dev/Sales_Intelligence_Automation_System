# Organize Documentation Files into Structured Directory
# Moves all markdown files into organized subdirectories

Write-Host "📁 Organizing documentation files..." -ForegroundColor Green
Write-Host ""

# Create directory structure
$basePath = Split-Path -Parent $PSScriptRoot
$dirs = @(
    "$basePath\docs\phases",
    "$basePath\docs\guides",
    "$basePath\docs\integrations",
    "$basePath\docs\archive",
    "$basePath\docs\fixes"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

$movedCount = 0

# Move phase-specific files
$phaseFiles = @(
    @{File="PHASE1_COMPLETE.md"; Dest="docs\phases\"},
    @{File="PHASE2_AND_3_COMPLETE.md"; Dest="docs\phases\"},
    @{File="PHASE2_AND_3_DEPLOYMENT_GUIDE.md"; Dest="docs\phases\"},
    @{File="PHASE1_CODE_REVIEW_AND_REFINEMENT.md"; Dest="docs\archive\"},
    @{File="PROJECT_COMPLETE_REFINED.md"; Dest="docs\phases\"}
)

Write-Host "Moving phase-specific files..." -ForegroundColor Yellow
foreach ($item in $phaseFiles) {
    $filePath = Join-Path $basePath $item.File
    $destPath = Join-Path $basePath $item.Dest
    if (Test-Path $filePath) {
        Move-Item -Path $filePath -Destination $destPath -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $($item.File) -> $($item.Dest)" -ForegroundColor Gray
        $movedCount++
    }
}

# Move fix/troubleshooting files
$fixFiles = @(
    @{File="DIALPAD_404_FIX.md"; Dest="docs\fixes\"},
    @{File="HUBSPOT_API_KEY_FIX.md"; Dest="docs\fixes\"},
    @{File="HUBSPOT_ENDPOINT_FIX.md"; Dest="docs\fixes\"},
    @{File="HUBSPOT_INGESTION_COMPLETE.md"; Dest="docs\fixes\"},
    @{File="HUBSPOT_INGESTION_FIXED.md"; Dest="docs\fixes\"},
    @{File="CLOUD_FUNCTION_DEPLOYMENT_FIX.md"; Dest="docs\fixes\"}
)

Write-Host "Moving fix documentation..." -ForegroundColor Yellow
foreach ($item in $fixFiles) {
    $filePath = Join-Path $basePath $item.File
    $destPath = Join-Path $basePath $item.Dest
    if (Test-Path $filePath) {
        Move-Item -Path $filePath -Destination $destPath -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $($item.File) -> $($item.Dest)" -ForegroundColor Gray
        $movedCount++
    }
}

# Move guide files
$guideFiles = @(
    @{File="QUICK_START.md"; Dest="docs\guides\"},
    @{File="QUICK_RUN.md"; Dest="docs\guides\"},
    @{File="RUN_PROJECT.md"; Dest="docs\guides\"},
    @{File="QUICK_START_TESTING.md"; Dest="docs\guides\"},
    @{File="QUICK_TEST_GUIDE.md"; Dest="docs\guides\"},
    @{File="COMPLETE_SETUP_GUIDE.md"; Dest="docs\guides\"},
    @{File="create_gmail_oauth_client.md"; Dest="docs\guides\"},
    @{File="MANUAL_STEPS.md"; Dest="docs\guides\"},
    @{File="ACCESS_WEB_APP.md"; Dest="docs\guides\"},
    @{File="WEB_APP_RUNNING.md"; Dest="docs\guides\"}
)

Write-Host "Moving guide files..." -ForegroundColor Yellow
foreach ($item in $guideFiles) {
    $filePath = Join-Path $basePath $item.File
    $destPath = Join-Path $basePath $item.Dest
    if (Test-Path $filePath) {
        Move-Item -Path $filePath -Destination $destPath -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $($item.File) -> $($item.Dest)" -ForegroundColor Gray
        $movedCount++
    }
}

# Move summary/review files to archive
$archiveFiles = @(
    @{File="CODE_REVIEW_AND_FIXES.md"; Dest="docs\archive\"},
    @{File="DEPLOYMENT_REVIEW.md"; Dest="docs\archive\"},
    @{File="PROJECT_REVIEW_SUMMARY.md"; Dest="docs\archive\"},
    @{File="SETUP_COMPLETE_SUMMARY.md"; Dest="docs\archive\"},
    @{File="TESTING_SUMMARY.md"; Dest="docs\archive\"},
    @{File="PRODUCTION_READY_FEATURES.md"; Dest="docs\archive\"},
    @{File="PROJECT_STATUS.md"; Dest="docs\archive\"},
    @{File="INTEGRATION_MODULES_README.md"; Dest="docs\archive\"}
)

Write-Host "Moving archive files..." -ForegroundColor Yellow
foreach ($item in $archiveFiles) {
    $filePath = Join-Path $basePath $item.File
    $destPath = Join-Path $basePath $item.Dest
    if (Test-Path $filePath) {
        Move-Item -Path $filePath -Destination $destPath -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $($item.File) -> $($item.Dest)" -ForegroundColor Gray
        $movedCount++
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ Documentation organization complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "Moved $movedCount files to organized structure" -ForegroundColor Cyan
Write-Host ""
Write-Host "New structure:" -ForegroundColor Yellow
Write-Host "  docs/phases/     - Phase-specific documentation"
Write-Host "  docs/guides/     - Setup and usage guides"
Write-Host "  docs/fixes/      - Fix documentation"
Write-Host "  docs/archive/    - Historical/summary documents"
Write-Host ""

