# Ingestion Trigger Commands

This document provides the exact commands to manually trigger ingestion for each data source.

## Prerequisites

1. Authenticated `gcloud` CLI: `gcloud auth login`
2. Project set: `gcloud config set project maharani-sales-hub-11-2025`
3. All Cloud Functions deployed (see `docs/PHASE1_HANDOFF.md`)

## Getting Access Token

```powershell
$accessToken = gcloud auth print-access-token
$baseUrl = "https://us-central1-maharani-sales-hub-11-2025.cloudfunctions.net"
```

## Gmail Sync

### Full Sync
```powershell
curl -X POST "$baseUrl/gmail-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full"}'
```

### Incremental Sync
```powershell
curl -X POST "$baseUrl/gmail-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"incremental"}'
```

## Salesforce Sync

### Full Sync - All Objects
```powershell
# Account
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full","object_type":"Account"}'

# Contact
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full","object_type":"Contact"}'

# Lead
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full","object_type":"Lead"}'

# Opportunity
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full","object_type":"Opportunity"}'

# Activity
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"full","object_type":"Activity"}'
```

### Incremental Sync
```powershell
curl -X POST "$baseUrl/salesforce-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{"sync_type":"incremental","object_type":"Account"}'
```

## Dialpad Sync

```powershell
curl -X POST "$baseUrl/dialpad-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{}'
```

## HubSpot Sync

```powershell
curl -X POST "$baseUrl/hubspot-sync" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{}'
```

## Entity Resolution

```powershell
curl -X POST "$baseUrl/entity-resolution" `
  -H "Authorization: Bearer $accessToken" `
  -H "Content-Type: application/json" `
  -d '{}'
```

## Automated Testing Script

Use the provided PowerShell script to test all ingestion functions:

```powershell
.\scripts\test_ingestion.ps1
```

## Verification

After triggering ingestion, verify the results:

1. **Check Cloud Function Logs:**
   ```powershell
   .\scripts\check_logs.ps1
   ```

2. **Check BigQuery Data:**
   ```powershell
   .\scripts\check_bigquery.ps1
   ```

3. **Check ETL Run History:**
   ```powershell
   bq query --use_legacy_sql=false --project_id=maharani-sales-hub-11-2025 "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"
   ```

## Expected Response Format

All functions should return a JSON response with:
- `status`: "success", "partial", or "failed"
- `rows_processed`: Number of rows processed
- `errors`: Number of errors (if any)
- Additional fields specific to each function

Example:
```json
{
  "status": "success",
  "rows_processed": 150,
  "errors": 0,
  "mailboxes_synced": 3,
  "messages_synced": 150
}
```

