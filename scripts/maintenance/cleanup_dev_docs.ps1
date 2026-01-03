# Cleanup Development/Testing Documentation
# This script removes development, testing, and internal communication docs

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleaning Up Development Documentation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Files to delete (development/testing/internal docs)
$filesToDelete = @(
    # Testing and alternatives
    "TEST_ACCOUNT_SCORING_ALTERNATIVES.md",
    "WEB_APP_TESTING_CHECKLIST.md",
    
    # Internal issue tracking
    "CLOUD_RUN_AUTH_ISSUE.md",
    "DEPLOY_ACCOUNT_SCORING.md",
    
    # Internal communications
    "RESPONSE_TO_ANAND_DEPLOYMENT.md",
    "RESPONSE_TO_ANAND.md",
    "ANAND_SETUP_WEB_APP_SA.md",
    
    # Status reports and tracking
    "SCHEDULER_STATUS_REPORT.md",
    "DIALPAD_FIXES_COMPLETE.md",
    "DIALPAD_SYNC_STATUS.md",
    "DIALPAD_WORKAROUND_IMPLEMENTED.md",
    "MILESTONE_2_3_STATUS.md",
    "FIXES_APPLIED.md",
    "ISSUES_FIXED_SUMMARY.md",
    "SYNC_TEST_RESULTS.md",
    "APPLICATION_RUNNING.md",
    "PROJECT_FINAL_STATUS.md",
    "PROJECT_COMPLETE.md",
    "PRODUCTION_COMPLETE.md",
    "PRODUCTION_READY.md",
    "ISSUES_FIXED.md",
    "REAL_WORLD_SYNC_COMPLETE.md",
    
    # Internal organization
    "DOCUMENTATION_STRUCTURE.md",
    "DOCUMENTATION_INDEX.md",
    "RUN_PROJECT_STEPS.md",
    
    # Proof documents (internal)
    "MILESTONE1_PROOF.md",
    "CLIENT_PROOF_DOCUMENT.md",
    "CLIENT_PROOF_SUMMARY.md",
    
    # Internal setup
    "SALESFORCE_CLIENT_CREDENTIALS_SETUP.md",
    "LOCAL_DEV_SETUP.md"  # Developer-specific, not production
)

$deletedCount = 0
$notFoundCount = 0

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "[DELETED] $file" -ForegroundColor Green
        $deletedCount++
    } else {
        Write-Host "[NOT FOUND] $file" -ForegroundColor Gray
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deleted: $deletedCount files" -ForegroundColor Green
Write-Host "Not found: $notFoundCount files" -ForegroundColor Gray
Write-Host ""
Write-Host "Production documentation has been preserved." -ForegroundColor White

