# Quick Start Guide - Phase 1 Setup

This guide provides the fastest path to get Phase 1 up and running.

## Prerequisites Check

```powershell
# Check gcloud
gcloud --version

# Check bq
bq --version

# Check authentication
gcloud auth list

# Set project
gcloud config set project maharani-sales-hub-11-2025
```

## Step-by-Step Setup

### 1. Prepare Credentials (Manual - 30 minutes)

**Read `MANUAL_STEPS.md`** and collect all required credentials:
- Gmail OAuth Client ID & Secret
- Salesforce credentials (Client ID, Secret, Username, Password, Security Token)
- Dialpad API Key
- HubSpot Private App Access Token

### 2. Run Automated Setup (Automated - 15-30 minutes)

```powershell
# Run the master setup script
.\setup_complete.ps1
```

This script will:
1. ✅ Enable all required GCP APIs
2. ✅ Create Secret Manager secrets (prompts you to paste credentials)
3. ✅ Create BigQuery dataset and all 13 tables
4. ✅ Create Pub/Sub topic
5. ✅ Deploy all 5 Cloud Functions
6. ✅ Create all 7 Cloud Scheduler jobs
7. ✅ Verify deployment

### 3. Test Ingestion (5 minutes)

```powershell
# Test all ingestion functions
.\scripts\test_ingestion.ps1
```

### 4. Verify Results (2 minutes)

```powershell
# Check logs
.\scripts\check_logs.ps1

# Check BigQuery data
.\scripts\check_bigquery.ps1

# Verify deployment
.\scripts\verify_deployment.ps1
```

## What Gets Created

### BigQuery
- Dataset: `sales_intelligence`
- 13 tables (gmail_messages, sf_accounts, etc.)
- 1 view (v_unmatched_emails)

### Cloud Functions (5)
- `gmail-sync` - Gmail ingestion
- `salesforce-sync` - Salesforce ingestion
- `dialpad-sync` - Dialpad ingestion
- `hubspot-sync` - HubSpot ingestion
- `entity-resolution` - Entity matching

### Cloud Scheduler Jobs (7)
- `gmail-full-sync` - Daily at 2 AM
- `gmail-incremental-sync` - Every hour
- `salesforce-full-sync` - Weekly Sunday 3 AM
- `salesforce-incremental-sync` - Every 6 hours
- `dialpad-sync` - Daily at 1 AM
- `hubspot-sync` - Daily at 4 AM
- `entity-resolution` - Every 4 hours

### Secret Manager (10 secrets)
- All API credentials stored securely

### Pub/Sub
- Topic: `ingestion-errors` (for error notifications)

## Manual Ingestion Triggers

See `docs/INGESTION_TRIGGERS.md` for curl commands to manually trigger ingestion.

## Troubleshooting

### Setup Fails
1. Check `gcloud auth list` - ensure you're authenticated
2. Check project: `gcloud config get-value project`
3. Check APIs: `gcloud services list --enabled`

### Functions Fail to Deploy
1. Check logs: `gcloud functions logs read FUNCTION_NAME --region=us-central1 --gen2`
2. Verify service account exists: `gcloud iam service-accounts describe sales-intel-poc-sa@maharani-sales-hub-11-2025.iam.gserviceaccount.com`

### Ingestion Fails
1. Check Secret Manager: `gcloud secrets list`
2. Verify secrets have values: `gcloud secrets versions access latest --secret=SECRET_NAME`
3. Check Cloud Function logs: `.\scripts\check_logs.ps1`

## Next Steps

After successful setup:
1. Monitor ETL runs: `bq query --use_legacy_sql=false "SELECT * FROM \`maharani-sales-hub-11-2025.sales_intelligence.etl_runs\` ORDER BY started_at DESC LIMIT 10"`
2. Review data quality in BigQuery
3. Check Cloud Scheduler job execution history
4. Proceed to Phase 2 development

## Full Documentation

- **Complete Handoff Guide:** `docs/PHASE1_HANDOFF.md`
- **Manual Steps:** `MANUAL_STEPS.md`
- **Ingestion Triggers:** `docs/INGESTION_TRIGGERS.md`
- **Testing Guide:** `docs/PHASE1_TESTING_GUIDE.md`

