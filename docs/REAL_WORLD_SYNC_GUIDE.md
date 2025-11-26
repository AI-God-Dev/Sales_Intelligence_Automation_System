# Real-World Data Sync Guide - Salesforce, Dialpad, HubSpot

## Overview

This guide provides comprehensive instructions for ensuring real-world data synchronization across Salesforce, Dialpad, and HubSpot.

## Quick Start

### Run Complete Validation

```powershell
# Navigate to scripts directory
cd SALES\scripts

# Run comprehensive validation
.\ensure_real_world_sync.ps1
```

### Run Complete Sync Cycle

```powershell
# Run all syncs in proper order
.\run_complete_sync_cycle.ps1
```

### Quick Health Check

```powershell
# Quick validation
.\validate_all_syncs.ps1
```

## Detailed Steps

### 1. Prerequisites Check

Before running syncs, ensure:

- ✅ gcloud CLI authenticated: `gcloud auth login`
- ✅ BigQuery access configured
- ✅ All secrets in Secret Manager:
  - `salesforce-client-id`
  - `salesforce-client-secret`
  - `salesforce-refresh-token` (or username/password)
  - `dialpad-api-key`
  - `hubspot-api-key`

### 2. Salesforce Sync

**Objects Synced:**
- Account
- Contact
- Lead
- Opportunity
- Task
- Event
- EmailMessage (NEW)

**Manual Trigger:**

```powershell
# Single object
$body = @{object_type="Account"; sync_type="incremental"} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "https://us-central1-PROJECT_ID.cloudfunctions.net/salesforce-sync" `
    -Method Post -Headers @{Authorization="Bearer $(gcloud auth print-identity-token)"} `
    -Body $body -ContentType "application/json"

# All objects
.\scripts\run_all_syncs.ps1
```

**Verify:**

```sql
-- Check all Salesforce tables
SELECT 'sf_accounts' as table_name, COUNT(*) as count FROM `PROJECT_ID.sales_intelligence.sf_accounts`
UNION ALL
SELECT 'sf_contacts', COUNT(*) FROM `PROJECT_ID.sales_intelligence.sf_contacts`
UNION ALL
SELECT 'sf_leads', COUNT(*) FROM `PROJECT_ID.sales_intelligence.sf_leads`
UNION ALL
SELECT 'sf_opportunities', COUNT(*) FROM `PROJECT_ID.sales_intelligence.sf_opportunities`
UNION ALL
SELECT 'sf_activities', COUNT(*) FROM `PROJECT_ID.sales_intelligence.sf_activities`
UNION ALL
SELECT 'sf_email_messages', COUNT(*) FROM `PROJECT_ID.sales_intelligence.sf_email_messages`;
```

### 3. Dialpad Sync

**Data Synced:**
- Call logs (all users)
- Call transcripts (when available)
- Phone numbers (normalized)
- Call metadata (duration, direction, sentiment)

**Manual Trigger:**

```powershell
$body = @{sync_type="incremental"} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "https://us-central1-PROJECT_ID.cloudfunctions.net/dialpad-sync" `
    -Method Post -Headers @{Authorization="Bearer $(gcloud auth print-identity-token)"} `
    -Body $body -ContentType "application/json"
```

**Verify:**

```sql
-- Check Dialpad calls
SELECT 
  COUNT(*) as total_calls,
  COUNT(CASE WHEN transcript_text IS NOT NULL THEN 1 END) as calls_with_transcripts,
  COUNT(CASE WHEN matched_contact_id IS NOT NULL THEN 1 END) as matched_calls
FROM `PROJECT_ID.sales_intelligence.dialpad_calls`;

-- Recent calls
SELECT 
  call_id,
  from_number,
  to_number,
  call_time,
  duration_seconds,
  CASE WHEN transcript_text IS NOT NULL THEN 'Yes' ELSE 'No' END as has_transcript
FROM `PROJECT_ID.sales_intelligence.dialpad_calls`
ORDER BY call_time DESC
LIMIT 10;
```

### 4. HubSpot Sync

**Data Synced:**
- Sequence metadata
- Sequence enrollment counts
- Sequence status (active/inactive)

**Manual Trigger:**

```powershell
$body = @{} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "https://us-central1-PROJECT_ID.cloudfunctions.net/hubspot-sync" `
    -Method Post -Headers @{Authorization="Bearer $(gcloud auth print-identity-token)"} `
    -Body $body -ContentType "application/json"
```

**Verify:**

```sql
-- Check HubSpot sequences
SELECT 
  sequence_id,
  sequence_name,
  is_active,
  enrollment_count,
  last_synced
FROM `PROJECT_ID.sales_intelligence.hubspot_sequences`
ORDER BY last_synced DESC;
```

### 5. Entity Resolution

**Matches:**
- Email addresses → Salesforce Contacts
- Phone numbers → Salesforce Contacts
- Calls → Contacts/Accounts

**Manual Trigger:**

