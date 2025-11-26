# Validate All Syncs - Quick Health Check
# Checks if all sync functions are working and have recent data

$projectId = "maharani-sales-hub-11-2025"
$dataset = "sales_intelligence"

Write-Host "🔍 Quick Sync Validation" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check recent ETL runs
$query = @"
SELECT 
  source_system,
  MAX(started_at) as last_run,
  COUNT(*) as total_runs,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
  SUM(rows_processed) as total_rows
FROM \`$projectId.$dataset.etl_runs\`
WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY source_system
ORDER BY source_system
"@

Write-Host "📊 Recent Sync Activity (Last 7 Days):" -ForegroundColor Yellow
Write-Host ""

try {
    $result = bq query --use_legacy_sql=false --format=prettyjson $query 2>&1
    if ($LASTEXITCODE -eq 0) {
        $json = $result | ConvertFrom-Json
        
        if ($json.Count -eq 0) {
            Write-Host "  ⚠️  No recent sync activity found" -ForegroundColor Yellow
        } else {
            foreach ($row in $json) {
                $system = $row.source_system
                $lastRun = $row.last_run
                $successRate = if ($row.total_runs -gt 0) { 
                    [math]::Round(($row.success_count / $row.total_runs) * 100, 1) 
                } else { 0 }
                
                $statusColor = if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 50) { "Yellow" } else { "Red" }
                
                Write-Host "  $system" -ForegroundColor Cyan
                Write-Host "    Last Run: $lastRun" -ForegroundColor White
                Write-Host "    Success Rate: $successRate% ($($row.success_count)/$($row.total_runs))" -ForegroundColor $statusColor
                Write-Host "    Total Rows: $($row.total_rows)" -ForegroundColor White
                Write-Host ""
            }
        }
    } else {
        Write-Host "  ❌ Query failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ Error: $_" -ForegroundColor Red
}

# Check table row counts
Write-Host "📋 Current Data Counts:" -ForegroundColor Yellow
Write-Host ""

$tables = @(
    @{Name="sf_accounts"; Desc="Salesforce Accounts"},
    @{Name="sf_contacts"; Desc="Salesforce Contacts"},
    @{Name="sf_leads"; Desc="Salesforce Leads"},
    @{Name="sf_opportunities"; Desc="Salesforce Opportunities"},
    @{Name="sf_activities"; Desc="Salesforce Activities"},
    @{Name="sf_email_messages"; Desc="Salesforce EmailMessages"},
    @{Name="dialpad_calls"; Desc="Dialpad Calls"},
    @{Name="hubspot_sequences"; Desc="HubSpot Sequences"},
    @{Name="gmail_messages"; Desc="Gmail Messages"}
)

foreach ($table in $tables) {
    $countQuery = "SELECT COUNT(*) as total FROM ``$projectId.$dataset.$($table.Name)``"
    try {
        $countResult = bq query --use_legacy_sql=false --format=prettyjson $countQuery 2>&1
        if ($LASTEXITCODE -eq 0) {
            $countJson = $countResult | ConvertFrom-Json
            $count = $countJson[0].total
            $color = if ($count -gt 0) { "Green" } else { "Yellow" }
            Write-Host "  $($table.Desc): $count" -ForegroundColor $color
        }
    } catch {
        Write-Host "  $($table.Desc): Error" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Validation Complete" -ForegroundColor Green

