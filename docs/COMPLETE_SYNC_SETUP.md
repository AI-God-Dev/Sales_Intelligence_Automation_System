# Complete Sync Setup Guide - Get All Real Data Syncing

This guide will help you get all integrations (Gmail, Salesforce, Dialpad, HubSpot) syncing real data to BigQuery.

## Prerequisites

✅ All Cloud Functions deployed  
✅ All secrets configured in Secret Manager  
✅ BigQuery tables created  
✅ Service account has proper permissions  

## Step-by-Step Setup

### Step 1: Verify Environment Variables

```powershell
$env:GCP_PROJECT_ID = "maharani-sales-hub-11-2025"
$env:GCP_REGION = "us-central1"
```

### Step 2: Redeploy All Functions (with latest fixes)

```powershell
# Redeploy all functions to ensure latest code is deployed
gcloud functions deploy gmail-sync --gen2 --region=us-central1
gcloud functions deploy salesforce-sync --gen2 --region=us-central1
gcloud functions deploy dialpad-sync --gen2 --region=us-central1
gcloud functions deploy hubspot-sync --gen2 --region=us-central1
```

### Step 3: Test Each Sync Individually

#### 3.1 Test Gmail Sync

```powershell
gcloud functions call gmail-sync --gen2 --region=us-central1 --data '{}'
```

**Check logs:**
```powershell
gcloud functions logs read gmail-sync --gen2 --region=us-central1 --limit=10
```

**Verify data:**
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\`"
```

#### 3.2 Test Salesforce Sync

**Test each object:**
```powershell
# Accounts
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"object_type":"Account","sync_type":"full"}'

# Contacts
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"object_type":"Contact","sync_type":"full"}'

# Leads
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"object_type":"Lead","sync_type":"full"}'

# Opportunities
gcloud functions call salesforce-sync --gen2 --region=us-central1 --data '{"object_type":"Opportunity","sync_type":"full"}'
```

**Check logs:**
```powershell
gcloud functions logs read salesforce-sync --gen2 --region=us-central1 --limit=20
```

**Verify data:**
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_accounts\`"
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_contacts\`"
```

**If OAuth fails, it will automatically fall back to username/password authentication.**

#### 3.3 Test Dialpad Sync

```powershell
gcloud functions call dialpad-sync --gen2 --region=us-central1 --data '{"sync_type":"full"}'
```

**Check logs:**
```powershell
gcloud functions logs read dialpad-sync --gen2 --region=us-central1 --limit=20
```

**Verify data:**
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`maharani-sales-hub-11-2025.sales_intelligence.dialpad_calls\`"
```

#### 3.4 Test HubSpot Sync

```powershell
gcloud functions call hubspot-sync --gen2 --region=us-central1 --data '{}'
```

**Check logs:**
```powershell
gcloud functions logs read hubspot-sync --gen2 --region=us-central1 --limit=10
```

**Verify data:**
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences\`"
```

### Step 4: Run Complete Test Script

Use the comprehensive test script:

```powershell
.\scripts\test_all_syncs_complete.ps1
```

This script will:
- Redeploy all functions
- Test each sync
- Verify data in BigQuery
- Check ETL runs
- Show error logs

### Step 5: Verify All Data in BigQuery

**Check all table counts:**
```bash
bq query --use_legacy_sql=false "
SELECT 
  'gmail_messages' as table_name, COUNT(*) as row_count 
FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\`
UNION ALL
SELECT 'gmail_participants', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_participants\`
UNION ALL
SELECT 'sf_accounts', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_accounts\`
UNION ALL
SELECT 'sf_contacts', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_contacts\`
UNION ALL
SELECT 'sf_leads', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_leads\`
UNION ALL
SELECT 'sf_opportunities', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_opportunities\`
UNION ALL
SELECT 'dialpad_calls', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.dialpad_calls\`
UNION ALL
SELECT 'hubspot_sequences', COUNT(*) FROM \`maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences\`
"
```

**Check ETL run status:**
```bash
bq query --use_legacy_sql=false "
SELECT 
  source_system, 
  job_type, 
  status, 
  rows_processed, 
  rows_failed,
  started_at
FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\`
ORDER BY started_at DESC
LIMIT 20
"
```

### Step 6: View Sample Data

**Gmail:**
```bash
bq query --use_legacy_sql=false "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.gmail_messages\` LIMIT 5"
```

**Salesforce:**
```bash
bq query --use_legacy_sql=false "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.sf_accounts\` LIMIT 5"
```

**Dialpad:**
```bash
bq query --use_legacy_sql=false "SELECT call_id, direction, from_number, to_number, duration_seconds, call_time FROM \`maharani-sales-hub-11-2025.sales_intelligence.dialpad_calls\` ORDER BY call_time DESC LIMIT 5"
```

**HubSpot:**
```bash
bq query --use_legacy_sql=false "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.hubspot_sequences\` LIMIT 5"
```

## Troubleshooting

### If Gmail sync has 0 rows:
- Check Gmail DWD setup
- Verify service account has domain-wide delegation
- Check OAuth client credentials in Secret Manager

### If Salesforce sync has 0 rows:
- Check logs for authentication errors
- Verify credentials in Secret Manager (username/password or OAuth)
- Ensure Salesforce has data (Accounts, Contacts, etc.)
- Check if using sandbox (set SALESFORCE_DOMAIN=test)

### If Dialpad sync has 0 rows:
- Verify API key has call data permissions
- Check if users have calls in Dialpad
- Review logs for endpoint errors
- Ensure API key is correct in Secret Manager

### If HubSpot sync has 0 rows:
- Check if Marketing Automation is enabled
- Verify API key has sequence access
- Review logs for 404 errors (may be expected if no sequences)

## Next Steps

Once all syncs are working:

1. **Set up Cloud Scheduler** for automated syncing
2. **Run Entity Resolution** to match emails/calls to Salesforce contacts
3. **Set up monitoring** and alerts
4. **Configure incremental syncs** for regular updates

## Quick Reference Commands

```powershell
# Check all data
.\scripts\check_bigquery.ps1

# Check logs
.\scripts\check_logs.ps1

# Test all syncs
.\scripts\test_all_syncs_complete.ps1

# Verify deployment
.\scripts\verify_deployment.ps1
```

