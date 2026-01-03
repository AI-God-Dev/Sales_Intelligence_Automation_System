# Create EmailMessage table in BigQuery if it doesn't exist
$projectId = "maharani-sales-hub-11-2025"
$dataset = "sales_intelligence"

Write-Host "Creating EmailMessage table in BigQuery..." -ForegroundColor Cyan

$createTableQuery = "CREATE TABLE IF NOT EXISTS ``$projectId.$dataset.sf_email_messages`` (
  email_message_id STRING NOT NULL OPTIONS(description="Salesforce EmailMessage ID (primary key)"),
  from_address STRING OPTIONS(description="Sender email address (normalized)"),
  to_address STRING OPTIONS(description="Recipient email address (normalized)"),
  cc_address STRING OPTIONS(description="CC email addresses (normalized)"),
  bcc_address STRING OPTIONS(description="BCC email addresses (normalized)"),
  subject STRING OPTIONS(description="Email subject"),
  text_body STRING OPTIONS(description="Plain text body"),
  html_body STRING OPTIONS(description="HTML body"),
  message_date TIMESTAMP OPTIONS(description="When email was sent"),
  related_to_id STRING OPTIONS(description="Related Case/Contact/Lead ID"),
  created_date TIMESTAMP OPTIONS(description="When created in Salesforce"),
  last_modified_date TIMESTAMP OPTIONS(description="Last modification"),
  ingested_at TIMESTAMP OPTIONS(description="When loaded into BigQuery")
)
PARTITION BY DATE(message_date)
CLUSTER BY from_address, related_to_id
OPTIONS(description='Salesforce EmailMessage records')"

try {
    bq query --use_legacy_sql=false $createTableQuery
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ EmailMessage table created successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create table" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

