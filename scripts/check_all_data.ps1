# Check all BigQuery table row counts
$projectId = "maharani-sales-hub-11-2025"
$dataset = "sales_intelligence"

Write-Host "Checking BigQuery table row counts..." -ForegroundColor Cyan
Write-Host ""

$tables = @(
    "sf_accounts",
    "sf_contacts",
    "dialpad_calls",
    "hubspot_sequences",
    "gmail_messages"
)

foreach ($table in $tables) {
    Write-Host "Checking $table..." -ForegroundColor Yellow
    $query = "SELECT COUNT(*) as total FROM ``$projectId.$dataset.$table``"
    try {
        $result = bq query --use_legacy_sql=false --format=csv --quiet "$query" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $count = ($result | Select-Object -Skip 1)
            Write-Host "  $table : $count rows" -ForegroundColor Green
        } else {
            Write-Host "  $table : Error querying" -ForegroundColor Red
            Write-Host "  $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "  $table : Error - $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "Done!" -ForegroundColor Cyan