```powershell
$body = @{entity_type="all"; batch_size=1000} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "https://us-central1-PROJECT_ID.cloudfunctions.net/entity-resolution" `
    -Method Post -Headers @{Authorization="Bearer $(gcloud auth print-identity-token)"} `
    -Body $body -ContentType "application/json"
```

**Verify:**

```sql
-- Email matches
SELECT 
  COUNT(*) as total_participants,
  COUNT(CASE WHEN sf_contact_id IS NOT NULL THEN 1 END) as matched,
  ROUND(COUNT(CASE WHEN sf_contact_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) as match_rate
FROM `PROJECT_ID.sales_intelligence.gmail_participants`;

-- Phone matches
SELECT 
  COUNT(*) as total_calls,
  COUNT(CASE WHEN matched_contact_id IS NOT NULL THEN 1 END) as matched,
  ROUND(COUNT(CASE WHEN matched_contact_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) as match_rate
FROM `PROJECT_ID.sales_intelligence.dialpad_calls`;
```

## Monitoring

### Check ETL Runs

```sql
-- Recent sync activity
SELECT 
  source_system,
  job_type,
  status,
  rows_processed,
  rows_failed,
  started_at,
  completed_at,
  TIMESTAMP_DIFF(completed_at, started_at, SECOND) as duration_seconds
FROM `PROJECT_ID.sales_intelligence.etl_runs`
ORDER BY started_at DESC
LIMIT 20;
```

### Check Sync Health

```sql
-- Success rate by system
SELECT 
  source_system,
  COUNT(*) as total_runs,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
  ROUND(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate,
  SUM(rows_processed) as total_rows_processed
FROM `PROJECT_ID.sales_intelligence.etl_runs`
WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY source_system
ORDER BY source_system;
```

## Troubleshooting

### Salesforce Sync Issues

**Problem:** Authentication errors
- **Solution:** Check OAuth credentials or username/password in Secret Manager
- **Verify:** `gcloud secrets versions access latest --secret=salesforce-client-id`

**Problem:** Rate limit errors
- **Solution:** Automatic retry with exponential backoff (already implemented)
- **Check:** Review logs for retry attempts

**Problem:** Missing EmailMessage data
- **Solution:** Ensure EmailMessage object is accessible in Salesforce
- **Verify:** Check Salesforce object permissions

### Dialpad Sync Issues

**Problem:** 404 errors for some users
- **Solution:** Normal - users without calls are skipped gracefully
- **Check:** Review logs for skipped users

**Problem:** Missing transcripts
- **Solution:** Transcripts are optional and fetched when available
- **Verify:** Check if Dialpad account has transcript feature enabled

### HubSpot Sync Issues

**Problem:** No sequences found
- **Solution:** Marketing Automation may not be enabled
- **Check:** Verify HubSpot subscription level

**Problem:** API endpoint errors
- **Solution:** Multiple endpoint fallback strategy (already implemented)
- **Verify:** Check logs for which endpoint worked

## Automation

### Cloud Scheduler Setup

Set up scheduled syncs:

```powershell
# Salesforce - Incremental sync every hour
gcloud scheduler jobs create http salesforce-incremental-sync `
    --location=us-central1 `
    --schedule="0 * * * *" `
    --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/salesforce-sync" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{"object_type":"Account","sync_type":"incremental"}' `
    --oidc-service-account-email=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com

# Dialpad - Incremental sync every 2 hours
gcloud scheduler jobs create http dialpad-incremental-sync `
    --location=us-central1 `
    --schedule="0 */2 * * *" `
    --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/dialpad-sync" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{"sync_type":"incremental"}' `
    --oidc-service-account-email=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com

# HubSpot - Full sync daily
gcloud scheduler jobs create http hubspot-daily-sync `
    --location=us-central1 `
    --schedule="0 2 * * *" `
    --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/hubspot-sync" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{}' `
    --oidc-service-account-email=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com

# Entity Resolution - Daily
gcloud scheduler jobs create http entity-resolution-daily `
    --location=us-central1 `
    --schedule="0 3 * * *" `
    --uri="https://us-central1-PROJECT_ID.cloudfunctions.net/entity-resolution" `
    --http-method=POST `
    --headers="Content-Type=application/json" `
    --message-body='{"entity_type":"all","batch_size":1000}' `
    --oidc-service-account-email=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
```

## Best Practices

1. **Run incremental syncs frequently** (hourly for Salesforce, every 2 hours for Dialpad)
2. **Run full syncs weekly** to catch any missed data
3. **Monitor ETL runs** for failures
4. **Check entity resolution match rates** regularly
5. **Review logs** for any recurring errors
6. **Validate data quality** periodically

## Support

For issues or questions:
1. Check Cloud Function logs: `gcloud functions logs read FUNCTION_NAME --gen2 --region=us-central1`
2. Review ETL runs table in BigQuery
3. Check Secret Manager for credential issues
4. Review documentation in `SALES/docs/`

