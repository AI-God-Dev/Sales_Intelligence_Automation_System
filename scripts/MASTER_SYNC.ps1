# Master Sync Script - One Script to Rule Them All
# This is the main entry point for all sync operations

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("validate", "sync", "full", "help")]
    [string]$Action = "help"
)

$projectId = "maharani-sales-hub-11-2025"

Write-Host ""
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Real-World Data Sync - Master Script    ║" -ForegroundColor Cyan
Write-Host "║   Salesforce | Dialpad | HubSpot          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    "validate" {
        Write-Host "🔍 Running Validation..." -ForegroundColor Yellow
        Write-Host ""
        & "$PSScriptRoot\validate_all_syncs.ps1"
    }
    
    "sync" {
        Write-Host "🔄 Running Incremental Sync Cycle..." -ForegroundColor Yellow
        Write-Host ""
        & "$PSScriptRoot\run_complete_sync_cycle.ps1"
    }
    
    "full" {
        Write-Host "🚀 Running Full Validation & Sync..." -ForegroundColor Yellow
        Write-Host ""
        & "$PSScriptRoot\ensure_real_world_sync.ps1"
    }
    
    "help" {
        Write-Host "Usage: .\MASTER_SYNC.ps1 [Action]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  validate  - Quick health check (no syncs triggered)" -ForegroundColor White
        Write-Host "  sync      - Run incremental sync cycle" -ForegroundColor White
        Write-Host "  full      - Full validation + sync + verification" -ForegroundColor White
        Write-Host "  help      - Show this help message" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Cyan
        Write-Host "  .\MASTER_SYNC.ps1 validate    # Quick check" -ForegroundColor Gray
        Write-Host "  .\MASTER_SYNC.ps1 sync        # Run syncs" -ForegroundColor Gray
        Write-Host "  .\MASTER_SYNC.ps1 full        # Complete validation" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Quick Start:" -ForegroundColor Cyan
        Write-Host "  1. .\MASTER_SYNC.ps1 validate  # Check current status" -ForegroundColor White
        Write-Host "  2. .\MASTER_SYNC.ps1 sync      # Run syncs" -ForegroundColor White
        Write-Host "  3. .\MASTER_SYNC.ps1 validate  # Verify results" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host ""

